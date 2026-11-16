"""PostgreSQL thật; giờ/event/ngày công dưới đây chỉ là fixture và rollback."""
from datetime import date, datetime, time, timedelta
from io import BytesIO
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo
from openpyxl import load_workbook
import pytest
from sqlalchemy import delete, select
from app.biz.attendance import apply_event, assigned_shift, finalize_day, recompute_day
from app.biz.attendance_excel import DETAIL_COLUMNS, TOTAL_COLUMNS, export_month
from app.biz.access import record_decision
from app.auth.security import utcnow
from app.recog.decision import Decision
from app.db.models import AttendanceDay, AttendanceRequest, Device, Employee, Gate, Holiday, RecognitionEvent, RecognitionModel, Shift, ShiftAssignment, UserAccount, UserRole
from test_admin_api import auth
from test_auth import runtime, validate

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB kiểm thử riêng')]
DAY = date(2026, 11, 16)
TZ = ZoneInfo('Asia/Ho_Chi_Minh')


def at(value):
    return datetime.fromisoformat('2026-11-16T' + value).replace(tzinfo=TZ)


async def setup(session):
    employee = await session.scalar(select(Employee).where(Employee.code == 'NV006'))
    owner = await session.scalar(select(UserAccount).where(UserAccount.email == 'nv001@demo.local'))
    gate = await session.scalar(select(Gate).where(Gate.company_id == employee.company_id, Gate.mode == 'ATTENDANCE_ACCESS'))
    await session.execute(delete(ShiftAssignment).where(ShiftAssignment.employee_id == employee.id))
    shift = Shift(company_id=employee.company_id, name='Ca kiểm thử T09', start_time=time(8, 30), end_time=time(17, 30),
                  break_start=time(12), break_end=time(13), grace_in_min=10, grace_out_min=10)
    session.add(shift)
    await session.flush()
    session.add(ShiftAssignment(company_id=employee.company_id, employee_id=employee.id, shift_id=shift.id,
                                weekday=1, effective_from=DAY))
    await session.flush()
    return employee, owner, gate, shift


async def add_event(session, employee, owner, gate, value):
    event = RecognitionEvent(company_id=employee.company_id, employee_id=employee.id, gate_id=gate.id,
        occurred_at=at(value), result='MANUAL_ATTENDANCE', door_action='NONE', performed_by_user_id=owner.id, reason='Fixture T09 rollback')
    session.add(event)
    await session.flush()
    return event


async def test_recompute_idempotent_late_event_and_window(runtime):
    _, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, shift = await setup(session)
        assert (await assigned_shift(session, employee, DAY)).id == shift.id
        await add_event(session, employee, owner, gate, '05:29:59')  # Trước cửa sổ 3h.
        first = await add_event(session, employee, owner, gate, '08:41')
        await add_event(session, employee, owner, gate, '09:00')  # Chưa đủ 30 phút.
        day = await finalize_day(session, employee.id, DAY, now=at('21:30'))
        assert day.status == 'MISSING_OUT' and day.check_in_event_id == first.id and day.check_out_at is None
        last = await add_event(session, employee, owner, gate, '17:30')
        await apply_event(session, last, now=at('22:00'))
        day = await recompute_day(session, employee.id, DAY, now=at('22:00'))
        before = (day.id, day.updated_at, day.status, day.check_in_at, day.check_out_at, day.late_min, day.worked_min, day.finalized)
        assert day.status == 'LATE' and day.late_min == 11 and day.finalized and day.check_out_event_id == last.id
        day = await recompute_day(session, employee.id, DAY, now=at('22:00'))
        assert before == (day.id, day.updated_at, day.status, day.check_in_at, day.check_out_at, day.late_min, day.worked_min, day.finalized)
        outside = await add_event(session, employee, owner, gate, '21:30:01')
        assert await apply_event(session, outside, now=at('22:00')) is None


