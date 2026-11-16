from datetime import date, datetime, time, timedelta
from functools import partial
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from app.api.contract import body_contract
from app.api.faces import own_employee as self_employee
from app.auth.dependencies import Database, Principal, department_scope, require_roles
from app.auth.security import utcnow
from app.biz.admin import audit, employee_scope, page_result, scoped
from app.biz.attendance import apply_event, assigned_shift, recompute_day
from app.biz.attendance_views import brief, can_review, day_view, event_view, month_bounds, request_view, shift_brief, summary
from app.db.models import AttendanceDay, AttendanceRequest, Company, Employee, Gate, Holiday, RecognitionEvent, UserRole
from app.errors import ApiError

router = APIRouter(prefix='/api/v1', tags=['Attendance'])
Admin = Annotated[Principal, Depends(require_roles('OWNER', 'HR'))]
Reader = Annotated[Principal, Depends(require_roles('OWNER', 'HR', 'MANAGER'))]
Operator = Annotated[Principal, Depends(require_roles('OWNER', 'HR', 'SECURITY'))]
SelfUser = Annotated[Principal, Depends(require_roles('EMPLOYEE'))]
RequestStatus = Literal['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED']
AttendanceStatus = Literal['HOLIDAY', 'LEAVE', 'OFF', 'NOT_STARTED', 'WAITING_IN', 'IN_PROGRESS', 'ABSENT', 'MISSING_OUT', 'NORMAL', 'LATE', 'EARLY', 'LATE_EARLY']


def reason(value):
    if not value or not value.strip():
        raise ApiError(400, 'VALIDATION_ERROR', 'Vui lòng nhập lý do.')
    return value.strip()


def timestamp(value):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError()
        return result
    except ValueError:
        raise ApiError(422, 'VALIDATION_ERROR', 'Giờ phải có múi giờ hợp lệ.') from None


async def scoped_employees(session, principal, department_id=None, employee_id=None):
    query = select(Employee).where(Employee.company_id == principal.account.company_id)
    scopes = department_scope(principal)
    if scopes is not None:
        if department_id is not None and department_id not in scopes:
            raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền xem phòng ban này.')
        query = query.where(Employee.department_id.in_(scopes))
    if employee_id:
        employee = await scoped(session, Employee, employee_id, principal)
        employee_scope(principal, employee)
        query = query.where(Employee.id == employee_id)
    if department_id:
        query = query.where(Employee.department_id == department_id)
    return query


@router.get('/attendance/days', operation_id='getAttendanceDays')
async def days(session: Database, principal: Reader, from_: Annotated[date, Query(alias='from')], to: date,
               department_id: UUID | None = None, employee_id: UUID | None = None, status: AttendanceStatus | None = None,
               page: Annotated[int, Query(ge=1)] = 1, size: Annotated[int, Query(ge=1, le=100)] = 20):
    if to < from_:
        raise ApiError(400, 'VALIDATION_ERROR', 'Khoảng ngày không hợp lệ.')
    employees = await scoped_employees(session, principal, department_id, employee_id)
    query = select(AttendanceDay).where(AttendanceDay.company_id == principal.account.company_id,
        AttendanceDay.employee_id.in_(employees.with_only_columns(Employee.id)),
        AttendanceDay.work_date >= from_, AttendanceDay.work_date <= to)
    if status:
        query = query.where(AttendanceDay.status == status)
    return await page_result(session, query.order_by(AttendanceDay.work_date.desc(), AttendanceDay.employee_id), page, size, day_view)


