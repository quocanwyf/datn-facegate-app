from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,Query,Response
from sqlalchemy import select,func,delete,update
from starlette.concurrency import run_in_threadpool
from app.api.auth import user_view as identity_view
from app.api.contract import body_contract
from app.auth.dependencies import Database,Principal,department_scope,require_roles
from app.auth.security import password_hasher,utcnow
from app.biz.admin import audit,scoped,has_role,temporary_password,page_result
from app.db.models import Department,Employee,UserAccount,UserRole,AuthRefreshToken
from app.errors import ApiError

router=APIRouter(prefix='/api/v1',tags=['Organization'])
Admin=Annotated[Principal,Depends(require_roles('OWNER','HR'))]
DepartmentReader=Annotated[Principal,Depends(require_roles('OWNER','HR','MANAGER','SECURITY'))]


async def department_view(session,department):
    count=await session.scalar(select(func.count()).select_from(Employee).where(Employee.department_id==department.id))
    return {'id':str(department.id),'name':department.name,'employee_count':count}


@router.get('/departments',operation_id='getDepartments')
async def departments(session:Database,principal:DepartmentReader)->list[dict]:
    query=select(Department).where(Department.company_id==principal.account.company_id)
    if has_role(principal,'MANAGER') and not any(has_role(principal,role) for role in ('OWNER','HR','SECURITY')):
        query=query.where(Department.id.in_(department_scope(principal)))
    return [await department_view(session,item) for item in (await session.scalars(query.order_by(Department.name))).all()]


@router.post('/departments',operation_id='postDepartments',status_code=201)
async def create_department(body:Annotated[dict,Depends(body_contract('DepartmentInput'))],session:Database,principal:Admin)->dict:
    department=Department(company_id=principal.account.company_id,name=body['name'])
    session.add(department);await session.flush()
    audit(session,principal,'DEPARTMENT_CREATE','department',department.id)
    return await department_view(session,department)


@router.patch('/departments/{id}',operation_id='patchDepartmentsById')
async def patch_department(id:UUID,body:Annotated[dict,Depends(body_contract('DepartmentInput'))],session:Database,principal:Admin)->dict:
    department=await scoped(session,Department,id,principal,True)
    department.name=body['name'];await session.flush()
    audit(session,principal,'DEPARTMENT_UPDATE','department',id)
    return await department_view(session,department)


async def roles_for(session,user_id):
    return list((await session.scalars(select(UserRole).where(UserRole.user_id==user_id))).all())


async def manageable_user(session,id,principal):
    account=await scoped(session,UserAccount,id,principal,True)
    if not has_role(principal,'OWNER') and any(role.role=='OWNER' for role in await roles_for(session,id)):
        raise ApiError(403,'FORBIDDEN','Nhân sự không được thay đổi tài khoản Chủ doanh nghiệp.')
    return account


async def validate_roles(session,roles,principal):
    seen=set()
    for grant in roles:
        role,scope=grant['role'],grant.get('scope_department_id')
        if role=='OWNER' and not has_role(principal,'OWNER'):
            raise ApiError(403,'FORBIDDEN','Nhân sự không được cấp vai trò Chủ doanh nghiệp.')
        if (role=='MANAGER') != (scope is not None):
            raise ApiError(422,'VALIDATION_ERROR','Vai trò quản lý cần đúng phạm vi phòng ban.')
        if scope:
            await scoped(session,Department,UUID(scope),principal)
        key=(role,str(UUID(scope)) if scope else None)
        if key in seen:raise ApiError(422,'VALIDATION_ERROR','Vai trò/phạm vi bị trùng.')
        seen.add(key)


async def account_view(session,account):
    identity=await identity_view(session,account)
    return {'id':str(account.id),'email':account.email,'status':account.status,'employee':identity.employee,
            'roles':identity.roles,'has_kiosk_pin':account.kiosk_pin_hash is not None,'last_login_at':account.last_login_at}