async def test_holiday_manual_and_leave_survive_recompute(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        day = await recompute_day(session, employee.id, DAY, now=at('22:00'))
        day_id, employee_id = day.id, employee.id
    headers = await auth(factory, 1)
    response = await client.patch(f'/api/v1/attendance/days/{day_id}', headers=headers,
        json={'check_in_at': at('08:30').isoformat(), 'check_out_at': at('17:30').isoformat(), 'reason': 'Sửa trong test'})
    assert response.status_code == 200, response.text
    validate('AttendanceDay', response.json())
    async with factory() as session, session.begin():
        employee = await session.get(Employee, employee_id)
        await add_event(session, employee, owner, gate, '08:00')
        day = await recompute_day(session, employee_id, DAY, now=at('22:00'))
        assert day.source == 'MANUAL' and day.check_in_at == at('08:30') and day.status == 'NORMAL'
    response = await client.post('/api/v1/attendance/leave', headers=headers,
        json={'employee_id': str(employee_id), 'dates': [str(DAY)], 'reason': 'Nghỉ phép kiểm thử'})
    assert response.status_code == 200 and response.json()[0]['status'] == 'LEAVE'
    async with factory() as session, session.begin():
        assert (await recompute_day(session, employee_id, DAY, now=at('22:00'))).status == 'LEAVE'
        other = await session.scalar(select(Employee).where(Employee.code == 'NV007'))
        session.add(Holiday(company_id=other.company_id, date=DAY, name='Lễ test'))
        await session.flush()
        assert (await recompute_day(session, other.id, DAY, now=at('22:00'))).status == 'HOLIDAY'
        assert (await recompute_day(session, employee_id, DAY, now=at('22:00'))).status == 'HOLIDAY'
        await session.delete(await session.get(Holiday, (other.company_id, DAY)))
        await session.flush()
        assert (await recompute_day(session, employee_id, DAY, now=at('22:00'))).status == 'LEAVE'


async def test_schedule_contract_and_overlap(runtime):
    client, factory, _ = runtime
    headers = await auth(factory, 1)
    invalid = await client.post('/api/v1/shifts', headers=headers, json={'name': 'Ca đêm test', 'start_time': '22:00', 'end_time': '06:00'})
    assert invalid.status_code == 422
    for body in [dict(name='Quá dài', start_time='00:00', end_time='18:00'),
                 dict(name='Nghỉ sai', start_time='08:00', end_time='17:00', break_start='07:00', break_end='09:00')]:
        assert (await client.post('/api/v1/shifts', headers=headers, json=body)).status_code == 422
    response = await client.post('/api/v1/shifts', headers=headers, json={'name': 'Ca API test', 'start_time': '08:30', 'end_time': '17:30'})
    assert response.status_code == 201
    validate('Shift', response.json())
    async with factory() as session:
        employee = await session.scalar(select(Employee).where(Employee.code == 'NV006'))
    body = dict(shift_id=response.json()['id'], employee_id=str(employee.id), weekdays=[1], effective_from=str(DAY))
    created = await client.post('/api/v1/shift-assignments', headers=headers, json=body)
    assert created.status_code == 201, created.text
    validate('ShiftAssignment', created.json()[0])
    overlap = await client.post('/api/v1/shift-assignments', headers=headers, json=body)
    assert overlap.status_code == 409 and overlap.json()['error']['code'] == 'ASSIGNMENT_OVERLAP'
    manager = await auth(factory, 5)
    assert (await client.get('/api/v1/shifts', headers=manager)).status_code == 200
    assert (await client.post('/api/v1/shifts', headers=manager, json={'name': 'Blocked', 'start_time': '08:00', 'end_time': '17:00'})).status_code == 403
    assert (await client.delete('/api/v1/shift-assignments/'+created.json()[0]['id'], headers=headers)).status_code == 204
    holiday = await client.post('/api/v1/holidays', headers=headers, json={'date': '2030-01-02', 'name': 'Lễ API test'})
    assert holiday.status_code == 201
    validate('Holiday', holiday.json())
    assert (await client.get('/api/v1/holidays?year=2030', headers=await auth(factory, 6))).status_code == 200
    assert (await client.delete('/api/v1/holidays/2030-01-02', headers=headers)).status_code == 204


async def test_requests_approve_reject_cancel_and_self_protection(runtime):
    client, factory, _ = runtime
    employee_headers, manager_headers = await auth(factory, 6), await auth(factory, 5)
    async with factory() as session, session.begin():
        employee, _, _, _ = await setup(session)
        await recompute_day(session, employee.id, DAY, now=at('22:00'))
    body = dict(work_date=str(DAY), type='FORGOT_IN', requested_in=at('08:30').isoformat(), requested_out=at('17:30').isoformat(), reason='Fixture giải trình')
    response = await client.post('/api/v1/me/requests', headers=employee_headers, json=body)
    assert response.status_code == 201, response.text
    validate('AttendanceRequest', response.json())
    identity = response.json()['id']
    duplicate = await client.post('/api/v1/me/requests', headers=employee_headers, json=body)
    assert duplicate.status_code == 409 and duplicate.json()['error']['code'] == 'REQUEST_PENDING_EXISTS'
    self_review = await client.post(f'/api/v1/attendance/requests/{identity}/approve', headers=await auth(factory, 1), json={})
    assert self_review.status_code == 403  # Owner không thay Manager team cho người gửi thường.
    response = await client.post(f'/api/v1/attendance/requests/{identity}/approve', headers=manager_headers, json={})
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'APPROVED'
    async with factory() as session:
        day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id, AttendanceDay.work_date == DAY))
        assert day.source == 'ADJUSTED' and day.check_in_at == at('08:30')
    month = await client.get('/api/v1/me/attendance?month=2026-11', headers=employee_headers)
    assert month.json()['summary']['work_days'] == 1
    assert (await client.post(f'/api/v1/attendance/requests/{identity}/approve', headers=manager_headers, json={})).status_code == 422
    body['type'] = 'OTHER'
    body['requested_in'], body['requested_out'] = at('08:00').isoformat(), at('18:00').isoformat()
    created = await client.post('/api/v1/me/requests', headers=employee_headers, json=body)
    second = created.json()['id']
    assert (await client.post(f'/api/v1/attendance/requests/{second}/reject', headers=manager_headers, json={})).status_code == 400
    assert (await client.post(f'/api/v1/attendance/requests/{second}/reject', headers=manager_headers, json={'note': 'Từ chối fixture'})).status_code == 200
    async with factory() as session:
        day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee.id, AttendanceDay.work_date == DAY))
        assert day.check_in_at == at('08:30') and day.check_out_at == at('17:30')
    third = await client.post('/api/v1/me/requests', headers=employee_headers, json=body)
    path = '/api/v1/me/requests/'+third.json()['id']+'/cancel'
    assert (await client.post(path, headers=await auth(factory, 7))).status_code == 403
    assert (await client.post(path, headers=employee_headers)).json()['status'] == 'CANCELLED'


