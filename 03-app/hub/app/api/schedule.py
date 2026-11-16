from datetime import date, time
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from app.api.contract import body_contract
from app.auth.dependencies import CurrentUser, Database, Principal, department_scope, require_roles
from app.biz.admin import audit, employee_scope, scoped
from app.biz.attendance import recompute_day
from app.db.models import Department, Employee, Holiday, Shift, ShiftAssignment
from app.errors import ApiError

router = APIRouter(prefix='/api/v1', tags=['Schedule'])
Admin = Annotated[Principal, Depends(require_roles('OWNER', 'HR'))]
Reader = Annotated[Principal, Depends(require_roles('OWNER', 'HR', 'MANAGER'))]


def shift_view(shift):
    return {**{key: getattr(shift, key) for key in ('id', 'name', 'grace_in_min', 'grace_out_min')},
            **{key: getattr(shift, key).strftime('%H:%M') if getattr(shift, key) else None
               for key in ('start_time', 'end_time', 'break_start', 'break_end')}}


def shift_values(body):
    try:
        values = {key: body[key] for key in ('name', 'grace_in_min', 'grace_out_min') if key in body}
        values['name'] = values['name'].strip()
        for key in ('start_time', 'end_time', 'break_start', 'break_end'):
            values[key] = time.fromisoformat(body[key]) if body.get(key) else None
        if not values['name'] or values['start_time'] >= values['end_time']:
            raise ValueError()
    except (ValueError, TypeError):
        raise ApiError(422, 'VALIDATION_ERROR', 'Tên hoặc giờ ca không hợp lệ.') from None
    return values


@router.get('/shifts', operation_id='getShifts')
async def shifts(session: Database, principal: Reader):
    rows = (await session.scalars(select(Shift).where(Shift.company_id == principal.account.company_id).order_by(Shift.name))).all()
    return [shift_view(row) for row in rows]


@router.post('/shifts', operation_id='postShifts', status_code=201)
async def create_shift(body: Annotated[dict, Depends(body_contract('ShiftInput'))], session: Database, principal: Admin):
    shift = Shift(company_id=principal.account.company_id, **shift_values(body))
    session.add(shift)
    await session.flush()
    audit(session, principal, 'SHIFT_CREATE', 'shift', shift.id)
    return shift_view(shift)


@router.patch('/shifts/{id}', operation_id='patchShiftsById')
async def update_shift(id: UUID, body: Annotated[dict, Depends(body_contract('ShiftInput'))], session: Database, principal: Admin):
    shift = await scoped(session, Shift, id, principal, True)
    for key, value in shift_values(body).items():
        setattr(shift, key, value)
    await session.flush()
    audit(session, principal, 'SHIFT_UPDATE', 'shift', id)
    return shift_view(shift)


async def assignment_view(session, row):
    shift = await session.get(Shift, row.shift_id)
    return {**{key: getattr(row, key) for key in ('id', 'shift_id', 'employee_id', 'department_id', 'weekday', 'effective_from', 'effective_to')},
            'shift_name': shift.name}


@router.get('/shift-assignments', operation_id='getShiftAssignments')
async def assignments(session: Database, principal: Reader, employee_id: UUID | None = None, department_id: UUID | None = None):
    scopes = department_scope(principal)
    query = select(ShiftAssignment).where(ShiftAssignment.company_id == principal.account.company_id)
    if employee_id:
        employee = await scoped(session, Employee, employee_id, principal)
        employee_scope(principal, employee)
        query = query.where(ShiftAssignment.employee_id == employee_id)
    if department_id:
        await scoped(session, Department, department_id, principal)
        if scopes is not None and department_id not in scopes:
            raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền xem phòng ban này.')
        query = query.where(ShiftAssignment.department_id == department_id)
    if scopes is not None:
        query = query.where((ShiftAssignment.department_id.in_(scopes)) | ShiftAssignment.employee_id.in_(
            select(Employee.id).where(Employee.company_id == principal.account.company_id, Employee.department_id.in_(scopes))))
    return [await assignment_view(session, row) for row in (await session.scalars(query.order_by(ShiftAssignment.weekday, ShiftAssignment.id))).all()]


