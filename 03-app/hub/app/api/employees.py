from typing import Annotated,Literal
from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request,Response
from sqlalchemy import and_, or_, select
from starlette.concurrency import run_in_threadpool
from app.api.contract import body_contract,source_contract
from app.auth.dependencies import Database,Principal,department_scope,require_roles
from app.auth.security import password_hasher,utcnow
from app.biz.admin import audit,converted,department_exists,employee_scope,employee_view,page_result,scoped,temporary_password
from app.biz.face_data import withdraw_consent
from app.biz.gallery_sync import reload_gallery
from app.db.models import Department,Employee,UserAccount,UserRole
from app.errors import ApiError

router=APIRouter(prefix='/api/v1/employees',tags=['Employees'])
Admin=Annotated[Principal,Depends(require_roles('OWNER','HR'))]
Reader=Annotated[Principal,Depends(require_roles('OWNER','HR','MANAGER'))]
ListReader=Annotated[Principal,Depends(require_roles('OWNER','HR','MANAGER','SECURITY'))]


@router.get('',operation_id='getEmployees')
async def employees(session:Database,principal:ListReader,q:str|None=None,department_id:UUID|None=None,
                    status:Literal['ACTIVE','SUSPENDED','TERMINATED']|None=None,attendance_method:Literal['FACE','MANUAL']|None=None,
                    page:Annotated[int,Query(ge=1)]=1,size:Annotated[int,Query(ge=1,le=100)]=20)->dict:
    query=select(Employee).where(Employee.company_id==principal.account.company_id)
    roles={grant.role for grant in principal.roles}
    global_reader=bool(roles.intersection({'OWNER','HR'}))
    manager_scopes={grant.scope_department_id for grant in principal.roles if grant.role=='MANAGER'}
    security='SECURITY' in roles
    if not global_reader:
        if department_id is not None and department_id not in manager_scopes and not security:
            raise ApiError(403,'FORBIDDEN','Bạn không có quyền xem phòng ban này.')
        allowed=Employee.department_id.in_(manager_scopes)
        if security:
            allowed=or_(allowed,and_(Employee.status=='ACTIVE',Employee.attendance_method=='MANUAL'))
        query=query.where(allowed)
        if security and not manager_scopes and (status not in (None,'ACTIVE') or attendance_method not in (None,'MANUAL')):
            raise ApiError(403,'FORBIDDEN','Bảo vệ chỉ tra cứu nhân viên đang hoạt động dùng chấm hộ.')
    if department_id:query=query.where(Employee.department_id==department_id)
    if status:query=query.where(Employee.status==status)
    if attendance_method:query=query.where(Employee.attendance_method==attendance_method)
    if q:query=query.where(Employee.code.ilike('%'+q+'%')|Employee.full_name.ilike('%'+q+'%'))
    async def visible_employee(session,item):
        if global_reader or item.department_id in manager_scopes:
            return await employee_view(session,item)
        department=await session.get(Department,item.department_id)
        return {**{key:str(getattr(item,key)) for key in ('id','department_id')},'code':item.code,
            'full_name':item.full_name,'department_name':department.name,'status':item.status,'attendance_method':item.attendance_method}
    return await page_result(session,query.order_by(Employee.code),page,size,visible_employee)


@router.get('/{id}',operation_id='getEmployeesById')
async def get_employee(id:UUID,session:Database,principal:Reader)->dict:
    employee=await scoped(session,Employee,id,principal)
    employee_scope(principal,employee)
    return await employee_view(session,employee)


