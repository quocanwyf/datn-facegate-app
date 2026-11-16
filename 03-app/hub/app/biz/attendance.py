"""Ngày công dẫn xuất theo múi giờ công ty; giờ sửa tay luôn được bảo toàn."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import and_, or_, select
from app.db.models import AttendanceDay, AttendanceRequest, AuditLog, Company, Employee, Gate, Holiday, RecognitionEvent, Shift, ShiftAssignment
from app.auth.security import utcnow


@dataclass(frozen=True)
class DayRules:
    before_h: float
    after_h: float
    checkout_min: float
    forgot_h: float

    @classmethod
    def from_settings(cls, settings):
        return cls(*(settings[key] for key in ('attendance_window_before_h', 'attendance_window_after_h',
                                               'min_checkout_after_checkin_min', 'forgot_out_before_end_h')))


def bounds(shift, work_date, timezone, rules):
    tz = ZoneInfo(timezone)
    start = datetime.combine(work_date, shift.start_time, tz)
    end = datetime.combine(work_date, shift.end_time, tz)
    return start, end, start - timedelta(hours=rules.before_h), end + timedelta(hours=rules.after_h)


def calculate_day(shift, work_date, timezone, rules, now, check_in=None, check_out=None,
                  *, holiday=False, leave=False, finalized=False):
    if now.tzinfo is None or any(value is not None and value.tzinfo is None for value in (check_in, check_out)):
        raise ValueError('Thời điểm phải có múi giờ.')
    if check_out is not None and (check_in is None or check_out < check_in):
        raise ValueError('Giờ ra phải sau giờ vào.')
    result = dict(check_in_at=check_in, check_out_at=check_out, suspect_forgot_out=False,
                  late_min=0, early_min=0, worked_min=0, finalized=finalized)
    if shift is not None:
        start, end, _, close = bounds(shift, work_date, timezone, rules)
        result['finalized'] = finalized or now >= close
        if check_in and check_in > start + timedelta(minutes=shift.grace_in_min):
            result['late_min'] = max(0, int((check_in - start).total_seconds() // 60))
        if check_in and check_out:
            a, b = max(check_in, start), min(check_out, end)
            rest = 0
            if shift.break_start is not None:
                rest_start = datetime.combine(work_date, shift.break_start, ZoneInfo(timezone))
                rest_end = datetime.combine(work_date, shift.break_end, ZoneInfo(timezone))
                rest = max(0, (min(b, rest_end) - max(a, rest_start)).total_seconds())
            result['worked_min'] = max(0, int((max(0, (b-a).total_seconds()) - rest) // 60))
    if holiday:
        status = 'HOLIDAY'
        result['late_min'] = 0
    elif leave:
        status = 'LEAVE'
        result['late_min'] = 0
    elif shift is None:
        status = 'OFF'
    elif not result['finalized']:
        status = 'IN_PROGRESS' if check_in else 'NOT_STARTED' if now < start else 'WAITING_IN'
    elif check_in is None:
        status = 'ABSENT'
    elif check_out is None or check_out < end - timedelta(hours=rules.forgot_h):
        status = 'MISSING_OUT'
        result['suspect_forgot_out'] = check_out is not None
    else:
        early = check_out < end - timedelta(minutes=shift.grace_out_min)
        if early:
            result['early_min'] = max(0, int((end-check_out).total_seconds() // 60))
        late = result['late_min'] > 0 or check_in > start + timedelta(minutes=shift.grace_in_min)
        status = 'LATE_EARLY' if late and early else 'LATE' if late else 'EARLY' if early else 'NORMAL'
    return dict(result, status=status)


async def assigned_shift(session, employee, work_date):
    query = select(ShiftAssignment).where(ShiftAssignment.company_id == employee.company_id,
        ShiftAssignment.weekday == work_date.isoweekday(), ShiftAssignment.effective_from <= work_date,
        or_(ShiftAssignment.effective_to.is_(None), ShiftAssignment.effective_to >= work_date))
    individual = await session.scalar(query.where(ShiftAssignment.employee_id == employee.id))
    assignment = individual or await session.scalar(query.where(ShiftAssignment.department_id == employee.department_id))
    return await session.get(Shift, assignment.shift_id) if assignment else None


async def recompute_day(session, employee_id, work_date, *, now=None, finalize=False):
    # Khóa nhân viên trước cả trường hợp ngày chưa tồn tại: tránh hai event cùng tạo một ngày.
    employee = await session.scalar(select(Employee).where(Employee.id == employee_id).with_for_update(key_share=True))
    if employee is None:
        raise ValueError('Nhân viên không tồn tại.')
    company = await session.get(Company, employee.company_id)
    now = now or utcnow()
    rules = DayRules.from_settings(company.settings)
    shift = await assigned_shift(session, employee, work_date)
    day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee_id,
                                                           AttendanceDay.work_date == work_date).with_for_update())
    if day is None:
        day = AttendanceDay(company_id=employee.company_id, employee_id=employee_id, work_date=work_date,
                            status='OFF', source='AUTO', finalized=False)
        session.add(day)
    holiday = await session.get(Holiday, (employee.company_id, work_date))
    if shift:
        _, _, begin, end = bounds(shift, work_date, company.timezone, rules)
    else:
        begin = datetime.combine(work_date, time.min, ZoneInfo(company.timezone))
        end = begin + timedelta(days=1) - timedelta(microseconds=1)
    # Lệnh nghỉ phép đã được audit là ý định bền vững. Giữ nó cả khi HOLIDAY
    # tạm đứng trước LEAVE trong thứ tự trạng thái, không cần thêm cột vào DB.
    leave = day.status == 'LEAVE' or day.source == 'MANUAL' and day.id is not None and await session.scalar(
        select(AuditLog.id).where(AuditLog.company_id == employee.company_id, AuditLog.entity == 'attendance_day',
            AuditLog.entity_id == str(day.id), AuditLog.action == 'ATTENDANCE_LEAVE').limit(1)) is not None
    if leave:
        calculated = calculate_day(shift, work_date, company.timezone, rules, now, day.check_in_at, day.check_out_at,
            holiday=holiday is not None, leave=True, finalized=day.finalized or finalize)
        day.shift_id = shift.id if shift else None
        for key, value in calculated.items():
            setattr(day, key, value)
        await session.flush()
        return day
    if day.source == 'MANUAL':
        calculated = calculate_day(shift, work_date, company.timezone, rules, now, day.check_in_at, day.check_out_at,
                                   holiday=holiday is not None, finalized=day.finalized or finalize)
    else:
        eligible = or_(and_(RecognitionEvent.result == 'MATCH', Gate.mode == 'ATTENDANCE_ACCESS',
                             RecognitionEvent.door_action == 'OPEN'), RecognitionEvent.result == 'MANUAL_ATTENDANCE')
        events = list((await session.scalars(select(RecognitionEvent).join(Gate, Gate.id == RecognitionEvent.gate_id).where(
            RecognitionEvent.company_id == employee.company_id, RecognitionEvent.employee_id == employee.id,
            RecognitionEvent.occurred_at >= begin, RecognitionEvent.occurred_at <= end, eligible)
            .order_by(RecognitionEvent.occurred_at, RecognitionEvent.id))).all())
        first = events[0] if events else None
        last = next((event for event in reversed(events) if first and
                     event.occurred_at >= first.occurred_at + timedelta(minutes=rules.checkout_min)), None)
        check_in, check_out = first.occurred_at if first else None, last.occurred_at if last else None
        day.check_in_event_id, day.check_out_event_id = first.id if first else None, last.id if last else None
        approved = (await session.scalars(select(AttendanceRequest).where(AttendanceRequest.employee_id == employee.id,
            AttendanceRequest.work_date == work_date, AttendanceRequest.status == 'APPROVED')
            .order_by(AttendanceRequest.reviewed_at, AttendanceRequest.id))).all()
        day.source = 'ADJUSTED' if approved else 'AUTO'
        for request in approved:
            if request.requested_in is not None:
                check_in = request.requested_in
            if request.requested_out is not None:
                check_out = request.requested_out
        calculated = calculate_day(shift, work_date, company.timezone, rules, now, check_in, check_out,
                                   holiday=holiday is not None, finalized=day.finalized or finalize)
    day.shift_id = shift.id if shift else None
    for key, value in calculated.items():
        setattr(day, key, value)
    await session.flush()
    return day


async def finalize_day(session, employee_id, work_date, *, now=None):
    employee = await session.get(Employee, employee_id)
    company = await session.get(Company, employee.company_id)
    shift = await assigned_shift(session, employee, work_date)
    now = now or utcnow()
    if shift is None or now < bounds(shift, work_date, company.timezone, DayRules.from_settings(company.settings))[3]:
        return await recompute_day(session, employee_id, work_date, now=now)
    return await recompute_day(session, employee_id, work_date, now=now, finalize=True)


async def apply_event(session, event, *, now=None):
    if event.employee_id is None:
        return None
    employee = await session.get(Employee, event.employee_id)
    company = await session.get(Company, employee.company_id)
    gate = await session.get(Gate, event.gate_id)
    if event.result != 'MANUAL_ATTENDANCE' and not (event.result == 'MATCH' and gate.mode == 'ATTENDANCE_ACCESS' and event.door_action == 'OPEN'):
        return None
    local_date = event.occurred_at.astimezone(ZoneInfo(company.timezone)).date()
    candidates = []
    for work_date in (local_date - timedelta(days=1), local_date, local_date + timedelta(days=1)):
        shift = await assigned_shift(session, employee, work_date)
        if shift:
            start, _, begin, end = bounds(shift, work_date, company.timezone, DayRules.from_settings(company.settings))
            if begin <= event.occurred_at <= end:
                candidates.append((abs((event.occurred_at-start).total_seconds()), work_date))
    if not candidates:
        return None
    # Một event chỉ gán vào một ngày; tie ưu tiên ngày sớm hơn.
    work_date = min(candidates)[1]
    return await recompute_day(session, employee.id, work_date, now=now)