@router.post('/shift-assignments', operation_id='postShiftAssignments', status_code=201)
async def create_assignment(body: Annotated[dict, Depends(body_contract('ShiftAssignmentInput'))], session: Database, principal: Admin):
    await scoped(session, Shift, UUID(body['shift_id']), principal)
    employee_id, department_id = body.get('employee_id'), body.get('department_id')
    if bool(employee_id) == bool(department_id) or not body['weekdays'] or len(set(body['weekdays'])) != len(body['weekdays']):
        raise ApiError(400, 'VALIDATION_ERROR', 'Chọn đúng một nhân viên/phòng ban và các thứ không trùng.')
    await scoped(session, Employee if employee_id else Department, UUID(employee_id or department_id), principal)
    begin = date.fromisoformat(body['effective_from'])
    end = date.fromisoformat(body['effective_to']) if body.get('effective_to') else None
    if end and end < begin:
        raise ApiError(400, 'VALIDATION_ERROR', 'Ngày kết thúc phải từ ngày bắt đầu trở đi.')
    rows = [ShiftAssignment(company_id=principal.account.company_id, shift_id=UUID(body['shift_id']),
        employee_id=UUID(employee_id) if employee_id else None, department_id=UUID(department_id) if department_id else None,
        weekday=weekday, effective_from=begin, effective_to=end) for weekday in body['weekdays']]
    session.add_all(rows)
    await session.flush()  # PostgreSQL EXCLUDE bảo vệ cả hai request đồng thời.
    for row in rows:
        audit(session, principal, 'ASSIGNMENT_CREATE', 'shift_assignment', row.id)
    return [await assignment_view(session, row) for row in rows]


@router.delete('/shift-assignments/{id}', operation_id='deleteShiftAssignmentsById', status_code=204)
async def delete_assignment(id: UUID, session: Database, principal: Admin):
    row = await scoped(session, ShiftAssignment, id, principal, True)
    await session.delete(row)
    audit(session, principal, 'ASSIGNMENT_DELETE', 'shift_assignment', id)
    return Response(status_code=204)


@router.get('/holidays', operation_id='getHolidays')
async def holidays(session: Database, principal: CurrentUser, year: int):
    if not 1 <= year < 9999:
        raise ApiError(400, 'VALIDATION_ERROR', 'Năm không hợp lệ.')
    rows = (await session.scalars(select(Holiday).where(Holiday.company_id == principal.account.company_id,
        Holiday.date >= date(year, 1, 1), Holiday.date < date(year+1, 1, 1)).order_by(Holiday.date))).all()
    return [{'date': row.date, 'name': row.name} for row in rows]


@router.post('/holidays', operation_id='postHolidays', status_code=201)
async def create_holiday(body: Annotated[dict, Depends(body_contract('Holiday'))], session: Database, principal: Admin):
    if not body['name'].strip():
        raise ApiError(400, 'VALIDATION_ERROR', 'Cần tên ngày lễ.')
    row = Holiday(company_id=principal.account.company_id, date=date.fromisoformat(body['date']), name=body['name'].strip())
    session.add(row)
    await session.flush()
    audit(session, principal, 'HOLIDAY_CREATE', 'holiday', row.date)
    for identity in (await session.scalars(select(Employee.id).where(Employee.company_id == principal.account.company_id, Employee.status == 'ACTIVE'))).all():
        await recompute_day(session, identity, row.date)
    return {'date': row.date, 'name': row.name}


@router.delete('/holidays/{date}', operation_id='deleteHolidaysById', status_code=204)
async def delete_holiday(date: date, session: Database, principal: Admin):
    row = await session.get(Holiday, (principal.account.company_id, date))
    if row is None:
        raise ApiError(404, 'HTTP_404', 'Không tìm thấy ngày lễ.')
    await session.delete(row)
    audit(session, principal, 'HOLIDAY_DELETE', 'holiday', date)
    await session.flush()
    for identity in (await session.scalars(select(Employee.id).where(Employee.company_id == principal.account.company_id, Employee.status == 'ACTIVE'))).all():
        await recompute_day(session, identity, date)
    return Response(status_code=204)
