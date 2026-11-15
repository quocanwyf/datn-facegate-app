from datetime import timedelta
import os
import uuid
import pytest
from sqlalchemy import select, update
from app.auth.security import utcnow
from app.db.models import Employee, UserAccount
from test_auth import runtime, login, headers, validate
from test_pairing import provision

pytestmark=[pytest.mark.asyncio,pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'),reason='Cần PostgreSQL kiểm thử riêng')]


async def setup(client,factory):
    owner,invitation=await provision(client,factory)
    paired=await client.post('/api/v1/kiosk/pair',json={'code':invitation['pairing_code']})
    assert paired.status_code == 200
    auth={'Authorization':'Bearer '+paired.json()['device_token']}
    return owner,auth


async def test_pin_lock_commits_and_unlocks_after_expiry(runtime):
    client,factory,app=runtime
    owner,auth=await setup(client,factory)
    listed=await client.get('/api/v1/kiosk/enrollers',headers=auth)
    assert listed.status_code == 200 and len(listed.json()) == 2
    assert all(set(item) == {'user_id','name'} for item in listed.json())
    user_id=owner['user']['id']
    for expected,remaining in [(403,4),(403,3),(403,2),(403,1),(429,0)]:
        response=await client.post('/api/v1/kiosk/enroll/sessions',headers=auth,json={'user_id':user_id,'pin':'0000'})
        assert response.status_code == expected
        assert response.json()['error']['details']['remaining'] == remaining
    blocked=await client.post('/api/v1/kiosk/enroll/sessions',headers=auth,json={'user_id':user_id,'pin':'2468'})
    assert blocked.status_code == 429
    async with factory() as session,session.begin():
        account=await session.get(UserAccount,uuid.UUID(user_id))
        assert account.pin_failed_count == 5 and account.pin_locked_until > utcnow()
        account.pin_locked_until=utcnow()-timedelta(seconds=1)
    opened=await client.post('/api/v1/kiosk/enroll/sessions',headers=auth,json={'user_id':user_id,'pin':'2468'})
    assert opened.status_code == 201
    validate('EnrollSession',opened.json())


async def test_active_employee_filter_consent_and_session_expiry(runtime):
    client,factory,app=runtime
    owner,auth=await setup(client,factory)
    opened=await client.post('/api/v1/kiosk/enroll/sessions',headers=auth,json={'user_id':owner['user']['id'],'pin':'2468'})
    assert opened.status_code == 201
    id=opened.json()['enroll_session_id']
    prefix='/api/v1/kiosk/enroll/sessions/'+id
    employees=await client.get(prefix+'/employees',headers=auth)
    assert employees.status_code == 200
    assert 'NV019' not in {e['code'] for e in employees.json()}
    target=next(e for e in employees.json() if e['code']=='NV022')
    response=await client.post(prefix+'/consent',headers=auth,json={'employee_id':target['id'],'agree':True})
    assert response.status_code == 200 and response.json()['attendance_method']=='FACE'
    validate('KioskEmployee',response.json())
    async with factory() as session:
        employee=await session.get(Employee,uuid.UUID(target['id']))
        assert employee.face_consent_at and str(employee.face_consent_by) == owner['user']['id']
    withdrawn=await client.post(prefix+'/consent',headers=auth,json={'employee_id':target['id'],'agree':False})
    assert withdrawn.status_code == 200,withdrawn.text
    assert withdrawn.json()['attendance_method']=='MANUAL'
    async with factory() as session:
        employee=await session.get(Employee,uuid.UUID(target['id']))
        assert employee.face_consent_at is None and employee.face_consent_by is None and employee.biometric_deleted_at
    app.state.enroll_sessions.sessions[uuid.UUID(id)].expires_at=utcnow()-timedelta(seconds=1)
    expired=await client.get(prefix+'/employees',headers=auth)
    assert expired.status_code == 422 and expired.json()['error']['code']=='SESSION_EXPIRED'
