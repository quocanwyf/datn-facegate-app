"""Fixture event chỉ trong transaction rollback; không phải phép quét/độ trễ AI."""
from datetime import datetime, timedelta
from io import StringIO
import csv
import os
from uuid import UUID
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import func, select
from app.auth.dependencies import Principal
from app.auth.security import utcnow
from app.api.ws_monitor import permitted_event
from app.db.models import Company, Device, Employee, FaceSample, Gate, RecognitionEvent, RecognitionModel, UserAccount, UserRole
from test_auth import runtime, validate
from test_admin_api import auth

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB T11 riêng')]


async def fixture(session):
    owner = await session.scalar(select(UserAccount).where(UserAccount.email == 'nv001@demo.local'))
    gate = await session.scalar(select(Gate).where(Gate.company_id == owner.company_id))
    employee = await session.scalar(select(Employee).where(Employee.code == 'NV006'))
    model = await session.scalar(select(RecognitionModel).where(RecognitionModel.is_active.is_(True)))
    device = Device(company_id=owner.company_id, gate_id=gate.id, name='Fixture event T11')
    session.add(device)
    await session.flush()
    event = RecognitionEvent(company_id=owner.company_id, gate_id=gate.id, device_id=device.id, model_id=model.id,
        occurred_at=utcnow(), result='UNKNOWN', door_action='NONE', n_frames=5)
    session.add(event)
    await session.flush()
    return owner, gate, employee, event


async def test_handle_is_employee_never_adds_samples_and_hr_cannot_handle(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        owner, gate, employee, event = await fixture(session)
        before = await session.scalar(select(func.count()).select_from(FaceSample))
        event_id, employee_id = event.id, employee.id
    path = f'/api/v1/events/{event_id}/handle'
    assert (await client.post(path, headers=await auth(factory, 2), json={'status': 'RESOLVED'})).status_code == 403
    assert (await client.post(path, headers=await auth(factory, 20), json={'status': 'IS_EMPLOYEE'})).status_code == 422
    response = await client.post(path, headers=await auth(factory, 20), json={'status': 'IS_EMPLOYEE', 'linked_employee_id': str(employee_id), 'note': 'Fixture bảo vệ nhận biết'})
    assert response.status_code == 200, response.text
    validate('Event', response.json())
    assert response.json()['handling']['linked_employee']['id'] == str(employee_id)
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(FaceSample)) == before
        assert (await session.get(RecognitionEvent, event_id)).result == 'UNKNOWN'
    unhandled = await client.get('/api/v1/events', headers=await auth(factory, 1), params={'result': ['UNKNOWN', 'SPOOF'], 'handled': 'false'})
    assert event_id not in {UUID(row['id']) for row in unhandled.json()['items']}


async def test_manual_open_no_attendance_and_csv_utf8_bom(runtime):
    client, factory, _ = runtime
    headers = await auth(factory, 1)
    async with factory() as session:
        gate = await session.scalar(select(Gate))
        before = await session.scalar(select(func.count()).select_from(RecognitionEvent))
    assert (await client.post(f'/api/v1/gates/{gate.id}/manual-open', headers=await auth(factory, 2), json={'reason': 'HR không mở cửa'})).status_code == 403
    assert (await client.post(f'/api/v1/gates/{gate.id}/manual-open', headers=headers, json={'reason': ' '})).status_code == 400
    response = await client.post(f'/api/v1/gates/{gate.id}/manual-open', headers=headers, json={'reason': '=Không được thành công thức'})
    assert response.status_code == 201
    validate('Event', response.json())
    assert response.json()['result'] == 'MANUAL_OPEN' and response.json()['employee'] is None
    listed = await client.get('/api/v1/events', headers=headers, params={'result': 'MANUAL_OPEN', 'page': 1, 'size': 10})
    validate('PageEvent', listed.json())
    assert listed.json()['total'] >= 1
    csv_response = await client.get('/api/v1/events/export', headers=headers, params={'result': 'MANUAL_OPEN'})
    assert csv_response.status_code == 200 and csv_response.content.startswith(b'\xef\xbb\xbf')
    rows = list(csv.reader(StringIO(csv_response.content.decode('utf-8-sig'))))
    assert rows[0][0] == 'Thời gian' and any(row[-1] == "'=Không được thành công thức" for row in rows[1:])
    assert (await client.get('/api/v1/events/export', headers=await auth(factory, 5))).status_code == 403
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(RecognitionEvent)) == before + 1