async def test_manual_self_edit_scope_and_me_contracts(runtime):
    client, factory, _ = runtime
    owner_headers = await auth(factory, 1)
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        own_employee = await session.get(Employee, owner.employee_id)
        own_day = await recompute_day(session, own_employee.id, DAY, now=at('22:00'))
        own_id, employee_id, gate_id = own_day.id, employee.id, gate.id
        employee.attendance_method = 'MANUAL'
        own_employee.attendance_method = 'MANUAL'
    assert (await client.patch(f'/api/v1/attendance/days/{own_id}', headers=owner_headers, json={'reason': 'Không được sửa mình'})).json()['error']['code'] == 'SELF_EDIT_FORBIDDEN'
    body = dict(employee_id=str(owner.employee_id), gate_id=str(gate_id), reason='Không tự chấm hộ')
    response = await client.post('/api/v1/attendance/manual', headers=owner_headers, json=body)
    assert response.status_code == 403 and response.json()['error']['code'] == 'SELF_MANUAL_FORBIDDEN'
    body['employee_id'] = str(employee_id)
    response = await client.post('/api/v1/attendance/manual', headers=await auth(factory, 20), json=body)
    assert response.status_code == 201, response.text
    validate('Event', response.json())
    employee_headers = await auth(factory, 6)
    for path, schema in [('/me/today', 'MeToday'), ('/me/attendance?month=2026-11', 'MeMonth'),
                         ('/me/days/2026-11-16', 'MeDay'), ('/me/requests', 'PageAttendanceRequest')]:
        response = await client.get('/api/v1'+path, headers=employee_headers)
        assert response.status_code == 200, response.text
        validate(schema, response.json())
    manager = await auth(factory, 5)
    response = await client.get('/api/v1/attendance/days?from=2026-11-01&to=2026-11-30', headers=manager)
    assert response.status_code == 200
    validate('PageAttendanceDay', response.json())
    assert all(row['employee']['department_id'] == str(employee.department_id) for row in response.json()['items'])
    assert (await client.get('/api/v1/attendance/export?month=2026-11&department_id='+str(own_employee.department_id), headers=manager)).status_code == 403


