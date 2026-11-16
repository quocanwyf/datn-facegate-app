import asyncio
import time
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from app.api.events import event_departments
from app.auth.dependencies import current_user
from app.biz.attendance_views import event_view, handling_view
from app.db.models import Device, Employee, EventHandling, RecognitionEvent
from app.errors import ApiError

router = APIRouter()


async def permitted_event(session, principal, identity):
    event = await session.get(RecognitionEvent, identity)
    if event is None or event.company_id != principal.account.company_id:
        return None
    scopes = event_departments(principal)
    if scopes is not None:
        employee = await session.get(Employee, event.employee_id) if event.employee_id else None
        if employee is None or employee.company_id != principal.account.company_id or employee.department_id not in scopes:
            return None
    return event


@router.websocket('/api/v1/ws/monitor')
async def monitor_socket(socket: WebSocket):
    await socket.accept()
    hub = socket.app.state.monitor
    queue = None
    receive_task = get_task = None
    expires = None
    async def send(value):
        await socket.send_json(jsonable_encoder(value))
    async def identity(token):
        async with hub.factory() as session:
            principal = await current_user(session, HTTPAuthorizationCredentials(scheme='Bearer', credentials=token))
            if not any(role.role in ('OWNER', 'HR', 'SECURITY', 'MANAGER') for role in principal.roles):
                raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền giám sát.')
            return principal
    try:
        try:
            first = await asyncio.wait_for(socket.receive_json(), 5)
        except asyncio.TimeoutError:
            raise ApiError(401, 'AUTH_TIMEOUT', 'Hết thời gian xác thực.') from None
        if not isinstance(first, dict) or first.get('type') != 'auth' or not isinstance(first.get('access_token'), str) or len(first['access_token']) > 8192:
            raise ApiError(401, 'TOKEN_INVALID', 'Cần xác thực ở thông điệp đầu.')
        token = first['access_token']
        await identity(token)  # current_user kiểm chữ ký, loại access, hạn và trạng thái tài khoản.
        expires = float(jwt.decode(token, options={'verify_signature': False})['exp'])  # Chỉ đọc deadline từ token đã xác minh.
        queue = hub.subscribe()
        receive_task = asyncio.create_task(socket.receive())
        last_counters, previous, initial = 0.0, None, True
        while True:
            principal = await identity(token)  # Quyền có thể đổi trong lúc WS còn mở.
            roles = {role.role for role in principal.roles}
            async with hub.factory() as session:
                if initial and roles.intersection({'OWNER', 'HR', 'SECURITY'}):
                    devices = (await session.scalars(select(Device).where(Device.company_id == principal.account.company_id, Device.status == 'ACTIVE'))).all()
                    for device in devices:
                        await send(dict(type='device_status', device_id=str(device.id), gate_id=str(device.gate_id),
                            online=bool(socket.app.state.kiosk_connections.get(device.id)), last_seen_at=device.last_seen_at))
                if roles.intersection({'OWNER', 'HR'}) and time.monotonic() - last_counters >= 2:
                    counters = await hub.counters(session, principal.account.company_id)
                    if counters != previous:
                        await send(dict(type='counters', **counters))
                        previous = counters
                    last_counters = time.monotonic()
            initial = False
            remaining = expires - time.time()
            if remaining <= 0:
                raise ApiError(401, 'TOKEN_EXPIRED', 'Phiên giám sát đã hết hạn.')
            get_task = asyncio.create_task(queue.get())
            done, _ = await asyncio.wait({receive_task, get_task}, timeout=min(2, remaining), return_when=asyncio.FIRST_COMPLETED)
            if receive_task in done:
                packet = receive_task.result()
                if packet.get('type') == 'websocket.disconnect':
                    break
                raise ApiError(400, 'BAD_MESSAGE', 'Kênh giám sát chỉ nhận thông điệp xác thực đầu tiên.')
            if get_task not in done:
                get_task.cancel()
                await asyncio.gather(get_task, return_exceptions=True)
                get_task = None
                continue
            kind, event_id = get_task.result()
            get_task = None
            if kind == 'overflow':
                await socket.close(code=1008)
                break
            principal = await identity(token)
            roles = {role.role for role in principal.roles}
            async with hub.factory() as session:
                if kind == 'device_status':
                    if not roles.intersection({'OWNER', 'HR', 'SECURITY'}):
                        continue
                    device = await session.get(Device, event_id)
                    if device and device.company_id == principal.account.company_id:
                        await send(dict(type=kind, device_id=str(device.id), gate_id=str(device.gate_id),
                            online=bool(socket.app.state.kiosk_connections.get(device.id)), last_seen_at=device.last_seen_at))
                    continue
                event = await permitted_event(session, principal, event_id)
                if event is None:
                    continue
                if kind == 'alert_handled':
                    handling = await session.get(EventHandling, event.id)
                    if handling:
                        await send(dict(type=kind, event_id=str(event.id), handling=await handling_view(session, handling)))
                elif kind == 'event':
                    payload = await event_view(session, event)
                    await send(dict(type='event', **payload))
                    if event.result in ('UNKNOWN', 'SPOOF'):
                        await send(dict(type='alert', **payload))
    except ApiError as error:
        code = 'TOKEN_EXPIRED' if expires is not None and time.time() >= expires else error.code
        await send(dict(type='error', code=code, message=error.message))
        await socket.close(code=4403 if error.status == 403 else 4401)
    except (WebSocketDisconnect, RuntimeError):
        pass
    except (ValueError, TypeError, KeyError):
        await send(dict(type='error', code='TOKEN_INVALID', message='Thông điệp xác thực không hợp lệ.'))
        await socket.close(code=4401)
    finally:
        if queue is not None:
            hub.queues.discard(queue)
        tasks = [task for task in (receive_task, get_task) if task is not None]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