@router.post('',operation_id='postEmployees',status_code=201)
async def create_employee(body:Annotated[dict,Depends(body_contract('EmployeeCreate'))],session:Database,principal:Admin)->dict:
    await department_exists(session,UUID(body['department_id']),principal)
    data=converted({key:value for key,value in body.items() if key in ('code','full_name','email','phone','department_id','joined_at')})
    employee=Employee(company_id=principal.account.company_id,**data)
    session.add(employee);await session.flush()
    password=None
    if body.get('create_account'):
        from jsonschema import FormatChecker
        if not employee.email or not FormatChecker().conforms(employee.email,'email'):
            raise ApiError(400,'VALIDATION_ERROR','Cần email hợp lệ để tạo tài khoản đăng nhập.')
        password=temporary_password()
        account=UserAccount(company_id=principal.account.company_id,email=employee.email,employee_id=employee.id,
                            password_hash=await run_in_threadpool(password_hasher.hash,password),must_change_password=True)
        session.add(account);await session.flush()
        session.add(UserRole(user_id=account.id,role='EMPLOYEE'))
        audit(session,principal,'USER_CREATE','user_account',account.id)
    audit(session,principal,'EMPLOYEE_CREATE','employee',employee.id)
    return {'employee':await employee_view(session,employee),'temporary_password':password}


@router.patch('/{id}',operation_id='patchEmployeesById')
async def patch_employee(id:UUID,body:Annotated[dict,Depends(body_contract('EmployeeUpdate'))],session:Database,principal:Admin)->dict:
    employee=await scoped(session,Employee,id,principal,True)
    allowed=source_contract()['components']['schemas']['EmployeeUpdate']['properties']
    updates=converted({key:value for key,value in body.items() if key in allowed})
    if 'department_id' in updates:await department_exists(session,updates['department_id'],principal)
    for key,value in updates.items():setattr(employee,key,value)
    await session.flush();audit(session,principal,'EMPLOYEE_UPDATE','employee',id)
    return await employee_view(session,employee)


async def transition(id,session,principal,request,source,target):
    employee=await scoped(session,Employee,id,principal,True)
    runtime=request.app.state.recognition
    key=f'employee/{employee.id}/status'
    retry=employee.status==target and runtime and runtime.mutations.pending(key)
    if employee.status!=source and not retry:
        raise ApiError(422,'VALIDATION_ERROR','Trạng thái nhân viên không cho phép thao tác này.')
    employee.status=target
    audit(session,principal,'EMPLOYEE_'+('SUSPEND' if target=='SUSPENDED' else 'REACTIVATE'),'employee',id)
    # Commit trước reload, nhưng tạm ngưng pipeline tới khi gallery mới sẵn sàng.
    completion=runtime.mutations.begin(key) if runtime else None
    await session.commit()
    await reload_gallery(request.app,completed=completion)
    return await employee_view(session,employee)


@router.post('/{id}/suspend',operation_id='postEmployeesSuspend')
async def suspend_employee(id:UUID,session:Database,principal:Admin,request:Request)->dict:
    return await transition(id,session,principal,request,'ACTIVE','SUSPENDED')


@router.post('/{id}/reactivate',operation_id='postEmployeesReactivate')
async def reactivate_employee(id:UUID,session:Database,principal:Admin,request:Request)->dict:
    return await transition(id,session,principal,request,'SUSPENDED','ACTIVE')


@router.post('/{id}/terminate',operation_id='postEmployeesTerminate',response_model=None)
async def terminate_employee(id:UUID,session:Database,principal:Admin,request:Request):
    employee=await scoped(session,Employee,id,principal,True)
    if employee.status=='TERMINATED' and employee.biometric_deleted_at is None:
        raise ApiError(422,'VALIDATION_ERROR','Nhân viên đã nghỉ việc.')
    employee.status,employee.terminated_at='TERMINATED',employee.terminated_at or utcnow()
    response=await withdraw_consent(request.app,session,employee,principal.account.id,action='EMPLOYEE_TERMINATE')
    if isinstance(response,Response):return response
    return await employee_view(session,employee)


@router.delete('/{id}/face',operation_id='deleteEmployeesFace',status_code=204,response_model=None)
async def delete_face(id:UUID,session:Database,principal:Admin,request:Request):
    employee=await scoped(session,Employee,id,principal,True)
    response=await withdraw_consent(request.app,session,employee,principal.account.id,action='FACE_DELETE')
    return response if isinstance(response,Response) else Response(status_code=204)
