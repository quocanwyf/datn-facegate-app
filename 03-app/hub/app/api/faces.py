import asyncio
from typing import Annotated,Literal
from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request,Response
from fastapi.responses import FileResponse,JSONResponse
from sqlalchemy import select,delete
from app.api.contract import body_contract
from app.auth.dependencies import Database,Principal,require_roles
from app.auth.security import utcnow
from app.biz.admin import audit,scoped,page_result
from app.biz.files import data_path,delete_private
from app.biz.gallery_sync import reload_gallery
from app.biz.face_data import withdraw_consent
from app.db.models import Department,Employee,FaceProfile,FaceSample,FaceTemplate,RecognitionModel,UserAccount
from app.errors import ApiError

router=APIRouter(prefix='/api/v1',tags=['Faces'])
Admin=Annotated[Principal,Depends(require_roles('OWNER','HR'))]
SelfUser=Annotated[Principal,Depends(require_roles('EMPLOYEE'))]


async def brief(session,id):
    if id is None:return None
    employee=await session.get(Employee,id)
    department=await session.get(Department,employee.department_id)
    return {'id':str(id),'code':employee.code,'full_name':employee.full_name,'department_id':str(employee.department_id),'department_name':department.name}


async def account_name(session,id):
    if not id:return None
    account=await session.get(UserAccount,id)
    employee=await session.get(Employee,account.employee_id) if account and account.employee_id else None
    return employee.full_name if employee else account.email if account else None


async def profile_view(session,profile):
    samples=(await session.scalars(select(FaceSample).where(FaceSample.profile_id==profile.id).order_by(FaceSample.created_at,FaceSample.id))).all()
    return {'id':str(profile.id),'employee':await brief(session,profile.employee_id),'status':profile.status,
            'enrolled_by':await account_name(session,profile.enrolled_by_user_id),'enrolled_at':profile.created_at,
            'duplicate_of':await brief(session,profile.duplicate_of_employee_id),'duplicate_score':profile.duplicate_score,
            'reviewed_by':await account_name(session,profile.reviewed_by_user_id),'reviewed_at':profile.reviewed_at,'review_note':profile.review_note,
            'samples':[{'id':str(sample.id),'det_score':sample.det_score,'yaw_ratio':sample.yaw_ratio,'p_live':sample.p_live,
                        'image_url':f'/api/v1/face-samples/{sample.id}/image'} for sample in samples]}


@router.get('/face-profiles',operation_id='getFaceProfiles')
async def profiles(session:Database,principal:Admin,status:Literal['PENDING_REVIEW','ACTIVE','REJECTED','SUPERSEDED']|None=None,
                   employee_id:UUID|None=None,page:Annotated[int,Query(ge=1)]=1,size:Annotated[int,Query(ge=1,le=100)]=20)->dict:
    query=select(FaceProfile).where(FaceProfile.company_id==principal.account.company_id)
    if status:query=query.where(FaceProfile.status==status)
    if employee_id:query=query.where(FaceProfile.employee_id==employee_id)
    return await page_result(session,query.order_by(FaceProfile.created_at.desc()),page,size,profile_view)


@router.get('/face-profiles/{id}',operation_id='getFaceProfilesById')
async def profile(id:UUID,session:Database,principal:Admin)->dict:
    return await profile_view(session,await scoped(session,FaceProfile,id,principal))


async def old_samples_cleanup(session,employee_id):
    ids=list((await session.scalars(select(FaceProfile.id).where(FaceProfile.employee_id==employee_id,FaceProfile.status=='SUPERSEDED'))).all())
    if not ids:return
    paths=list((await session.scalars(select(FaceSample.image_path).where(FaceSample.profile_id.in_(ids)))).all())
    await asyncio.to_thread(delete_private,paths)
    await session.execute(delete(FaceSample).where(FaceSample.profile_id.in_(ids)))
    await session.execute(delete(FaceTemplate).where(FaceTemplate.profile_id.in_(ids)))
    await session.commit()