@router.get('/users',operation_id='getUsers')
async def users(session:Database,principal:Admin,page:Annotated[int,Query(ge=1)]=1,size:Annotated[int,Query(ge=1,le=100)]=20)->dict:
    query=select(UserAccount).where(UserAccount.company_id==principal.account.company_id).order_by(UserAccount.email)
    return await page_result(session,query,page,size,account_view)


@router.post('/users',operation_id='postUsers',status_code=201)
async def create_user(body:Annotated[dict,Depends(body_contract('UserCreate'))],session:Database,principal:Admin)->dict:
    await validate_roles(session,body['roles'],principal)
    employee_id=UUID(body['employee_id']) if body.get('employee_id') else None
    if employee_id:await scoped(session,Employee,employee_id,principal)
    password=temporary_password()
    account=UserAccount(company_id=principal.account.company_id,email=body['email'],employee_id=employee_id,
                        password_hash=await run_in_threadpool(password_hasher.hash,password),must_change_password=True)
    session.add(account);await session.flush()
    for grant in body['roles']:
        session.add(UserRole(user_id=account.id,role=grant['role'],scope_department_id=UUID(grant['scope_department_id']) if grant.get('scope_department_id') else None))
    await session.flush();audit(session,principal,'USER_CREATE','user_account',account.id)
    return {'user':await account_view(session,account),'temporary_password':password}


@router.patch('/users/{id}',operation_id='patchUsersById')
async def patch_user(id:UUID,body:Annotated[dict,Depends(body_contract('UserUpdate'))],session:Database,principal:Admin)->dict:
    account=await manageable_user(session,id,principal)
    if 'employee_id' in body:
        employee_id=UUID(body['employee_id']) if body['employee_id'] else None
        if employee_id:await scoped(session,Employee,employee_id,principal)
        account.employee_id=employee_id
    if 'status' in body:
        account.status=body['status']
        if account.status=='DISABLED':
            await session.execute(update(AuthRefreshToken).where(AuthRefreshToken.user_id==id,AuthRefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    await session.flush();audit(session,principal,'USER_UPDATE','user_account',id)
    return await account_view(session,account)


@router.put('/users/{id}/roles',operation_id='putUsersRoles')
async def put_roles(id:UUID,body:Annotated[dict,Depends(body_contract('RolesInput'))],session:Database,principal:Admin)->dict:
    account=await manageable_user(session,id,principal)
    await validate_roles(session,body['roles'],principal)
    await session.execute(delete(UserRole).where(UserRole.user_id==id))
    for grant in body['roles']:
        session.add(UserRole(user_id=id,role=grant['role'],scope_department_id=UUID(grant['scope_department_id']) if grant.get('scope_department_id') else None))
    await session.flush();audit(session,principal,'USER_ROLES_UPDATE','user_account',id)
    return await account_view(session,account)


@router.put('/users/{id}/kiosk-pin',operation_id='putUsersKioskPin',status_code=204)
async def put_pin(id:UUID,body:Annotated[dict,Depends(body_contract('PinInput'))],session:Database,principal:Admin)->Response:
    account=await manageable_user(session,id,principal)
    if not any(grant.role in ('OWNER','HR') for grant in await roles_for(session,id)):
        raise ApiError(422,'VALIDATION_ERROR','Chỉ tài khoản Chủ doanh nghiệp/Nhân sự dùng PIN Kiosk.')
    account.kiosk_pin_hash=await run_in_threadpool(password_hasher.hash,body['pin'])
    account.pin_failed_count,account.pin_locked_until=0,None
    audit(session,principal,'USER_PIN_UPDATE','user_account',id)
    return Response(status_code=204)


@router.post('/users/{id}/reset-password',operation_id='postUsersResetPassword')
async def reset_password(id:UUID,session:Database,principal:Admin)->dict:
    account=await manageable_user(session,id,principal)
    password=temporary_password()
    account.password_hash=await run_in_threadpool(password_hasher.hash,password)
    account.must_change_password=True
    await session.execute(update(AuthRefreshToken).where(AuthRefreshToken.user_id==id,AuthRefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    audit(session,principal,'USER_PASSWORD_RESET','user_account',id)
    return {'temporary_password':password}
