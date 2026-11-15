import asyncio
from collections import defaultdict
from sqlalchemy import select
from app.auth.device import find_device
from app.auth.security import utcnow
from app.biz.access import record_decision
from app.biz.enrollment import persist_enrollment
from app.db.models import Company, Employee, Gate, ThresholdProfile
from app.db.session import Session
from app.errors import ApiError
from app.recog.runtime import FrameError


class KioskService:
    def __init__(self, app, runtime, factory=Session):
        self.app, self.runtime, self.factory = app, runtime, factory
        self.gate_locks = defaultdict(asyncio.Lock)

    async def authenticate(self, token, version=None):
        async with self.factory() as session, session.begin():
            device = await find_device(session, token)
            device.last_seen_at = utcnow()
            if version is not None:
                device.app_version = version
            return device

    async def config(self, device):
        async with self.factory() as session:
            gate = await session.get(Gate, device.gate_id)
            settings = (await session.get(Company, device.company_id)).settings
            return {'type':'config','gate':{'id':str(gate.id),'name':gate.name,'mode':gate.mode},
                    **{key:settings[key] for key in ('research_banner','max_fps','frame_long_side','jpeg_quality','result_display_sec')},
                    'server_time':utcnow().isoformat()}

    async def frame(self, connection_id, token, header, jpeg):
        device = await self.authenticate(token)
        async with self.gate_locks[device.gate_id]:
            async with self.factory() as session:
                company, gate = await session.get(Company, device.company_id), await session.get(Gate, device.gate_id)
                if not self.runtime.model_verified:
                    raise FrameError('MODEL_NOT_VERIFIED', 'Máy chủ chưa sẵn sàng.')
                model_id = self.runtime.model['id']
                threshold = await session.scalar(select(ThresholdProfile.cos_threshold).where(ThresholdProfile.model_id == model_id,
                                                       ThresholdProfile.level == gate.threshold_level)) if gate.threshold_level != 'CUSTOM' else gate.custom_threshold
                strict = await session.scalar(select(ThresholdProfile.cos_threshold).where(ThresholdProfile.model_id == model_id, ThresholdProfile.level == 'STRICT_TEST'))
                if threshold is None or strict is None:
                    raise FrameError('RECOGNITION_UNAVAILABLE', 'Thiếu cấu hình ngưỡng của cửa.')
                payload = {'connection_id':connection_id,'gate_id':gate.id,'settings':company.settings,'mode':header['mode'],
                           'jpeg':jpeg,'tau':float(threshold),'threshold_level':gate.threshold_level,'strict_threshold':float(strict)}
                enrollment = None
                if header['mode'] == 'enroll':
                    from uuid import UUID
                    from app.api.kiosk import enroller
                    enrollment = self.app.state.enroll_sessions.get(UUID(header['enroll_session_id']), device.id)
                    if await enroller(session, enrollment.user_id, device.company_id) is None:
                        raise ApiError(422, 'SESSION_EXPIRED', 'Người đăng ký không còn quyền.')
                    employee_id = UUID(header['employee_id'])
                    employee = await session.get(Employee, employee_id)
                    if (employee is None or employee.company_id != device.company_id or employee.status != 'ACTIVE'
                            or employee.face_consent_at != enrollment.consent.get(employee_id) or employee.face_consent_at is None):
                        raise ApiError(422, 'SESSION_EXPIRED', 'Cần đồng ý trước khi đăng ký khuôn mặt.')
                    payload.update(enroll_session_id=enrollment.id, employee_id=employee_id)
            inferred = await asyncio.wrap_future(self.runtime.worker.submit('frame', payload, device_id=device.id))
            if 'samples' in inferred:
                # Không gửi ảnh/vector nội bộ ra WS, chỉ gửi kết quả sau DB + file hoàn tất.
                return await persist_enrollment(self.factory, device, enrollment, payload['employee_id'], inferred)
            if 'decision' in inferred:
                try:
                    return await record_decision(self.factory, device, payload, inferred)
                except BaseException:
                    await asyncio.wrap_future(self.runtime.worker.submit('rollback_decision',dict(inferred,gate_id=device.gate_id)))
                    raise
            return inferred

    async def discard(self, connection_id):
        await asyncio.wrap_future(self.runtime.worker.submit('discard', connection_id))

    async def reload(self,completed=None):
        count = await asyncio.wrap_future(self.runtime.worker.submit('reload', {'complete':completed or {}}))
        if not self.runtime.ready:
            raise FrameError('RECOGNITION_UNAVAILABLE','Một thao tác cập nhật dữ liệu khuôn mặt chưa hoàn tất.')
        for connections in list(self.app.state.kiosk_connections.values()):
            for channel in list(connections.values()):
                try:
                    await channel['send'](await self.config(channel['device']))
                except (RuntimeError,OSError):
                    pass
        return count
