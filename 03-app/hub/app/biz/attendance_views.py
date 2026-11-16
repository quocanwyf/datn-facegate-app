from calendar import monthrange
from datetime import date
from sqlalchemy import select
from app.db.models import AttendanceDay, Department, Employee, Gate, Shift, UserAccount, UserRole
from app.errors import ApiError

WORK_STATUSES = {'NORMAL', 'LATE', 'EARLY', 'LATE_EARLY'}


def month_bounds(month):
    try:
        if len(month) != 7:
            raise ValueError()
        begin = date.fromisoformat(month + '-01')
    except ValueError:
        raise ApiError(400, 'VALIDATION_ERROR', 'Tháng phải có dạng YYYY-MM.') from None
    return begin, date(begin.year, begin.month, monthrange(begin.year, begin.month)[1])


def summary(days):
    unique = {(row.employee_id, row.work_date): row for row in days}.values()
    return {'work_days': sum(row.status in WORK_STATUSES for row in unique),
            'late_count': sum(row.late_min > 0 or row.status in ('LATE', 'LATE_EARLY') for row in unique),
            'late_minutes': sum(row.late_min for row in unique),
            'missing_or_absent': sum(row.status in ('MISSING_OUT', 'ABSENT') for row in unique)}


async def brief(session, employee):
    department = await session.get(Department, employee.department_id)
    return dict(id=str(employee.id), code=employee.code, full_name=employee.full_name,
                department_id=str(employee.department_id), department_name=department.name)


def shift_brief(shift):
    return dict(id=str(shift.id), name=shift.name, start_time=shift.start_time.strftime('%H:%M'),
                end_time=shift.end_time.strftime('%H:%M')) if shift else None


async def day_view(session, day):
    return {**{key: getattr(day, key) for key in ('work_date', 'check_in_at', 'check_out_at', 'status',
        'suspect_forgot_out', 'late_min', 'early_min', 'worked_min', 'source', 'finalized', 'edit_reason')},
        'id': str(day.id), 'employee': await brief(session, await session.get(Employee, day.employee_id)),
        'shift': shift_brief(await session.get(Shift, day.shift_id)) if day.shift_id else None}


def required_reviewer(roles, department_id):
    names = {role.role for role in roles}
    if 'OWNER' in names:
        return 'HR'
    if 'HR' in names:
        return 'OWNER'
    if any(role.role == 'MANAGER' and role.scope_department_id == department_id for role in roles):
        return 'HR'
    return 'MANAGER'


def can_review(principal, requester_id, requester_roles, employee):
    if principal.account.id == requester_id or principal.account.company_id != employee.company_id:
        return False
    target = required_reviewer(requester_roles, employee.department_id)
    return any(role.role == target and (target != 'MANAGER' or role.scope_department_id == employee.department_id)
               for role in principal.roles)


async def request_view(session, row, principal):
    employee = await session.get(Employee, row.employee_id)
    roles = (await session.scalars(select(UserRole).where(UserRole.user_id == row.requested_by_user_id))).all()
    day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == row.employee_id,
                                                           AttendanceDay.work_date == row.work_date))
    reviewer = await session.get(UserAccount, row.reviewer_user_id) if row.reviewer_user_id else None
    reviewer_employee = await session.get(Employee, reviewer.employee_id) if reviewer and reviewer.employee_id else None
    return {**{key: getattr(row, key) for key in ('work_date', 'type', 'requested_in', 'requested_out', 'reason',
        'status', 'created_at', 'reviewed_at', 'review_note')}, 'id': str(row.id),
        'employee': await brief(session, employee), 'recorded_in': day.check_in_at if day else None,
        'recorded_out': day.check_out_at if day else None,
        'reviewer_name': reviewer_employee.full_name if reviewer_employee else reviewer.email if reviewer else None,
        'can_review': row.status == 'PENDING' and can_review(principal, row.requested_by_user_id, roles, employee)}


async def event_view(session, row):
    gate = await session.get(Gate, row.gate_id)
    employee = await session.get(Employee, row.employee_id) if row.employee_id else None
    performer = await session.get(UserAccount, row.performed_by_user_id) if row.performed_by_user_id else None
    return {**{key: getattr(row, key) for key in ('occurred_at', 'result', 'top1_score', 'threshold_used',
        'threshold_level', 'p_live_min', 'n_frames', 'door_action', 'reason')}, 'id': str(row.id),
        'device_id': str(row.device_id) if row.device_id else None,
        'gate': {'id': str(gate.id), 'name': gate.name, 'mode': gate.mode},
        'employee': await brief(session, employee) if employee else None,
        'has_snapshot': row.snapshot_path is not None, 'performed_by': performer.email if performer else None}
