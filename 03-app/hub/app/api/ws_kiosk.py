import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.errors import ApiError
from app.recog.worker import Busy

router = APIRouter()


@router.websocket('/api/v1/ws/kiosk')
async def kiosk_socket(socket: WebSocket):
    await socket.accept()
    service = socket.app.state.kiosk_service
    connection_id = uuid4()
    send_lock = asyncio.Lock()
    task, device, header = None, None, None
    last_seq = None

    async def send(message):
        async with send_lock:
            await socket.send_json(message)

    async def revoke():
        await send({'type':'error','code':'DEVICE_REVOKED','message':'Thiết bị đã bị thu hồi.'})
        await socket.close(code=4401)

    async def process(frame_header, data):
        seq = frame_header['seq']
        try:
            response = await service.frame(connection_id, token, frame_header, data)
            if response['type'] != 'enroll_done':
                response['seq'] = seq
            await send(response)
        except Busy:
            await send({'type':'state','seq':seq,'state':'BUSY'})
        except (ApiError, RuntimeError) as error:
            code = getattr(error, 'code', 'OPERATION_INCOMPLETE')
            message = getattr(error, 'message', None) or {
                'MODEL_NOT_VERIFIED':'Máy chủ chưa sẵn sàng.', 'RECOGNITION_UNAVAILABLE':'Máy chủ tạm ngưng nhận dạng.',
                'FRAME_DECODE_FAILED':'Không đọc được khung hình.'}.get(code, 'Chưa hoàn tất thao tác. Vui lòng thử lại.')
            await send({'type':'error','seq':seq,'code':code,'message':message})
            if code in ('TOKEN_INVALID','DEVICE_REVOKED'):
                await socket.close(code=4401)
        except Exception:
            await send({'type':'error','seq':seq,'code':'OPERATION_INCOMPLETE','message':'Chưa hoàn tất thao tác. Vui lòng thử lại.'})

    try:
        try:
            first = await asyncio.wait_for(socket.receive_json(), timeout=5)
        except asyncio.TimeoutError:
            await send({'type':'error','code':'AUTH_TIMEOUT','message':'Hết thời gian xác thực thiết bị.'})
            await socket.close(code=4401)
            return
        if not isinstance(first,dict) or first.get('type') != 'auth' or not isinstance(first.get('device_token'),str):
            raise ApiError(401,'TOKEN_INVALID','Vui lòng xác thực thiết bị.')
        token = first['device_token']
        device = await service.authenticate(token, first.get('app_version'))
        socket.app.state.kiosk_connections.setdefault(device.id,{})[connection_id] = {'send':send,'revoke':revoke,'device':device}
        await send(await service.config(device))
        while True:
            try:
                message = await asyncio.wait_for(socket.receive(), timeout=15)
            except asyncio.TimeoutError:
                await socket.close(code=1001)
                break
            if message['type'] == 'websocket.disconnect':
                break
            await service.authenticate(token)
            if header is not None:
                current, header = header, None
                if message.get('bytes') is None:
                    await send({'type':'error','seq':current['seq'],'code':'BAD_MESSAGE','message':'Cần gửi JPEG ngay sau thông tin khung.'})
                elif current.get('_drop'):
                    continue
                elif task is not None and not task.done():
                    await send({'type':'state','seq':current['seq'],'state':'BUSY'})
                else:
                    # Lấy exception của task trước để không rò lỗi nền.
                    if task:
                        await task
                    task = asyncio.create_task(process(current,message['bytes']))
                continue
            try:
                control = json.loads(message.get('text') or '')
            except (ValueError, TypeError):
                await send({'type':'error','code':'BAD_MESSAGE','message':'Thông điệp không hợp lệ.'})
                continue
            if not isinstance(control,dict):
                await send({'type':'error','code':'BAD_MESSAGE','message':'Thông điệp không hợp lệ.'})
            elif control.get('type') == 'ping':
                await send({'type':'pong'})
            elif control.get('type') == 'frame':
                seq, mode = control.get('seq'), control.get('mode')
                valid = type(seq) is int and mode in ('recognize','enroll')
                if mode == 'enroll':
                    from uuid import UUID
                    try:
                        UUID(control.get('enroll_session_id','')); UUID(control.get('employee_id',''))
                    except (ValueError,TypeError,AttributeError):
                        valid = False
                if not valid:
                    await send({'type':'error','code':'BAD_MESSAGE','message':'Thông tin khung không hợp lệ.', **({'seq':seq} if type(seq) is int else {})})
                    header = {'seq':seq,'_drop':True}  # bỏ binary đi kèm metadata sai
                    continue
                header = control
                if last_seq is not None and seq <= last_seq:
                    header['_drop'] = True
                else:
                    last_seq = seq
            else:
                await send({'type':'error','code':'BAD_MESSAGE','message':'Thông điệp không được hỗ trợ.'})
    except ApiError as error:
        await send({'type':'error','code':error.code,'message':error.message})
        await socket.close(code=4401)
    except (WebSocketDisconnect, RuntimeError):
        pass
    except (ValueError,TypeError,KeyError):
        await send({'type':'error','code':'BAD_MESSAGE','message':'Thông điệp xác thực không hợp lệ.'})
        await socket.close(code=4401)
    finally:
        if task and not task.done():
            task.cancel()
        if task:
            await asyncio.gather(task,return_exceptions=True)
        if device:
            connections = socket.app.state.kiosk_connections.get(device.id,{})
            connections.pop(connection_id,None)
            if not connections:
                socket.app.state.kiosk_connections.pop(device.id,None)
        if service:
            await service.discard(connection_id)