@router.patch('/attendance/days/{id}', operation_id='patchAttendanceDaysById')
async def edit_day(id: UUID, body: Annotated[dict, Depends(body_contract('AttendanceDayEdit'))], session: Database, principal: Admin):
    initial = await scoped(session, AttendanceDay, id, principal)
    if initial.employee_id == principal.account.employee_id:
        raise ApiError(403, 'SELF_EDIT_FORBIDDEN', 'Không được sửa ngày công của chính mình.')
    note = reason(body['reason'])
    await scoped(session, Employee, initial.employee_id, principal, True)
    day = await scoped(session, AttendanceDay, id, principal, True)
    for key in ('check_in_at', 'check_out_at'):
        if key in body:
            setattr(day, key, timestamp(body[key]))
    if day.check_out_at is not None and (day.check_in_at is None or day.check_out_at < day.check_in_at):
        raise ApiError(422, 'VALIDATION_ERROR', 'Giờ ra phải sau giờ vào.')
    day.source, day.edited_by_user_id, day.edit_reason = 'MANUAL', principal.account.id, note
    day = await recompute_day(session, day.employee_id, day.work_date)
    audit(session, principal, 'ATTENDANCE_EDIT', 'attendance_day', day.id)
    return await day_view(session, day)


@router.post('/attendance/leave', operation_id='postAttendanceLeave')
async def leave(body: Annotated[dict, Depends(body_contract('LeaveInput'))], session: Database, principal: Admin):
    employee = await scoped(session, Employee, UUID(body['employee_id']), principal, True)
    note = reason(body['reason'])
    if not body['dates']:
        raise ApiError(400, 'VALIDATION_ERROR', 'Cần chọn ngày nghỉ.')
    result = []
    for work_date in sorted({date.fromisoformat(value) for value in body['dates']}):
        day = await recompute_day(session, employee.id, work_date)
        holiday = await session.get(Holiday, (employee.company_id, work_date))
        day.status, day.source, day.edit_reason, day.edited_by_user_id = 'HOLIDAY' if holiday else 'LEAVE', 'MANUAL', note, principal.account.id
        day.suspect_forgot_out = False
        await session.flush()
        audit(session, principal, 'ATTENDANCE_LEAVE', 'attendance_day', day.id)
        result.append(await day_view(session, day))
    return result


@router.post('/attendance/manual', operation_id='postAttendanceManual', status_code=201)
async def manual(body: Annotated[dict, Depends(body_contract('ManualAttendanceInput'))], session: Database, principal: Operator):
    employee = await scoped(session, Employee, UUID(body['employee_id']), principal, True)
    gate = await scoped(session, Gate, UUID(body['gate_id']), principal)
    if employee.id == principal.account.employee_id:
        raise ApiError(403, 'SELF_MANUAL_FORBIDDEN', 'Không được chấm công hộ chính mình.')
    if employee.attendance_method != 'MANUAL' or employee.status != 'ACTIVE' or not gate.is_active or gate.mode != 'ATTENDANCE_ACCESS':
        raise ApiError(422, 'VALIDATION_ERROR', 'Nhân viên hoặc cửa không cho phép chấm công hộ.')
    event = RecognitionEvent(company_id=employee.company_id, gate_id=gate.id, employee_id=employee.id,
        result='MANUAL_ATTENDANCE', door_action='NONE', occurred_at=utcnow(),
        performed_by_user_id=principal.account.id, reason=reason(body['reason']))
    session.add(event)
    await session.flush()
    await apply_event(session, event)
    audit(session, principal, 'ATTENDANCE_MANUAL', 'recognition_event', event.id)
    return await event_view(session, event)


@router.get('/attendance/requests', operation_id='getAttendanceRequests')
async def requests(session: Database, principal: Reader, status: RequestStatus | None = None,
                   scope: Literal['all', 'team'] = 'all', page: Annotated[int, Query(ge=1)] = 1,
                   size: Annotated[int, Query(ge=1, le=100)] = 20):
    employees = await scoped_employees(session, principal)
    query = select(AttendanceRequest).where(AttendanceRequest.company_id == principal.account.company_id,
        AttendanceRequest.employee_id.in_(employees.with_only_columns(Employee.id)))
    if scope == 'team':
        team = {role.scope_department_id for role in principal.roles if role.role == 'MANAGER'}
        query = query.where(AttendanceRequest.employee_id.in_(select(Employee.id).where(Employee.department_id.in_(team))))
    if status:
        query = query.where(AttendanceRequest.status == status)
    return await page_result(session, query.order_by(AttendanceRequest.created_at.desc(), AttendanceRequest.id), page, size,
                             partial(request_view, principal=principal))


