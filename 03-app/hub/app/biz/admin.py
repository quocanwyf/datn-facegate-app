from datetime import date
import secrets
from uuid import UUID
from sqlalchemy import func,select
from app.auth.dependencies import department_scope
from app.db.models import AuditLog,Department,Employee,FaceProfile,UserAccount
from app.errors import ApiError


def audit(session,principal,action,entity,id):
    session.add(AuditLog(company_id=principal.account.company_id,actor_user_id=principal.account.id,action=action,entity=entity,entity_id=str(id)))


def has_role(principal,role):
    return any(grant.role==role for grant in principal.roles)


async def scoped(session,model,id,principal,lock=False):
    query=select(model).where(model.id==id,model.company_id==principal.account.company_id)
    row=await session.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    if row is None:raise ApiError(404,'HTTP_404','Không tìm thấy dữ liệu.')
    return row


async def department_exists(session,id,principal):
    return await scoped(session,Department,id,principal)


def employee_scope(principal,employee):
    scopes=department_scope(principal)
    if scopes is not None and employee.department_id not in scopes:
        raise ApiError(403,'FORBIDDEN','Bạn không có quyền truy cập nhân viên phòng ban này.')


def converted(data):
    result=dict(data)
    for key in ('department_id','employee_id'):
        if result.get(key) is not None:result[key]=UUID(result[key])
    if result.get('joined_at') is not None:result['joined_at']=date.fromisoformat(result['joined_at'])
    return result


async def employee_view(session,employee):
    department=await session.get(Department,employee.department_id)
    status=await session.scalar(select(FaceProfile.status).where(FaceProfile.employee_id==employee.id).order_by(FaceProfile.created_at.desc()).limit(1))
    user_id=await session.scalar(select(UserAccount.id).where(UserAccount.employee_id==employee.id))
    return {'id':str(employee.id),'code':employee.code,'full_name':employee.full_name,'email':employee.email,'phone':employee.phone,
            'department_id':str(employee.department_id),'department_name':department.name,'status':employee.status,
            'attendance_method':employee.attendance_method,'joined_at':employee.joined_at,'terminated_at':employee.terminated_at,
            'face_consent_at':employee.face_consent_at,'face_profile_status':status,'user_id':str(user_id) if user_id else None}


async def page_result(session,query,page,size,view):
    total=await session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    items=(await session.scalars(query.offset((page-1)*size).limit(size))).all()
    return {'items':[await view(session,item) for item in items],'total':total,'page':page,'size':size}


def temporary_password():
    return secrets.token_urlsafe(18)