async def test_excel_two_sheets_unique_day_dates_and_manager_scope(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        employee.full_name = '=FORMULA_TEST'
        await add_event(session, employee, owner, gate, '08:41')
        await add_event(session, employee, owner, gate, '17:30')
        day = await recompute_day(session, employee.id, DAY, now=at('22:00'))
        assert day.status == 'LATE'
    response = await client.get('/api/v1/attendance/export?month=2026-11', headers=await auth(factory, 5))
    assert response.status_code == 200, response.text
    workbook = load_workbook(BytesIO(response.content))
    assert workbook.sheetnames == ['Tổng hợp', 'Chi tiết']
    assert [cell.value for cell in workbook['Tổng hợp'][1]] == TOTAL_COLUMNS
    assert [cell.value for cell in workbook['Chi tiết'][1]] == DETAIL_COLUMNS
    total = next(row for row in workbook['Tổng hợp'].iter_rows(min_row=2, values_only=True) if row[0] == 'NV006')
    assert total[1] == "'=FORMULA_TEST" and total[3:6] == (1, 1, 11)
    assert {row[2].value for row in workbook['Tổng hợp'].iter_rows(min_row=2)} == {'Kỹ thuật'}
    detail = workbook['Chi tiết']
    record = next(row for row in detail.iter_rows(min_row=2) if row[0].value == 'NV006')
    assert record[2].number_format == 'dd/mm/yyyy' and record[4].number_format == 'hh:mm'
    assert record[6].value == 'Đi muộn' and record[8].value == 11
    report = os.environ.get('T09_REPORT_DIR')
    if report:
        (Path(report) / 'bang-cong-2026-11-test.xlsx').write_bytes(response.content)


async def test_access_only_match_does_not_count(runtime, model_row):
    _, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        gate.mode = 'ACCESS_ONLY'
        model = await session.scalar(select(RecognitionModel).where(RecognitionModel.manifest_id == model_row['manifest_id']))
        assert model is not None  # Manifest thật đã có trong seed chính thức.
        device = Device(company_id=employee.company_id, gate_id=gate.id, name='Fixture device')
        session.add(device)
        await session.flush()
        event = RecognitionEvent(company_id=employee.company_id, employee_id=employee.id, gate_id=gate.id,
            device_id=device.id, model_id=model.id, occurred_at=at('08:30'), result='MATCH', door_action='OPEN',
            top1_score=.99, threshold_used=.5, n_frames=5)
        session.add(event)
        await session.flush()
        assert await apply_event(session, event, now=at('22:00')) is None
        assert (await recompute_day(session, employee.id, DAY, now=at('22:00'))).status == 'ABSENT'


async def test_match_result_in_out_is_committed_with_event(runtime):
    _, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        employee.face_consent_at = utcnow()
        employee.face_consent_by = owner.id
        gate.default_policy = 'ALLOW_ALL_ACTIVE'
        model = await session.scalar(select(RecognitionModel).where(RecognitionModel.is_active.is_(True)))
        device = Device(company_id=employee.company_id, gate_id=gate.id, name='Fixture MATCH', status='ACTIVE',
                        token_hash='0' * 64, token_expires_at=utcnow()+timedelta(days=1))
        session.add(device)
        await session.flush()
        employee_id, model_id = employee.id, model.id
    payload = {'tau': .5, 'threshold_level': 'DEFAULT_VAL'}
    for value, expected in [('08:30', 'IN'), ('17:30', 'OUT')]:
        inferred = {'decision': Decision('MATCH', employee_id=employee_id, score=.99, n_frames=5),
                    'occurred_at': at(value), 'model_id': model_id}
        result = await record_decision(factory, device, payload, inferred)
        assert result['result'] == 'OK' and result['attendance']['kind'] == expected
        assert result['attendance']['status'] == 'IN_PROGRESS'
    async with factory() as session:
        day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == employee_id, AttendanceDay.work_date == DAY))
        assert day.check_in_at == at('08:30') and day.check_out_at == at('17:30')


