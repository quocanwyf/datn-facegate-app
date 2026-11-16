"""Dữ liệu giờ cố định để kiểm nghiệp vụ; không phải số đo nhận dạng."""
from datetime import date, datetime, time
from types import SimpleNamespace as Row
from zoneinfo import ZoneInfo
import pytest
from app.biz.attendance import DayRules, calculate_day
from app.biz.attendance_views import can_review, required_reviewer, summary

DAY = date(2026, 11, 16)
TZ = 'Asia/Ho_Chi_Minh'
RULES = DayRules(3, 4, 30, 2)
SHIFT = Row(start_time=time(8, 30), end_time=time(17, 30), break_start=time(12), break_end=time(13), grace_in_min=10, grace_out_min=10)


def at(value):
    return datetime.fromisoformat('2026-11-16T' + value).replace(tzinfo=ZoneInfo(TZ)) if value else None


@pytest.mark.parametrize('now,check_in,check_out,status,late,early,worked,suspect', [
    ('08:29:59', None, None, 'NOT_STARTED', 0, 0, 0, False),
    ('08:30', None, None, 'WAITING_IN', 0, 0, 0, False),
    ('21:29:59', None, None, 'WAITING_IN', 0, 0, 0, False),
    ('21:30', None, None, 'ABSENT', 0, 0, 0, False),
    ('17:30', '08:30', '17:30', 'IN_PROGRESS', 0, 0, 480, False),
    ('21:30', '08:40', '17:20', 'NORMAL', 0, 0, 460, False),
    ('21:30', '08:40:01', '17:30', 'LATE', 10, 0, 469, False),
    ('21:30', '08:41', '17:30', 'LATE', 11, 0, 469, False),
    ('21:30', '08:30', '17:19:59', 'EARLY', 0, 10, 469, False),
    ('21:30', '08:41', '17:00', 'LATE_EARLY', 11, 30, 439, False),
    ('21:30', '08:00', '18:00', 'NORMAL', 0, 0, 480, False),
    ('21:30', '08:30', None, 'MISSING_OUT', 0, 0, 0, False),
    ('21:30', '08:30', '12:00', 'MISSING_OUT', 0, 0, 210, True),
    ('21:30', '08:30', '15:29:59', 'MISSING_OUT', 0, 0, 359, True),
    ('21:30', '08:30', '15:30', 'EARLY', 0, 120, 360, False),
    ('21:30', '13:00', '17:30', 'LATE', 270, 0, 270, False),
    ('21:30', '12:30', '17:30', 'LATE', 240, 0, 270, False),
    ('21:30', '08:30', '12:30', 'MISSING_OUT', 0, 0, 210, True),
])
def test_status_grace_rounding_and_break_overlap(now, check_in, check_out, status, late, early, worked, suspect):
    result = calculate_day(SHIFT, DAY, TZ, RULES, at(now), at(check_in), at(check_out))
    assert (result['status'], result['late_min'], result['early_min'], result['worked_min'], result['suspect_forgot_out']) == (status, late, early, worked, suspect)


@pytest.mark.parametrize('shift,holiday,leave,status', [(SHIFT, True, True, 'HOLIDAY'), (None, False, True, 'LEAVE'), (None, False, False, 'OFF'), (None, True, False, 'HOLIDAY')])
def test_priority(shift, holiday, leave, status):
    assert calculate_day(shift, DAY, TZ, RULES, at('22:00'), holiday=holiday, leave=leave)['status'] == status


def test_finalized_never_reverts_and_timezone_required():
    assert calculate_day(SHIFT, DAY, TZ, RULES, at('09:00'), finalized=True)['status'] == 'ABSENT'
    with pytest.raises(ValueError):
        calculate_day(SHIFT, DAY, TZ, RULES, datetime(2026, 11, 16))


@pytest.mark.parametrize('roles,expected', [
    ([('OWNER', None), ('HR', None)], 'HR'), ([('HR', None), ('MANAGER', 'own')], 'OWNER'),
    ([('MANAGER', 'own')], 'HR'), ([('MANAGER', 'other')], 'MANAGER'), ([('EMPLOYEE', None)], 'MANAGER')])
def test_review_escalation_multiple_roles(roles, expected):
    grants = [Row(role=role, scope_department_id=scope) for role, scope in roles]
    assert required_reviewer(grants, 'own') == expected
    employee = Row(company_id='company', department_id='own')
    self_principal = Row(account=Row(id='sender', company_id='company'), roles=[Row(role=expected, scope_department_id='own')])
    assert not can_review(self_principal, 'sender', grants, employee)
    other = Row(account=Row(id='other', company_id='company'), roles=[])
    assert not can_review(other, 'sender', grants, employee)  # Không có người duyệt vẫn chờ.
    other.roles = [Row(role=expected, scope_department_id='own')]
    assert can_review(other, 'sender', grants, employee)


def test_unique_workday_summary():
    row = Row(employee_id='person', work_date=DAY, status='LATE', late_min=11)
    assert summary([row, row]) == dict(work_days=1, late_count=1, late_minutes=11, missing_or_absent=0)


def test_zero_grace_compares_seconds_before_flooring_minutes():
    shift = Row(**{**vars(SHIFT), 'grace_in_min': 0})
    result = calculate_day(shift, DAY, TZ, RULES, at('22:00'), at('08:30:01'), at('17:30'))
    assert result['status'] == 'LATE' and result['late_min'] == 0
    assert summary([Row(employee_id='person', work_date=DAY, **result)])['late_count'] == 1
    assert calculate_day(shift, DAY, TZ, RULES, at('22:00'), at('08:30:01'), at('17:30'), holiday=True)['late_min'] == 0
