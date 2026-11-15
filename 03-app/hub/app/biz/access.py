import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from app.biz.files import write_private, delete_private
from app.db.models import Device, Employee, Gate, RecognitionEvent, t_gate_allowed_department
from app.errors import ApiError


async def record_decision(factory, device, payload, inferred):
    decision = inferred['decision']
    relative = None
    try:
        async with factory() as session, session.begin():
            current = await session.get(Device, device.id)
            if current is None or current.status != 'ACTIVE':
                raise ApiError(401, 'DEVICE_REVOKED', 'Thiết bị đã bị thu hồi.')
            gate = await session.get(Gate, device.gate_id)
            employee = await session.get(Employee, decision.employee_id) if decision.employee_id else None
            allowed, reason, event_result = False, None, decision.result
            if employee:
                if employee.status != 'ACTIVE':
                    reason, event_result = 'INACTIVE', 'DENIED_INACTIVE'
                elif employee.attendance_method != 'FACE' or employee.face_consent_at is None:
                    raise ApiError(503, 'RECOGNITION_UNAVAILABLE', 'Dữ liệu khuôn mặt không còn hiệu lực.')
                elif not gate.is_active:
                    reason, event_result = 'RULE', 'DENIED_RULE'
                else:
                    allowed = gate.default_policy == 'ALLOW_ALL_ACTIVE' or await session.scalar(select(t_gate_allowed_department.c.gate_id).where(
                            t_gate_allowed_department.c.gate_id == gate.id, t_gate_allowed_department.c.department_id == employee.department_id)) is not None
                    if not allowed:
                        reason, event_result = 'RULE', 'DENIED_RULE'
            result = {'type':'result','result':'OK' if allowed else 'DENY','door':'OPEN' if allowed else 'DENY',
                      'attendance':{'kind':'NONE'},'message':'Đã nhận diện.' if allowed else 'Không được phép qua cửa.'}
            if employee:
                result['employee'] = {'name':employee.full_name,'code':employee.code}
                if decision.suppressed and allowed:
                    result['result'], result['message'] = 'ALREADY', 'Đã ghi nhận trước đó.'
                    result['attendance']['time'] = datetime.fromtimestamp(decision.recorded_at, timezone.utc).isoformat()
            else:
                reason = decision.result
                result['message'] = 'Không nhận diện được khuôn mặt.' if reason == 'UNKNOWN' else 'Không xác thực được khuôn mặt thật.'
            if reason:
                result['reason'] = reason
            if decision.suppressed:
                return result
            event_id = uuid4()
            if 'crop' in inferred:
                relative = f'snapshots/{event_id}.png'
                await asyncio.to_thread(write_private, relative, inferred['crop'])
            session.add(RecognitionEvent(id=event_id, company_id=device.company_id, gate_id=gate.id, device_id=device.id,
                         occurred_at=inferred['occurred_at'], result=event_result, employee_id=employee.id if employee else None,
                         model_id=inferred['model_id'], top1_score=decision.score, threshold_used=payload['tau'],
                         threshold_level=payload['threshold_level'], p_live_min=decision.p_live_min, n_frames=decision.n_frames,
                         door_action='OPEN' if allowed else 'NONE', snapshot_path=relative))
        return result
    except Exception:
        if relative:
            await asyncio.to_thread(delete_private, [relative])
        raise