async def review(id, body, session, principal, approved):
    row = await scoped(session, AttendanceRequest, id, principal, True)
    if row.requested_by_user_id == principal.account.id:
        raise ApiError(403, 'SELF_REVIEW_FORBIDDEN', 'Không được tự duyệt giải trình.')
    employee = await scoped(session, Employee, row.employee_id, principal)
    grants = (await session.scalars(select(UserRole).where(UserRole.user_id == row.requested_by_user_id))).all()
    if not can_review(principal, row.requested_by_user_id, grants, employee):
        raise ApiError(403, 'FORBIDDEN', 'Giải trình cần người duyệt đúng cấp theo vai trò người gửi.')
    if row.status != 'PENDING':
        raise ApiError(422, 'NOT_PENDING', 'Giải trình đã được xử lý.')
    note = body.get('note')
    if not approved:
        note = reason(note)
    row.status = 'APPROVED' if approved else 'REJECTED'
    row.reviewer_user_id, row.reviewed_at, row.review_note = principal.account.id, utcnow(), note
    await session.flush()
    if approved:
        try:
            await recompute_day(session, row.employee_id, row.work_date)
        except ValueError:
            raise ApiError(422, 'VALIDATION_ERROR', 'Giờ đề nghị không tạo được cặp giờ vào/ra hợp lệ.') from None
    audit(session, principal, 'REQUEST_APPROVE' if approved else 'REQUEST_REJECT', 'attendance_request', row.id)
    return await request_view(session, row, principal)


@router.post('/attendance/requests/{id}/approve', operation_id='postAttendanceRequestsApprove')
async def approve(id: UUID, body: Annotated[dict, Depends(body_contract('ReviewInput'))], session: Database, principal: Reader):
    return await review(id, body, session, principal, True)


@router.post('/attendance/requests/{id}/reject', operation_id='postAttendanceRequestsReject')
async def reject(id: UUID, body: Annotated[dict, Depends(body_contract('ReviewInput'))], session: Database, principal: Reader):
    return await review(id, body, session, principal, False)


@router.get('/me/requests', operation_id='getMeRequests', tags=['Me'])
async def my_requests(session: Database, principal: SelfUser, status: RequestStatus | None = None,
                      page: Annotated[int, Query(ge=1)] = 1, size: Annotated[int, Query(ge=1, le=100)] = 20):
    employee = await self_employee(session, principal)
    query = select(AttendanceRequest).where(AttendanceRequest.employee_id == employee.id,
                                           AttendanceRequest.requested_by_user_id == principal.account.id)
    if status:
        query = query.where(AttendanceRequest.status == status)
    return await page_result(session, query.order_by(AttendanceRequest.created_at.desc(), AttendanceRequest.id), page, size,
                             partial(request_view, principal=principal))


@router.post('/me/requests', operation_id='postMeRequests', status_code=201, tags=['Me'])
async def create_request(body: Annotated[dict, Depends(body_contract('AttendanceRequestCreate'))], session: Database, principal: SelfUser):
    employee = await self_employee(session, principal, True)
    check_in, check_out = timestamp(body.get('requested_in')), timestamp(body.get('requested_out'))
    if (body['type'] == 'FORGOT_IN' and not check_in or body['type'] == 'FORGOT_OUT' and not check_out
            or check_in and check_out and check_out <= check_in):
        raise ApiError(422, 'VALIDATION_ERROR', 'Cần giờ đề nghị hợp lệ cho loại giải trình.')
    work_date = date.fromisoformat(body['work_date'])
    pending = await session.scalar(select(AttendanceRequest.id).where(AttendanceRequest.employee_id == employee.id,
        AttendanceRequest.work_date == work_date, AttendanceRequest.status == 'PENDING'))
    if pending:
        raise ApiError(409, 'REQUEST_PENDING_EXISTS', 'Ngày này đã có giải trình chờ duyệt.')
    row = AttendanceRequest(company_id=employee.company_id, employee_id=employee.id,
        requested_by_user_id=principal.account.id, work_date=work_date, type=body['type'], reason=reason(body['reason']),
        requested_in=check_in, requested_out=check_out)
    session.add(row)
    await session.flush()
    audit(session, principal, 'REQUEST_CREATE', 'attendance_request', row.id)
    return await request_view(session, row, principal)