async def review_profile(id,body,session,principal,request,approved):
    initial=await scoped(session,FaceProfile,id,principal)
    # Cùng thứ tự khóa với thu mẫu: employee trước profile, tránh deadlock.
    employee=await scoped(session,Employee,initial.employee_id,principal,True)
    profile=await scoped(session,FaceProfile,id,principal,True)
    key=f'employee/{employee.id}/review/{id}/'+('approve' if approved else 'reject')
    if profile.status!='PENDING_REVIEW':
        # Retry chỉ phục hồi các bước hậu commit bị lỗi, không xử lý hồ sơ lần hai.
        runtime=request.app.state.recognition
        if profile.status in ('ACTIVE','REJECTED') and runtime and runtime.mutations.pending(key):
            completion=runtime.mutations.begin(key)
            try:
                await old_samples_cleanup(session,employee.id)
            except OSError:
                return JSONResponse(status_code=503,content={'error':{'code':'BIOMETRIC_DELETE_INCOMPLETE','message':'Chưa xóa xong mẫu cũ. Vui lòng thử lại.'}})
            await reload_gallery(request.app,completed=completion)
        raise ApiError(409,'PROFILE_ALREADY_REVIEWED','Hồ sơ đã được xử lý.')
    note=body.get('note')
    if (not approved or profile.duplicate_of_employee_id is not None) and not (note and note.strip()):
        raise ApiError(422,'VALIDATION_ERROR','Vui lòng nhập lý do xử lý hồ sơ.')
    if approved and (employee.status not in ('ACTIVE','SUSPENDED') or employee.attendance_method!='FACE' or employee.face_consent_at is None):
        raise ApiError(422,'VALIDATION_ERROR','Nhân viên không còn đủ điều kiện dùng khuôn mặt.')
    old=[]
    if approved:
        active_model=await session.scalar(select(RecognitionModel.id).where(RecognitionModel.is_active))
        template=await session.scalar(select(FaceTemplate).where(FaceTemplate.profile_id==id,FaceTemplate.model_id==active_model))
        samples=(await session.scalars(select(FaceSample).where(FaceSample.profile_id==id))).all()
        if template is None or len(samples)!=5 or template.n_samples!=5:
            raise ApiError(422,'VALIDATION_ERROR','Hồ sơ chưa có đủ mẫu và template hợp lệ.')
        files_present=await asyncio.to_thread(lambda:all(data_path(sample.image_path).is_file() for sample in samples))
        if not files_present:raise ApiError(422,'VALIDATION_ERROR','Thiếu file mẫu khuôn mặt.')
        old=list((await session.scalars(select(FaceProfile).where(FaceProfile.employee_id==employee.id,FaceProfile.status=='ACTIVE',FaceProfile.id!=id))).all())
        for previous in old:previous.status='SUPERSEDED'
        await session.flush()
    profile.status='ACTIVE' if approved else 'REJECTED'
    profile.reviewed_by_user_id,profile.reviewed_at,profile.review_note=principal.account.id,utcnow(),note
    audit(session,principal,'FACE_APPROVE' if approved else 'FACE_REJECT','face_profile',id)
    runtime=request.app.state.recognition
    completion=runtime.mutations.begin(key) if runtime else None
    await session.commit()
    try:
        if approved:await old_samples_cleanup(session,employee.id)
    except OSError:
        return JSONResponse(status_code=503,content={'error':{'code':'BIOMETRIC_DELETE_INCOMPLETE','message':'Chưa xóa xong mẫu cũ. Máy chủ tạm ngưng nhận dạng.'}})
    await reload_gallery(request.app,completed=completion)
    return await profile_view(session,profile)


@router.post('/face-profiles/{id}/approve',operation_id='postFaceProfilesApprove',response_model=None)
async def approve(id:UUID,body:Annotated[dict,Depends(body_contract('ReviewInput'))],session:Database,principal:Admin,request:Request):
    return await review_profile(id,body,session,principal,request,True)


@router.post('/face-profiles/{id}/reject',operation_id='postFaceProfilesReject',response_model=None)
async def reject(id:UUID,body:Annotated[dict,Depends(body_contract('ReviewInput'))],session:Database,principal:Admin,request:Request):
    return await review_profile(id,body,session,principal,request,False)


@router.get('/face-samples/{id}/image',operation_id='getFaceSamplesImage',response_class=FileResponse)
async def sample_image(id:UUID,session:Database,principal:Admin):
    row=(await session.execute(select(FaceSample).join(FaceProfile,FaceProfile.id==FaceSample.profile_id).where(FaceSample.id==id,FaceProfile.company_id==principal.account.company_id))).scalar_one_or_none()
    if row is None:raise ApiError(404,'HTTP_404','Không tìm thấy ảnh mẫu.')
    path=data_path(row.image_path)
    if not await asyncio.to_thread(path.is_file):raise ApiError(404,'HTTP_404','Không tìm thấy ảnh mẫu.')
    return FileResponse(path,media_type='image/png',headers={'Cache-Control':'no-store'})


async def own_employee(session,principal,lock=False):
    if principal.account.employee_id is None:
        raise ApiError(403,'FORBIDDEN','Tài khoản chưa liên kết nhân viên.')
    return await scoped(session,Employee,principal.account.employee_id,principal,lock)


async def me_face_view(session,employee):
    status=await session.scalar(select(FaceProfile.status).where(FaceProfile.employee_id==employee.id).order_by(FaceProfile.created_at.desc()).limit(1))
    return {'attendance_method':employee.attendance_method,'face_consent_at':employee.face_consent_at,'face_profile_status':status}


@router.get('/me/face',operation_id='getMeFace',tags=['Me'])
async def me_face(session:Database,principal:SelfUser)->dict:
    return await me_face_view(session,await own_employee(session,principal))


@router.post('/me/face/revoke',operation_id='postMeFaceRevoke',tags=['Me'],response_model=None)
async def me_revoke(session:Database,principal:SelfUser,request:Request):
    employee=await own_employee(session,principal,True)
    response=await withdraw_consent(request.app,session,employee,principal.account.id)
    return response if isinstance(response,Response) else await me_face_view(session,employee)