async def test_scheduler_uses_shift_closing_time_and_finalizes(runtime, monkeypatch):
    _, factory, _ = runtime
    import app.biz.attendance_scheduler as scheduler_module
    import app.biz.attendance as attendance_module
    async with factory() as session, session.begin():
        employee, _, _, _ = await setup(session)
        identity = employee.id
    monkeypatch.setattr(scheduler_module, 'utcnow', lambda: at('09:00'))
    scheduler = scheduler_module.AttendanceScheduler(factory)
    await scheduler.reconcile()
    job = scheduler.scheduler.get_job(f'attendance/{identity}/{DAY}')
    assert job is not None and job.trigger.run_date == at('21:30')
    monkeypatch.setattr(attendance_module, 'utcnow', lambda: at('21:30'))
    await scheduler.close_day(identity, DAY)
    async with factory() as session:
        day = await session.scalar(select(AttendanceDay).where(AttendanceDay.employee_id == identity, AttendanceDay.work_date == DAY))
        assert day.finalized and day.status == 'ABSENT'


async def test_invalid_request_empty_reason_and_manual_gate_are_rejected(runtime):
    client, factory, _ = runtime
    headers = await auth(factory, 6)
    for body in [dict(work_date=str(DAY), type='FORGOT_IN', reason='Thiếu giờ'),
                 dict(work_date=str(DAY), type='OTHER', reason='   '),
                 dict(work_date=str(DAY), type='OTHER', reason='Giờ đảo', requested_in=at('17:30').isoformat(), requested_out=at('08:30').isoformat())]:
        assert (await client.post('/api/v1/me/requests', headers=headers, json=body)).status_code in (400, 422)
    async with factory() as session, session.begin():
        employee, _, gate, _ = await setup(session)
        gate.mode = 'ACCESS_ONLY'
        employee.attendance_method = 'MANUAL'
        body = dict(employee_id=str(employee.id), gate_id=str(gate.id), reason='Chọn sai cửa')
    assert (await client.post('/api/v1/attendance/manual', headers=await auth(factory, 20), json=body)).status_code == 422


@pytest.mark.parametrize('out,selected', [('08:59:59', False), ('09:00', True), ('09:00:01', True)])
async def test_checkout_exact_thirty_minute_boundary(runtime, out, selected):
    _, factory, _ = runtime
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        await add_event(session, employee, owner, gate, '08:30')
        last = await add_event(session, employee, owner, gate, out)
        day = await recompute_day(session, employee.id, DAY, now=at('22:00'))
        assert (day.check_out_event_id == last.id) is selected
