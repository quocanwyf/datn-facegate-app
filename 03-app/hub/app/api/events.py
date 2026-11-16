from datetime import date, datetime, time, timedelta
from io import StringIO
import csv
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from app.api.attendance import reason
from app.api.contract import body_contract
from app.auth.dependencies import Database, Principal, require_roles
from app.auth.security import utcnow
from app.biz.admin import audit, page_result, scoped
from app.biz.attendance_excel import safe
from app.biz.attendance_views import brief, event_view
from app.biz.files import data_path
from app.db.models import Company, Employee, EventHandling, Gate, RecognitionEvent, UserAccount
from app.errors import ApiError

router = APIRouter(prefix='/api/v1', tags=['Events'])
Reader = Annotated[Principal, Depends(require_roles('OWNER', 'HR', 'SECURITY', 'MANAGER'))]
Operator = Annotated[Principal, Depends(require_roles('OWNER', 'SECURITY'))]
SnapshotReader = Annotated[Principal, Depends(require_roles('OWNER', 'HR', 'SECURITY'))]
EventResult = Literal['MATCH', 'UNKNOWN', 'SPOOF', 'DENIED_RULE', 'DENIED_INACTIVE', 'MANUAL_OPEN', 'MANUAL_ATTENDANCE']


def event_departments(principal):
    if any(role.role in ('OWNER', 'HR', 'SECURITY') for role in principal.roles):
        return None
    return {role.scope_department_id for role in principal.roles if role.role == 'MANAGER'}


async def event_query(session, principal, from_ts=None, to_ts=None, gate_id=None, results=None,
                      employee_id=None, performed_by=None, handled=None):
    query = select(RecognitionEvent).where(RecognitionEvent.company_id == principal.account.company_id)
    scopes = event_departments(principal)
    if scopes is not None:
        query = query.where(RecognitionEvent.employee_id.in_(select(Employee.id).where(
            Employee.company_id == principal.account.company_id, Employee.department_id.in_(scopes))))
    if from_ts is not None and from_ts.tzinfo is None or to_ts is not None and to_ts.tzinfo is None or from_ts and to_ts and to_ts < from_ts:
        raise ApiError(400, 'VALIDATION_ERROR', 'Khoảng thời gian phải hợp lệ và có múi giờ.')
    if from_ts:
        query = query.where(RecognitionEvent.occurred_at >= from_ts)
    if to_ts:
        query = query.where(RecognitionEvent.occurred_at <= to_ts)
    if gate_id:
        await scoped(session, Gate, gate_id, principal)
        query = query.where(RecognitionEvent.gate_id == gate_id)
    if employee_id:
        employee = await scoped(session, Employee, employee_id, principal)
        if scopes is not None and employee.department_id not in scopes:
            raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền xem nhân viên này.')
        query = query.where(RecognitionEvent.employee_id == employee_id)
    if performed_by:
        await scoped(session, UserAccount, performed_by, principal)
        query = query.where(RecognitionEvent.performed_by_user_id == performed_by)
    if results:
        query = query.where(RecognitionEvent.result.in_(results))
    if handled is not None:
        exists = select(EventHandling.event_id).where(EventHandling.event_id == RecognitionEvent.id).exists()
        query = query.where(exists if handled else ~exists)
    return query.order_by(RecognitionEvent.occurred_at.desc(), RecognitionEvent.id.desc())


@router.get('/events', operation_id='getEvents')
async def events(session: Database, principal: Reader, from_ts: datetime | None = None, to_ts: datetime | None = None,
    gate_id: UUID | None = None, result: Annotated[list[EventResult] | None, Query()] = None,
    employee_id: UUID | None = None, performed_by: UUID | None = None, handled: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1, size: Annotated[int, Query(ge=1, le=100)] = 20):
    query = await event_query(session, principal, from_ts, to_ts, gate_id, result, employee_id, performed_by, handled)
    return await page_result(session, query, page, size, event_view)


@router.get('/events/manual-report', operation_id='getEventsManualReport')
async def manual_report(session: Database, principal: SnapshotReader,
                         from_: Annotated[date, Query(alias='from')], to: date):
    if to < from_:
        raise ApiError(400, 'VALIDATION_ERROR', 'Khoảng ngày không hợp lệ.')
    company = await session.get(Company, principal.account.company_id)
    begin = datetime.combine(from_, time.min, ZoneInfo(company.timezone))
    end = datetime.combine(to+timedelta(days=1), time.min, ZoneInfo(company.timezone))
    rows = (await session.execute(select(RecognitionEvent.performed_by_user_id, func.count(),
        func.count(func.distinct(RecognitionEvent.employee_id))).where(RecognitionEvent.company_id == company.id,
        RecognitionEvent.result == 'MANUAL_ATTENDANCE', RecognitionEvent.occurred_at >= begin,
        RecognitionEvent.occurred_at < end).group_by(RecognitionEvent.performed_by_user_id))).all()
    result = []
    for user_id, count, distinct in rows:
        account = await session.get(UserAccount, user_id)
        employee = await session.get(Employee, account.employee_id) if account.employee_id else None
        # Dùng danh tính tài khoản thật nếu người chấm không liên kết nhân viên.
        actor = {**await brief(session, employee), 'id': str(account.id)} if employee else dict(id=str(account.id), code=account.email, full_name=account.email)
        result.append(dict(performed_by=actor, count=count, distinct_employees=distinct))
    return result