@router.post('/me/requests/{id}/cancel', operation_id='postMeRequestsCancel', tags=['Me'])
async def cancel_request(id: UUID, session: Database, principal: SelfUser):
    employee = await self_employee(session, principal)
    row = await scoped(session, AttendanceRequest, id, principal, True)
    if row.employee_id != employee.id or row.requested_by_user_id != principal.account.id:
        raise ApiError(403, 'FORBIDDEN', 'Không được hủy giải trình của người khác.')
    if row.status != 'PENDING':
        raise ApiError(422, 'NOT_PENDING', 'Chỉ được hủy giải trình đang chờ duyệt.')
    row.status = 'CANCELLED'
    audit(session, principal, 'REQUEST_CANCEL', 'attendance_request', row.id)
    await session.flush()
    return await request_view(session, row, principal)


async def date_events(session, employee, work_date, timezone):
    begin = datetime.combine(work_date, time.min, ZoneInfo(timezone))
    return (await session.scalars(select(RecognitionEvent).where(RecognitionEvent.employee_id == employee.id,
        RecognitionEvent.company_id == employee.company_id, RecognitionEvent.occurred_at >= begin,
        RecognitionEvent.occurred_at < begin+timedelta(days=1)).order_by(RecognitionEvent.occurred_at))).all()


@router.get('/me/today', operation_id='getMeToday', tags=['Me'])
async def today(session: Database, principal: SelfUser):
    employee = await self_employee(session, principal)
    company = await session.get(Company, employee.company_id)
    work_date = utcnow().astimezone(ZoneInfo(company.timezone)).date()
    shift = await assigned_shift(session, employee, work_date)
    holiday = await session.get(Holiday, (employee.company_id, work_date))
    day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id, AttendanceDay.work_date == work_date))
    passes = []
    for event in await date_events(session, employee, work_date, company.timezone):
        gate = await session.get(Gate, event.gate_id)
        passes.append(dict(occurred_at=event.occurred_at, gate_name=gate.name, gate_mode=gate.mode, result=event.result))
    return dict(date=work_date, shift=shift_brief(shift), holiday=holiday.name if holiday else None,
                attendance_method=employee.attendance_method, day=await day_view(session, day) if day else None, passes=passes)


@router.get('/me/attendance', operation_id='getMeAttendance', tags=['Me'])
async def my_month(session: Database, principal: SelfUser, month: str):
    employee = await self_employee(session, principal)
    begin, end = month_bounds(month)
    rows = (await session.scalars(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id,
        AttendanceDay.work_date >= begin, AttendanceDay.work_date <= end).order_by(AttendanceDay.work_date))).all()
    return dict(month=month, days=[await day_view(session, row) for row in rows], summary=summary(rows))


@router.get('/me/days/{date}', operation_id='getMeDaysById', tags=['Me'])
async def my_day(date: date, session: Database, principal: SelfUser):
    employee = await self_employee(session, principal)
    company = await session.get(Company, employee.company_id)
    day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id, AttendanceDay.work_date == date))
    request = await session.scalar(select(AttendanceRequest).where(AttendanceRequest.employee_id == employee.id,
        AttendanceRequest.work_date == date).order_by(AttendanceRequest.created_at.desc()).limit(1))
    return dict(day=await day_view(session, day) if day else None,
        events=[await event_view(session, event) for event in await date_events(session, employee, date, company.timezone)],
        request=await request_view(session, request, principal) if request else None)


@router.get('/attendance/export', operation_id='getAttendanceExport')
async def export(session: Database, principal: Reader, month: str, department_id: UUID | None = None):
    from app.biz.attendance_excel import export_month
    employees = (await session.scalars((await scoped_employees(session, principal, department_id)).order_by(Employee.code))).all()
    content = await export_month(session, employees, month)
    return Response(content, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': f'attachment; filename="bang-cong-{month}.xlsx"'})
