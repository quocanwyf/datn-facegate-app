"""Pipeline T05: toàn bộ mô hình, OpenCV và tensor chỉ chạy trong worker."""
from datetime import datetime, timezone
from threading import Event
import sys
import numpy as np
from sqlalchemy import create_engine, select,update
import torch
from app.config import get_settings
from app.db.models import Company, RecognitionModel
from app.recog.decision import Cooldowns, DeviceSession, Observation, Params
from app.recog.detector import Detector
from app.recog.embedder import Embedder
from app.recog.gallery import Gallery, RecognitionUnavailable, gallery_query
from app.recog.model_loader import load_verified
from app.recog.worker import InferenceWorker
from app.recog.mutations import MutationBarrier


class FrameError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class RecognitionRuntime:
    def __init__(self):
        self.model_verified = False
        self.error_code = 'MODEL_NOT_VERIFIED'
        self.gallery = None
        self.mutations=MutationBarrier()
        self.paused = self.mutations.paused
        self.sessions, self.samples = {}, {}
        self.cooldowns = Cooldowns()
        self.engine = None
        self.worker = InferenceWorker(initializer=self.initialize)

    def initialize(self):
        settings = get_settings()
        self.engine = create_engine(settings.database_url.get_secret_value().replace('postgresql+asyncpg:', 'postgresql+psycopg:'), hide_parameters=True, pool_pre_ping=True)
        try:
            with self.engine.connect() as connection:
                self.model = dict(connection.execute(select(RecognitionModel.__table__).where(RecognitionModel.is_active)).mappings().one())
                self.company_id = connection.scalar(select(Company.id))
                initial_settings = connection.scalar(select(Company.settings).where(Company.id == self.company_id))
            device = settings.infer_device
            if device == 'auto':
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.device = torch.device(device)
            backbone, self.meta, self.verify_report = load_verified(self.model, self.device)
            self.model_verified = True
            import cv2
            runtime_info={'python':sys.version.split()[0],'torch':str(torch.__version__),'opencv':cv2.__version__,
                          'numpy':np.__version__,'device':str(self.device),'cuda':torch.version.cuda,'amp':self.meta['amp'],
                          'verified_at':datetime.now(timezone.utc).isoformat()}
            with self.engine.begin() as connection:
                connection.execute(update(RecognitionModel).where(RecognitionModel.id==self.model['id']).values(runtime=runtime_info))
            self.model['runtime']=runtime_info
            self.embedder = Embedder(backbone, self.device)
            self.detector = Detector(initial_settings['min_face_px'], initial_settings['max_abs_yaw_ratio'])
            self.gallery = Gallery(self.device)
            self.reload(None)
        except Exception as error:
            self.error_code = 'MODEL_NOT_VERIFIED' if not self.model_verified else 'RECOGNITION_UNAVAILABLE'
            # Chỉ log mã/lớp lỗi, không đưa đường dẫn/bí mật hay dữ liệu mặt ra WS.
            print(f'Recognition startup degraded: {self.error_code} ({type(error).__name__})', flush=True)
        return {'frame': self.frame, 'reload': self.reload, 'discard': self.discard,
                'discard_employee':self.discard_employee, 'rollback_decision':self.rollback_decision}

    def rollback_decision(self, payload):
        decision = payload['decision']
        if decision.suppressed:
            return
        registry = self.cooldowns.employees if decision.result == 'MATCH' else self.cooldowns.alerts
        key = (payload['gate_id'],decision.employee_id) if decision.result == 'MATCH' else payload['gate_id']
        if registry.get(key) == payload['occurred_at'].timestamp():
            registry.pop(key, None)

    @property
    def ready(self):
        return self.model_verified and self.gallery is not None and self.gallery.ready and not self.paused.is_set()

    def reload(self, payload):
        if not self.model_verified or self.gallery is None:
            raise FrameError('MODEL_NOT_VERIFIED', 'Máy chủ chưa sẵn sàng.')
        def rows():
            with self.engine.connect() as connection:
                return connection.execute(gallery_query(self.model['id'], self.company_id)).all()
        try:
            generation=self.mutations.snapshot()
            count = self.gallery.reload(rows)
            self.sessions.clear()
            completed=(payload or {}).get('complete',{})
            self.mutations.finish_reload(generation,completed)
            return count
        except Exception:
            self.paused.set()
            raise RecognitionUnavailable('Máy chủ tạm ngưng nhận dạng.') from None

    def discard(self, connection_id):
        self.sessions.pop(connection_id, None)
        for key in list(self.samples):
            if key[0] == connection_id:
                del self.samples[key]

    def discard_employee(self, employee_id):
        for key in list(self.samples):
            if key[2] == employee_id:
                del self.samples[key]

    def frame(self, payload):
        import cv2
        if not self.model_verified:
            raise FrameError('MODEL_NOT_VERIFIED', 'Máy chủ chưa sẵn sàng.')
        settings = payload['settings']
        if settings['anti_spoof_enabled']:
            raise FrameError('RECOGNITION_UNAVAILABLE', 'Chống giả mạo chưa được hiệu chỉnh tại T13.')
        recognize = payload['mode'] == 'recognize'
        if recognize and not self.ready:
            raise FrameError('RECOGNITION_UNAVAILABLE', 'Máy chủ tạm ngưng nhận dạng.')
        if recognize and self.gallery.size == 0:
            return {'type': 'state', 'state': 'NO_GALLERY'}
        try:
            image = cv2.imdecode(np.frombuffer(payload['jpeg'], dtype=np.uint8), cv2.IMREAD_COLOR) if payload['jpeg'].startswith(b'\xff\xd8') else None
        except cv2.error:
            image = None
        if image is None:
            raise FrameError('FRAME_DECODE_FAILED', 'Không đọc được khung hình.')
        if max(image.shape[:2]) > settings['frame_long_side']:
            raise FrameError('BAD_MESSAGE', 'Khung hình vượt kích thước cấu hình.')
        self.detector.min_face_px = settings['min_face_px']
        self.detector.max_abs_yaw_ratio = settings['max_abs_yaw_ratio']
        faces = self.detector.detector.detect(image)
        observation = self.detector.observe(image, faces)
        now = datetime.now(timezone.utc).timestamp()
        if not recognize:
            return self.enroll(payload, image, faces, observation)
        params = Params.from_settings(settings, payload['tau'])
        key = payload['connection_id']
        session = self.sessions.get(key)
        if session is None or session.params != params:
            session = self.sessions[key] = DeviceSession(params, payload['gate_id'], self.cooldowns)
        if not observation.valid:
            session.consume(Observation(False, now))
            return {'type': 'state', 'state': {'NO_FACE':'NO_FACE', 'FACE_TOO_SMALL':'TOO_FAR', 'BAD_POSE':'LOOK_STRAIGHT'}[observation.reason]}
        embedding = self.embedder.embed(image, observation.landmarks)
        identity, score = self.gallery.top1(embedding)
        decision = session.consume(Observation(True, now, observation.bbox, identity, score))
        if not self.ready:
            if decision:
                self.rollback_decision({'decision':decision,'gate_id':payload['gate_id'],
                                        'occurred_at':datetime.fromtimestamp(now,timezone.utc)})
            raise FrameError('RECOGNITION_UNAVAILABLE', 'Máy chủ tạm ngưng nhận dạng.')
        if decision is None:
            return {'type':'state', 'state':'CHECKING', 'bbox':list(observation.bbox), 'frames_in_window':len(session.window)}
        output = {'decision':decision, 'model_id':self.model['id'], 'occurred_at':datetime.fromtimestamp(now, timezone.utc)}
        if decision.result in ('UNKNOWN', 'SPOOF') and not decision.suppressed:
            x,y,w,h = observation.bbox
            crop = image[max(0,int(y)):min(image.shape[0],int(y+h)), max(0,int(x)):min(image.shape[1],int(x+w))]
            ok, encoded = cv2.imencode('.png', crop)
            if not ok:
                self.rollback_decision(dict(output, gate_id=payload['gate_id']))
                raise FrameError('OPERATION_INCOMPLETE', 'Chưa lưu được ảnh cảnh báo.')
            output['crop'] = encoded.tobytes()
        return output

    def enroll(self, payload, image, faces, observation):
        import cv2
        key = (payload['connection_id'], payload['enroll_session_id'], payload['employee_id'])
        samples = self.samples.setdefault(key, [])
        reason = ('MULTI_FACE' if len(faces) > 1 else {'NO_FACE':'NO_FACE','FACE_TOO_SMALL':'TOO_SMALL','BAD_POSE':'POSE'}.get(observation.reason))
        if reason:
            return {'type':'enroll_progress','accepted':len(samples),'total':5,'reason':reason}
        embedding = self.embedder.embed(image, observation.landmarks)
        maximum = get_settings().enroll_max_cos_similarity
        if any(float(embedding @ sample['vector']) > maximum for sample in samples):
            return {'type':'enroll_progress','accepted':len(samples),'total':5,'reason':'TOO_SIMILAR'}
        from fr.align.template import norm_crop
        aligned, _ = norm_crop(image, observation.landmarks)
        ok, png = cv2.imencode('.png', aligned)
        if not ok:
            raise FrameError('OPERATION_INCOMPLETE', 'Chưa lưu được mẫu đăng ký.')
        samples.append({'png':png.tobytes(),'vector':embedding,'det_score':observation.det_score,'yaw_ratio':observation.yaw_ratio,'p_live':None})
        if len(samples) < 5:
            return {'type':'enroll_progress','accepted':len(samples),'total':5}
        self.samples.pop(key)
        template = np.mean([sample['vector'] for sample in samples], axis=0)
        norm = np.linalg.norm(template)
        if not np.isfinite(norm) or norm == 0:
            raise FrameError('OPERATION_INCOMPLETE', 'Template đăng ký không hợp lệ.')
        template = template / norm
        duplicate_id, duplicate_score = None, None
        if self.gallery is None or not self.gallery.ready:
            raise FrameError('RECOGNITION_UNAVAILABLE', 'Chưa kiểm tra được trùng khuôn mặt.')
        # Loại chính nhân viên đang đăng ký lại khỏi phép kiểm trùng.
        with self.engine.connect() as connection:
            rows = connection.execute(gallery_query(self.model['id'], self.company_id)).all()
        candidates = [(identity,float(np.asarray(vector,dtype=np.float32) @ template)) for identity,vector in rows if identity != payload['employee_id']]
        if candidates:
            identity, score = max(candidates, key=lambda item:item[1])
            if score >= payload['strict_threshold']:
                duplicate_id, duplicate_score = identity, score
        return {'samples':samples,'template':template,'model_id':self.model['id'],
                'duplicate_id':duplicate_id,'duplicate_score':duplicate_score}

    def close(self):
        self.worker.close()
        self.samples.clear()
        if self.engine:
            self.engine.dispose()
