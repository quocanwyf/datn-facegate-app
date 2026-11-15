import os
from threading import Event
from types import SimpleNamespace
import uuid
import pytest
from sqlalchemy import select
from app.auth.security import encode_token,verify_password
from app.db.models import Department,Employee,UserAccount,UserRole,Company,AuditLog
from test_auth import runtime,validate

pytestmark=[pytest.mark.asyncio,pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'),reason='Cần PostgreSQL thử riêng')]


async def auth(factory,number):
    async with factory() as session:
        account=await session.scalar(select(UserAccount).where(UserAccount.email==f'nv{number:03}@demo.local'))
        token,_=encode_token(account.id,'access')
    return {'Authorization':'Bearer '+token}


@pytest.mark.parametrize('number,role',[(1,'OWNER'),(2,'HR'),(5,'MANAGER'),(20,'SECURITY'),(6,'EMPLOYEE')])
async def test_permission_matrix_reads(runtime,number,role):
    client,factory,app=runtime;headers=await auth(factory,number)
    cases=[('/dashboard/today',{'OWNER','HR'},'Dashboard'),('/employees',{'OWNER','HR','MANAGER'},'PageEmployee'),
           ('/departments',{'OWNER','HR','MANAGER','SECURITY'},None),('/users',{'OWNER','HR'},'PageUser'),
           ('/face-profiles',{'OWNER','HR'},'PageFaceProfile'),('/gates',{'OWNER','HR','SECURITY'},None),
           ('/settings/recognition',{'OWNER','HR'},'RecognitionSettings'),('/models/active',{'OWNER','HR'},'ModelActive'),
           ('/audit-logs',{'OWNER'},'PageAuditLog'),('/me/face',{'OWNER','HR','MANAGER','SECURITY','EMPLOYEE'},'MeFace')]
    for path,allowed,schema in cases:
        response=await client.get('/api/v1'+path,headers=headers)
        assert response.status_code==(200 if role in allowed else 403),(role,path,response.status_code)
        if response.status_code==200 and schema:validate(schema,response.json())
    print(f'permission_read_role={role}; cases={len(cases)}')


async def test_manager_scope_cannot_be_bypassed(runtime):
    client,factory,_=runtime;headers=await auth(factory,5)
    me=(await client.get('/api/v1/me',headers=headers)).json()
    scope=next(g['scope_department_id'] for g in me['roles'] if g['role']=='MANAGER')
    response=await client.get('/api/v1/employees',headers=headers,params={'size':100})
    assert response.status_code==200 and response.json()['items']
    assert all(item['department_id']==scope for item in response.json()['items'])
    async with factory() as session:
        outside=await session.scalar(select(Employee).where(Employee.department_id!=uuid.UUID(scope)))
    assert (await client.get('/api/v1/employees',headers=headers,params={'department_id':str(outside.department_id)})).status_code==403
    assert (await client.get('/api/v1/employees/'+str(outside.id),headers=headers)).status_code==403
    departments=(await client.get('/api/v1/departments',headers=headers)).json()
    assert {item['id'] for item in departments}=={scope}


@pytest.mark.parametrize('number',[1,2])
async def test_admin_writes_and_password_never_stored_plaintext(runtime,number):
    client,factory,_=runtime;headers=await auth(factory,number)
    department=await client.post('/api/v1/departments',headers=headers,json={'name':'Phòng thử T06'})
    assert department.status_code==201;validate('Department',department.json())
    updated=await client.patch('/api/v1/departments/'+department.json()['id'],headers=headers,json={'name':'Phòng thử T06 cập nhật'})
    assert updated.status_code==200
    body={'code':'T06_CREATED','full_name':'Nhân viên kiểm API','department_id':department.json()['id'],'email':'new-user@demo.local','create_account':True}
    response=await client.post('/api/v1/employees',headers=headers,json=body)
    assert response.status_code==201
    validate('EmployeeCreated',response.json())
    password=response.json()['temporary_password']
    assert password
    duplicate=await client.post('/api/v1/employees',headers=headers,json=body)
    assert duplicate.status_code==409
    id=response.json()['employee']['id']
    changed=await client.patch('/api/v1/employees/'+id,headers=headers,json={'full_name':'Tên đã sửa','status':'TERMINATED'})
    assert changed.status_code==200 and changed.json()['status']=='ACTIVE'
    async with factory() as session:
        account=await session.scalar(select(UserAccount).where(UserAccount.email==body['email']))
        assert account.password_hash!=password and verify_password(account.password_hash,password) and account.must_change_password
        assert await session.scalar(select(AuditLog.id).where(AuditLog.entity_id==id,AuditLog.action=='EMPLOYEE_CREATE'))
    print(f'admin_write_role={number}; employee_create_update_audit=true')


async def test_hr_cannot_manage_owner_or_gate_owner_fields(runtime):
    client,factory,_=runtime;headers=await auth(factory,2)
    async with factory() as session:
        owner=await session.scalar(select(UserAccount.id).where(UserAccount.email=='nv001@demo.local'))
    assert (await client.patch(f'/api/v1/users/{owner}',headers=headers,json={'status':'DISABLED'})).status_code==403
    assert (await client.post(f'/api/v1/users/{owner}/reset-password',headers=headers)).status_code==403
    assert (await client.put(f'/api/v1/users/{owner}/kiosk-pin',headers=headers,json={'pin':'1234'})).status_code==403
    assert (await client.post('/api/v1/users',headers=headers,json={'email':'blocked@demo.local','roles':[{'role':'OWNER'}]})).status_code==403
    gate=(await client.get('/api/v1/gates',headers=headers)).json()[0]
    id=gate['id']
    allowed=await client.patch('/api/v1/gates/'+id,headers=headers,json={'default_policy':'DEPARTMENTS_ONLY'})
    assert allowed.status_code==200
    for data in [{'name':'Cửa khác'},{'mode':'ACCESS_ONLY'},{'threshold_level':'STRICT_TEST'},{'custom_threshold':.5},{'is_active':False}]:
        assert (await client.patch('/api/v1/gates/'+id,headers=headers,json=data)).status_code==403
    departments=(await client.get('/api/v1/departments',headers=headers)).json()
    ids=[departments[0]['id']]
    allowed=await client.put('/api/v1/gates/'+id+'/allowed-departments',headers=headers,json={'department_ids':ids})
    assert allowed.status_code==200 and allowed.json()['allowed_department_ids']==ids
    assert (await client.get('/api/v1/settings/recognition',headers=headers)).status_code==200
    assert (await client.put('/api/v1/settings/recognition',headers=headers,json={'window_size':5})).status_code==403


async def test_owner_user_roles_reset_and_scope_validation(runtime):
    client,factory,_=runtime;headers=await auth(factory,1)
    created=await client.post('/api/v1/users',headers=headers,json={'email':'owner-api@demo.local','roles':[{'role':'OWNER'}]})
    assert created.status_code==201
    id=created.json()['user']['id'];password=created.json()['temporary_password']
    login=await client.post('/api/v1/auth/login',json={'email':'owner-api@demo.local','password':password})
    assert login.status_code==200
    assert (await client.get('/api/v1/me/face',headers={'Authorization':'Bearer '+login.json()['access_token']})).status_code==403
    reset=await client.post('/api/v1/users/'+id+'/reset-password',headers=headers)
    assert reset.status_code==200 and reset.json()['temporary_password']!=password
    assert (await client.post('/api/v1/auth/refresh',json={'refresh_token':login.json()['refresh_token']})).status_code==401
    invalid=await client.put('/api/v1/users/'+id+'/roles',headers=headers,json={'roles':[{'role':'MANAGER'}]})
    assert invalid.status_code==422
    department=(await client.get('/api/v1/departments',headers=headers)).json()[0]['id']
    valid=await client.put('/api/v1/users/'+id+'/roles',headers=headers,json={'roles':[{'role':'MANAGER','scope_department_id':department}]})
    assert valid.status_code==200 and valid.json()['roles'][0]['role']=='MANAGER'


async def test_settings_reject_atomically_and_preserve_old_configuration(runtime):
    client,factory,_=runtime;headers=await auth(factory,1)
    previous=(await client.get('/api/v1/settings/recognition',headers=headers)).json()
    for invalid in [{'window_size':0},{'window_size':2,'match_min':3},{'match_min':0},{'anti_spoof_enabled':True,'liveness_threshold':.5},
                    {'anti_spoof_enabled':True,'liveness_threshold':None},{'liveness_threshold':1.1}]:
        response=await client.put('/api/v1/settings/recognition',headers=headers,json=invalid)
        assert response.status_code==422
        assert (await client.get('/api/v1/settings/recognition',headers=headers)).json()==previous
    valid=await client.put('/api/v1/settings/recognition',headers=headers,json={'cooldown_employee_sec':61})
    assert valid.status_code==200 and valid.json()['cooldown_employee_sec']==61


async def test_non_admin_write_routes_forbidden(runtime):
    client,factory,_=runtime
    for number in (5,20,6):
        headers=await auth(factory,number)
        for method,path,body in [('post','/departments',{'name':'forbidden'}),('post','/employees',{'code':'x','full_name':'x','department_id':str(uuid.uuid4())}),
                                 ('post','/users',{'email':'x@demo.local','roles':[]}),('post','/gates',{}),
                                 ('post','/face-profiles/'+str(uuid.uuid4())+'/approve',{}),('post','/face-profiles/'+str(uuid.uuid4())+'/reject',{'note':'x'})]:
            assert (await client.request(method,'/api/v1'+path,headers=headers,json=body)).status_code==403
        assert (await client.get('/api/v1/face-samples/'+str(uuid.uuid4())+'/image',headers=headers)).status_code==403


@pytest.mark.parametrize('number',[1,2])
async def test_owner_and_hr_manage_non_owner_roles_pin_and_disable(runtime,number):
    client,factory,_=runtime;headers=await auth(factory,number)
    async with factory() as session:
        id=await session.scalar(select(UserAccount.id).where(UserAccount.email=='nv006@demo.local'))
    changed=await client.put(f'/api/v1/users/{id}/roles',headers=headers,json={'roles':[{'role':'HR'},{'role':'EMPLOYEE'}]})
    assert changed.status_code==200
    assert (await client.put(f'/api/v1/users/{id}/kiosk-pin',headers=headers,json={'pin':'1234'})).status_code==204
    reset=await client.post(f'/api/v1/users/{id}/reset-password',headers=headers)
    assert reset.status_code==200
    assert (await client.patch(f'/api/v1/users/{id}',headers=headers,json={'status':'DISABLED'})).status_code==200
    async with factory() as session:
        account=await session.get(UserAccount,id)
        assert account.status=='DISABLED' and verify_password(account.kiosk_pin_hash,'1234')


async def test_owner_creates_and_changes_gate_threshold(runtime):
    client,factory,_=runtime;headers=await auth(factory,1)
    created=await client.post('/api/v1/gates',headers=headers,json={'name':'Cửa thử T06','mode':'ACCESS_ONLY','default_policy':'ALLOW_ALL_ACTIVE','threshold_level':'STRICT_TEST'})
    assert created.status_code==201
    validate('Gate',created.json());id=created.json()['id']
    changed=await client.patch('/api/v1/gates/'+id,headers=headers,json={'threshold_level':'CUSTOM','custom_threshold':.6})
    assert changed.status_code==200 and changed.json()['effective_threshold']==.6
    invalid=await client.patch('/api/v1/gates/'+id,headers=headers,json={'custom_threshold':1.1})
    assert invalid.status_code==422