async def test_manager_team_security_company_and_snapshot_scope(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        owner, gate, employee, unknown = await fixture(session)
        owner_event = RecognitionEvent(company_id=owner.company_id, gate_id=gate.id, occurred_at=utcnow(),
            result='MANUAL_OPEN', door_action='OPEN', performed_by_user_id=owner.id, reason='Fixture khác team')
        team_event = RecognitionEvent(company_id=owner.company_id, gate_id=gate.id, employee_id=employee.id,
            occurred_at=utcnow(), result='MANUAL_ATTENDANCE', door_action='NONE', performed_by_user_id=owner.id, reason='Fixture cùng team')
        company = Company(name='Công ty fixture ngoài phạm vi', timezone='Asia/Ho_Chi_Minh', settings={})
        session.add(company)
        await session.flush()
        foreign_gate = Gate(company_id=company.id, name='Cửa ngoài phạm vi', mode='ACCESS_ONLY', default_policy='ALLOW_ALL_ACTIVE', threshold_level='DEFAULT_VAL')
        session.add(foreign_gate)
        await session.flush()
        foreign = RecognitionEvent(company_id=company.id, gate_id=foreign_gate.id, occurred_at=utcnow(),
            result='MANUAL_OPEN', door_action='OPEN', performed_by_user_id=owner.id, reason='Fixture ngoài công ty')
        session.add_all([owner_event, team_event, foreign])
        await session.flush()
        manager = await session.scalar(select(UserAccount).where(UserAccount.email == 'nv005@demo.local'))
        grants = list((await session.scalars(select(UserRole).where(UserRole.user_id == manager.id))).all())
        assert await permitted_event(session, Principal(manager, grants), team_event.id) is not None
        assert await permitted_event(session, Principal(manager, grants), unknown.id) is None
        assert await permitted_event(session, Principal(manager, grants), owner_event.id) is None
        security = await session.scalar(select(UserAccount).where(UserAccount.email == 'nv020@demo.local'))
        roles = list((await session.scalars(select(UserRole).where(UserRole.user_id == security.id))).all())
        assert await permitted_event(session, Principal(security, roles), foreign.id) is None
        assert await permitted_event(session, Principal(security, roles), unknown.id) is not None
        team_id, foreign_id, unknown_id = team_event.id, foreign.id, unknown.id
    manager_response = await client.get('/api/v1/events', headers=await auth(factory, 5), params={'size': 100})
    ids = {row['id'] for row in manager_response.json()['items']}
    assert str(team_id) in ids and str(unknown_id) not in ids and str(foreign_id) not in ids
    security_response = await client.get('/api/v1/events', headers=await auth(factory, 20), params={'size': 100})
    assert str(foreign_id) not in {row['id'] for row in security_response.json()['items']}
    assert (await client.get(f'/api/v1/events/{unknown_id}/snapshot', headers=await auth(factory, 5))).status_code == 403
    assert (await client.get(f'/api/v1/events/{unknown_id}/snapshot', headers=await auth(factory, 1))).status_code == 404


async def test_manual_report_counts_distinct_people(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        owner, gate, employee, _ = await fixture(session)
        other = await session.scalar(select(Employee).where(Employee.code == 'NV007'))
        for person in (employee, employee, other):
            session.add(RecognitionEvent(company_id=owner.company_id, gate_id=gate.id, employee_id=person.id,
                occurred_at=datetime(2030,1,2,8,tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')), result='MANUAL_ATTENDANCE', performed_by_user_id=owner.id, reason='Fixture báo cáo'))
    today = '2030-01-02'  # Tách khỏi manual event thật của các test WS khi chạy lại DB.
    response = await client.get('/api/v1/events/manual-report', headers=await auth(factory, 20), params={'from': today, 'to': today})
    assert response.status_code == 200, response.text
    row = next(row for row in response.json() if row['performed_by']['code'] == 'NV001')
    validate('ManualReportRow', row)
    assert row['count'] == 3 and row['distinct_employees'] == 2
    assert row['performed_by']['id'] == str(owner.id)  # Khóa người thực hiện là user_account.id.


async def test_security_employee_lookup_is_minimal_manual_only_and_roles_are_additive(runtime):
    client, factory, _ = runtime
    headers = await auth(factory, 20)
    response = await client.get('/api/v1/employees', headers=headers, params={'size': 100})
    assert response.status_code == 200
    validate('PageEmployee', response.json())
    assert response.json()['items']
    keys = {'id', 'code', 'full_name', 'department_id', 'department_name', 'status', 'attendance_method'}
    for row in response.json()['items']:
        assert set(row) <= keys and row['status'] == 'ACTIVE' and row['attendance_method'] == 'MANUAL'
    assert (await client.get('/api/v1/employees', headers=headers, params={'attendance_method': 'FACE'})).status_code == 403
    assert (await client.get('/api/v1/employees', headers=headers, params={'q': 'NV006'})).json()['total'] == 0
    assert (await client.get('/api/v1/employees/'+response.json()['items'][0]['id'], headers=headers)).status_code == 403
    async with factory() as session, session.begin():
        security = await session.scalar(select(UserAccount).where(UserAccount.email == 'nv020@demo.local'))
        employee = await session.scalar(select(Employee).where(Employee.code == 'NV006'))
        session.add(UserRole(user_id=security.id, role='MANAGER', scope_department_id=employee.department_id))
    combined = await client.get('/api/v1/employees', headers=headers, params={'size': 100})
    indexed = {row['code']: row for row in combined.json()['items']}
    assert 'NV006' in indexed and 'NV022' in indexed and 'NV001' not in indexed
    assert 'email' in indexed['NV006'] and set(indexed['NV022']) <= keys