@router.get('/events/export', operation_id='getEventsExport')
async def export(session: Database, principal: SnapshotReader, from_ts: datetime | None = None, to_ts: datetime | None = None,
                 gate_id: UUID | None = None, result: Annotated[list[EventResult] | None, Query()] = None):
    query = await event_query(session, principal, from_ts, to_ts, gate_id, result)
    company = await session.get(Company, principal.account.company_id)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Thời gian', 'Cửa', 'Thiết bị', 'Kết quả', 'Mã NV', 'Họ tên', 'Điểm', 'Ngưỡng', 'Mức ngưỡng', 'Số khung', 'Người thực hiện', 'Lý do'])
    for event in (await session.scalars(query)).all():
        row = await event_view(session, event)
        values = [event.occurred_at.astimezone(ZoneInfo(company.timezone)).strftime('%d/%m/%Y %H:%M:%S'), row['gate']['name'],
            row['device_id'], event.result, row['employee']['code'] if row['employee'] else None,
            row['employee']['full_name'] if row['employee'] else None, event.top1_score, event.threshold_used,
            event.threshold_level, event.n_frames, row['performed_by'], event.reason]
        writer.writerow([safe(value) for value in values])
    return Response(output.getvalue().encode('utf-8-sig'), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename="su-kien.csv"'})


@router.get('/events/{id}/snapshot', operation_id='getEventsSnapshot')
async def snapshot(id: UUID, session: Database, principal: SnapshotReader):
    event = await scoped(session, RecognitionEvent, id, principal)
    if event.result not in ('UNKNOWN', 'SPOOF') or not event.snapshot_path:
        raise ApiError(404, 'HTTP_404', 'Không còn ảnh cảnh báo.')
    path = data_path(event.snapshot_path)
    if not path.is_file():
        raise ApiError(404, 'HTTP_404', 'Không còn ảnh cảnh báo.')
    return FileResponse(path, media_type='image/png', headers={'Cache-Control': 'no-store'})


@router.post('/events/{id}/handle', operation_id='postEventsHandle')
async def handle(id: UUID, body: Annotated[dict, Depends(body_contract('EventHandleInput'))],
                 session: Database, principal: Operator, request: Request):
    event = await scoped(session, RecognitionEvent, id, principal, True)
    if event.result not in ('UNKNOWN', 'SPOOF'):
        raise ApiError(422, 'VALIDATION_ERROR', 'Chỉ xử lý cảnh báo người lạ hoặc chống giả mạo.')
    linked = body.get('linked_employee_id')
    if (body['status'] == 'IS_EMPLOYEE') != bool(linked):
        raise ApiError(422, 'VALIDATION_ERROR', 'Chọn nhân viên khi đánh dấu là nhân viên; trạng thái khác không gắn nhân viên.')
    if linked:
        await scoped(session, Employee, UUID(linked), principal)
    row = await session.get(EventHandling, id)
    if row is None:
        row = EventHandling(event_id=id)
        session.add(row)
    row.status, row.linked_employee_id = body['status'], UUID(linked) if linked else None
    row.handled_by_user_id, row.handled_at, row.note = principal.account.id, utcnow(), body.get('note')
    await session.flush()
    audit(session, principal, 'EVENT_HANDLE', 'recognition_event', id)
    result = await event_view(session, event)
    await session.commit()
    request.app.state.monitor.publish('alert_handled', id)
    return result


@router.post('/gates/{id}/manual-open', operation_id='postGatesManualOpen', status_code=201, tags=['Gates'])
async def manual_open(id: UUID, body: Annotated[dict, Depends(body_contract('ManualOpenInput'))],
                       session: Database, principal: Operator, request: Request):
    gate = await scoped(session, Gate, id, principal)
    if not gate.is_active:
        raise ApiError(400, 'VALIDATION_ERROR', 'Cửa đang bị tắt.')
    event = RecognitionEvent(company_id=principal.account.company_id, gate_id=id, occurred_at=utcnow(),
        result='MANUAL_OPEN', door_action='OPEN', performed_by_user_id=principal.account.id, reason=reason(body['reason']))
    session.add(event)
    await session.flush()
    audit(session, principal, 'MANUAL_OPEN', 'recognition_event', event.id)
    result = await event_view(session, event)
    await session.commit()
    request.app.state.monitor.publish('event', event.id)
    return result
