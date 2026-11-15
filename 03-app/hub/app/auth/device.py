from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from app.auth.dependencies import Database, bearer
from app.auth.security import token_hash, utcnow
from app.db.models import Device
from app.errors import ApiError


async def find_device(session, token):
    device = await session.scalar(select(Device).where(Device.token_hash == token_hash(token)))
    if device is not None and device.status == 'REVOKED':
        raise ApiError(401, 'DEVICE_REVOKED', 'Thiết bị đã bị thu hồi.')
    if device is None or device.status != 'ACTIVE' or device.token_expires_at is None or device.token_expires_at <= utcnow():
        raise ApiError(401, 'TOKEN_INVALID', 'Phiên thiết bị không hợp lệ hoặc đã hết hạn.')
    return device


async def current_device(session: Database, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Device:
    if credentials is None:
        raise ApiError(401, 'TOKEN_INVALID', 'Vui lòng ghép thiết bị.')
    return await find_device(session, credentials.credentials)


CurrentDevice = Annotated[Device, Depends(current_device)]
