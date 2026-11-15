from typing import Annotated
from fastapi import APIRouter,Depends,Query,Request
from sqlalchemy import select
from app.api.contract import body_contract,source_contract
from app.auth.dependencies import Database,Principal,require_roles
from app.biz.admin import audit,page_result
from app.db.models import AuditLog,Company,Device,RecognitionModel,ThresholdProfile
from app.recog.decision import Params
from app.errors import ApiError

router=APIRouter(prefix='/api/v1',tags=['Settings'])
Reader=Annotated[Principal,Depends(require_roles('OWNER','HR'))]
Owner=Annotated[Principal,Depends(require_roles('OWNER'))]


def public_settings(settings):
    fields=source_contract()['components']['schemas']['RecognitionSettings']['properties']
    return {key:settings[key] for key in fields if key in settings}


@router.get('/settings/recognition',operation_id='getSettingsRecognition')
async def settings(session:Database,principal:Reader)->dict:
    return public_settings((await session.get(Company,principal.account.company_id)).settings)


@router.put('/settings/recognition',operation_id='putSettingsRecognition')
async def put_settings(body:Annotated[dict,Depends(body_contract('RecognitionSettings',422))],session:Database,principal:Owner,request:Request)->dict:
    company=await session.scalar(select(Company).where(Company.id==principal.account.company_id).with_for_update())
    merged=dict(company.settings);merged.update(public_settings(body))
    try:
        Params.from_settings(merged,0)
        if merged['anti_spoof_enabled']:
            # T13 bổ sung dấu hiệu hiệu chỉnh thật. T06 không cho tự bật bằng API.
            raise ValueError('Chống giả mạo chưa được hiệu chỉnh tại T13')
        if merged['max_fps']<=0 or merged['frame_long_side']<=0 or merged['min_face_px']<=0 or not 1<=merged['jpeg_quality']<=100:
            raise ValueError('Tham số khung hình không hợp lệ')
    except (ValueError,TypeError,KeyError):
        raise ApiError(422,'VALIDATION_ERROR','Cấu hình không hợp lệ hoặc chống giả mạo chưa được hiệu chỉnh tại T13.') from None
    company.settings=merged;audit(session,principal,'SETTINGS_UPDATE','company',company.id)
    await session.commit()
    service=request.app.state.kiosk_service
    if service:
        for connections in list(request.app.state.kiosk_connections.values()):
            for channel in list(connections.values()):
                try:await channel['send'](await service.config(channel['device']))
                except (RuntimeError,OSError):pass
    return public_settings(merged)


@router.get('/models/active',operation_id='getModelsActive')
async def active_model(session:Database,principal:Reader,request:Request)->dict:
    model=await session.scalar(select(RecognitionModel).where(RecognitionModel.is_active))
    if model is None:raise ApiError(404,'HTTP_404','Không có mô hình đang hoạt động.')
    thresholds=(await session.scalars(select(ThresholdProfile).where(ThresholdProfile.model_id==model.id).order_by(ThresholdProfile.level))).all()
    result={key:getattr(model,key) for key in ('code','name','epoch','source_sha256','stripped_sha256','t_bs','alignment_version','runtime')}
    result['thresholds']=[{key:getattr(row,key) for key in ('level','cos_threshold','label','source_ref')} for row in thresholds]
    if model.runtime.get('verified_at'):result['verified_at']=model.runtime['verified_at']
    return result


async def audit_view(session,row):
    from app.api.faces import account_name
    device=await session.get(Device,row.actor_device_id) if row.actor_device_id else None
    return {'id':row.id,'at':row.at,'actor':await account_name(session,row.actor_user_id),'actor_device':device.name if device else None,
            'action':row.action,'entity':row.entity,'entity_id':row.entity_id,'detail':row.detail}


@router.get('/audit-logs',operation_id='getAuditLogs',tags=['System'])
async def audit_logs(session:Database,principal:Owner,page:Annotated[int,Query(ge=1)]=1,size:Annotated[int,Query(ge=1,le=100)]=20)->dict:
    query=select(AuditLog).where(AuditLog.company_id==principal.account.company_id).order_by(AuditLog.at.desc(),AuditLog.id.desc())
    return await page_result(session,query,page,size,audit_view)
