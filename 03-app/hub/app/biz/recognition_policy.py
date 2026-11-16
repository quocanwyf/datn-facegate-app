"""Kiểm lại policy tại điểm commit, tuần tự hóa với PUT settings."""
from sqlalchemy import select
from app.db.models import Company
from app.errors import ApiError
from app.config import get_settings
from app.recog.liveness import POLICY_FIELDS, require_approval


async def lock_recognition_policy(session, company_id, expected):
    # FOR SHARE chặn UPDATE settings đến khi event/profile commit; KEY SHARE không đủ.
    company = await session.scalar(select(Company).where(Company.id == company_id).with_for_update(read=True))
    fields = (*POLICY_FIELDS, 'anti_spoof_enabled', 'liveness_threshold')
    if company is None or any(company.settings.get(key) != expected.get(key) for key in fields):
        raise ApiError(503, 'RECOGNITION_UNAVAILABLE', 'Cấu hình vừa thay đổi; vui lòng quét lại.')
    if company.settings['anti_spoof_enabled']:
        try:
            require_approval(get_settings().hub_data_dir, company.settings['liveness_threshold'], company.settings)
        except (OSError, ValueError, TypeError, KeyError):
            raise ApiError(503, 'RECOGNITION_UNAVAILABLE', 'Phê duyệt chống giả mạo không còn hợp lệ; vui lòng kiểm tra lại.') from None
