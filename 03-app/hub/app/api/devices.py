from datetime import datetime, timedelta
import json
import secrets
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from app.auth.dependencies import Database, Principal, require_roles
from app.auth.security import token_hash, utcnow
from app.config import get_settings
from app.db.models import Device, Gate
from app.errors import ApiError

router = APIRouter(prefix='/api/v1', tags=['Gates'])
Owner = Annotated[Principal, Depends(require_roles('OWNER'))]


class DeviceCreate(BaseModel):
    gate_id: UUID
    name: str


class DeviceView(BaseModel):
    id: UUID
    gate_id: UUID
    name: str
    status: str
    online: bool
    last_seen_at: datetime | None = None
    app_version: str | None = None


class DevicePairing(BaseModel):
    device: DeviceView
    pairing_code: str
    expires_at: datetime
    qr_payload: str


class PairRequest(BaseModel):
    code: str = Field(pattern=r'^\d{6}$')
    device_info: dict[str, str] | None = None


def device_view(device, app) -> DeviceView:
    return DeviceView(id=device.id, gate_id=device.gate_id, name=device.name, status=device.status,
                      online=device.id in app.state.kiosk_connections, last_seen_at=device.last_seen_at, app_version=device.app_version)


@router.get('/devices', operation_id='getDevices')
async def list_devices(session: Database, owner: Owner, request: Request, gate_id: UUID | None = None) -> list[DeviceView]:
    query = select(Device).where(Device.company_id == owner.account.company_id)
    if gate_id:
        query = query.where(Device.gate_id == gate_id)
    devices = (await session.scalars(query.order_by(Device.created_at))).all()
    return [device_view(device, request.app) for device in devices]


@router.post('/devices', status_code=201, operation_id='postDevices')
async def create_device(body: DeviceCreate, session: Database, owner: Owner, request: Request) -> DevicePairing:
    gate = await session.scalar(select(Gate).where(Gate.id == body.gate_id, Gate.company_id == owner.account.company_id))
    if gate is None:
        raise ApiError(404, 'HTTP_404', 'Không tìm thấy cửa.')
    # DB không có UNIQUE cho pairing_code_hash; tuần tự hóa cấp mã để tránh trùng.
    await session.execute(text('SELECT pg_advisory_xact_lock(69534005)'))
    for _ in range(100):
        code = f'{secrets.randbelow(1000000):06d}'
        digest = token_hash(code)
        if await session.scalar(select(Device.id).where(Device.pairing_code_hash == digest, Device.status == 'PENDING')) is None:
            break
    else:
        raise ApiError(400, 'VALIDATION_ERROR', 'Chưa cấp được mã ghép. Vui lòng thử lại.')
    expires = utcnow() + timedelta(minutes=10)
    device = Device(company_id=owner.account.company_id, gate_id=gate.id, name=body.name,
                    pairing_code_hash=digest, pairing_expires_at=expires)
    session.add(device)
    await session.flush()
    return DevicePairing(device=device_view(device, request.app), pairing_code=code, expires_at=expires,
                         qr_payload=json.dumps({'hub': get_settings().hub_public_url, 'code': code}))


@router.post('/devices/{id}/revoke', operation_id='postDevicesRevoke')
async def revoke_device(id: UUID, session: Database, owner: Owner, request: Request) -> DeviceView:
    device = await session.scalar(select(Device).where(Device.id == id, Device.company_id == owner.account.company_id).with_for_update())
    if device is None:
        raise ApiError(404, 'HTTP_404', 'Không tìm thấy thiết bị.')
    device.status, device.pairing_code_hash = 'REVOKED', None
    await session.commit()
    channels = list(request.app.state.kiosk_connections.pop(device.id,{}).values())
    for channel in channels:
        try:
            await channel['revoke']()
        except (RuntimeError,OSError):
            pass
    return device_view(device, request.app)


@router.post('/kiosk/pair', operation_id='postKioskPair', tags=['Kiosk'])
async def pair_device(body: PairRequest, session: Database, request: Request) -> dict:
    # Dùng peer IP thật; không đọc X-Forwarded-For do client tự gửi trong mô hình LAN.
    ip = request.client.host if request.client else 'unknown'
    limiter = request.app.state.pairing_attempts
    async with limiter.serial(ip):
        return await pair_under_lock(body, session, limiter, ip)


async def pair_under_lock(body, session, limiter, ip):
    limiter.check(ip)
    device = await session.scalar(select(Device).where(Device.pairing_code_hash == token_hash(body.code), Device.status == 'PENDING').with_for_update())
    if device is None:
        limiter.failed(ip)
    if device.pairing_expires_at is None or device.pairing_expires_at <= utcnow():
        raise ApiError(422, 'PAIRING_EXPIRED', 'Mã ghép đã hết hạn. Vui lòng tạo mã mới trên trang quản trị.')
    gate = await session.get(Gate, device.gate_id)
    # Kiểm lại sau await để request đúng mã đang bay không vượt khóa IP vừa có hiệu lực.
    limiter.check(ip)
    token = secrets.token_urlsafe(48)
    device.status, device.token_hash = 'ACTIVE', token_hash(token)
    device.token_expires_at = utcnow() + timedelta(days=30)
    device.last_seen_at = utcnow()
    device.app_version = (body.device_info or {}).get('app_version')
    await session.flush()
    limiter.succeeded(ip)
    return {'device_id': str(device.id), 'device_token': token, 'token_expires_at': device.token_expires_at,
            'gate': {'id': str(gate.id), 'name': gate.name, 'mode': gate.mode}}
