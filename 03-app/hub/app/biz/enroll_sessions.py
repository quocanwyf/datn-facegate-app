from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from app.auth.security import utcnow
from app.errors import ApiError


@dataclass
class EnrollSession:
    id: UUID
    device_id: UUID
    company_id: UUID
    user_id: UUID
    expires_at: datetime
    consent: dict = field(default_factory=dict)


class EnrollSessions:
    def __init__(self):
        self.sessions = {}

    def create(self, device, user_id):
        self.sessions = {key: value for key, value in self.sessions.items() if value.expires_at > utcnow()}
        session = EnrollSession(uuid4(), device.id, device.company_id, user_id, utcnow() + timedelta(minutes=5))
        self.sessions[session.id] = session
        return session

    def get(self, session_id, device_id):
        session = self.sessions.get(session_id)
        if session is None or session.device_id != device_id or session.expires_at <= utcnow():
            raise ApiError(422, 'SESSION_EXPIRED', 'Phiên đăng ký đã hết hạn. Vui lòng nhập PIN lại.')
        return session
