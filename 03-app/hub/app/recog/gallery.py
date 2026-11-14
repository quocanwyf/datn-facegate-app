from threading import RLock
from uuid import UUID
import numpy as np
from sqlalchemy import select
import torch
from app.db.models import Employee, FaceProfile, FaceTemplate


class RecognitionUnavailable(RuntimeError):
    code = 'RECOGNITION_UNAVAILABLE'


class NoGallery(RuntimeError):
    code = 'NO_GALLERY'


def gallery_query(model_id: UUID, company_id: UUID):
    return (select(Employee.id, FaceTemplate.vector).join(FaceProfile, FaceProfile.employee_id == Employee.id)
            .join(FaceTemplate, FaceTemplate.profile_id == FaceProfile.id)
            .where(Employee.company_id == company_id, FaceProfile.company_id == company_id,
                   Employee.status.in_(('ACTIVE', 'SUSPENDED')), Employee.attendance_method == 'FACE',
                   Employee.face_consent_at.is_not(None), FaceProfile.status == 'ACTIVE', FaceTemplate.model_id == model_id)
            .order_by(Employee.id))


class Gallery:
    def __init__(self, device: torch.device):
        self.device = device
        self._lock = RLock()
        self._ids = ()
        self._matrix = None
        self._ready = False

    @property
    def size(self):
        with self._lock:
            return len(self._ids) if self._ready else 0

    @property
    def ready(self):
        with self._lock:
            return self._ready

    def reload(self, load_rows):
        # Thất bại thì ngừng nhận dạng cả với snapshot cũ; không báo thành công sớm.
        with self._lock:
            self._ready = False
            try:
                rows = list(load_rows())
                vectors = np.asarray([row[1] for row in rows], dtype=np.float32).reshape(-1, 512)
                if not np.isfinite(vectors).all() or (len(rows) and not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-3)):
                    raise ValueError('Template không hữu hạn hoặc chưa L2')
                matrix = torch.from_numpy(vectors).to(self.device)
                self._ids, self._matrix = tuple(row[0] for row in rows), matrix
                self._ready = True
            except Exception:
                self._ids, self._matrix = (), None
                raise RecognitionUnavailable('Nạp gallery chưa hoàn tất; tạm ngưng nhận dạng.') from None
        return len(rows)

    def top1(self, embedding: np.ndarray):
        with self._lock:
            if not self._ready:
                raise RecognitionUnavailable('Gallery chưa sẵn sàng.')
            if not self._ids:
                raise NoGallery('Chưa có dữ liệu khuôn mặt.')
            vector = np.asarray(embedding, dtype=np.float32)
            if vector.shape != (512,) or not np.isfinite(vector).all():
                raise ValueError('Embedding phải là vector 512 hữu hạn')
            scores = self._matrix @ torch.from_numpy(np.ascontiguousarray(vector)).to(self.device)
            index = int(torch.argmax(scores).item())
            return self._ids[index], float(scores[index].item())
