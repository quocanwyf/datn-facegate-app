from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,Request
from sqlalchemy import delete,func,select
from app.api.contract import body_contract
from app.auth.dependencies import Database,Principal,require_roles
from app.biz.admin import audit,has_role,scoped
from app.db.models import Department,Device,Gate,RecognitionModel,ThresholdProfile,t_gate_allowed_department
from app.errors import ApiError

router=APIRouter(prefix='/api/v1/gates',tags=['Gates'])
Reader=Annotated[Principal,Depends(require_roles('OWNER','HR','SECURITY'))]
Admin=Annotated[Principal,Depends(require_roles('OWNER','HR'))]
Owner=Annotated[Principal,Depends(require_roles('OWNER'))]


async def gate_view(session,gate,app):
    threshold=gate.custom_threshold
    if gate.threshold_level!='CUSTOM':
        threshold=await session.scalar(select(ThresholdProfile.cos_threshold).join(RecognitionModel,RecognitionModel.id==ThresholdProfile.model_id)
                                      .where(RecognitionModel.is_active,ThresholdProfile.level==gate.threshold_level))
    if threshold is None:raise ApiError(422,'VALIDATION_ERROR','Thiếu ngưỡng nhận dạng của cửa.')
    departments=list((await session.scalars(select(t_gate_allowed_department.c.department_id).where(t_gate_allowed_department.c.gate_id==gate.id))).all())
    devices=list((await session.scalars(select(Device.id).where(Device.gate_id==gate.id,Device.status=='ACTIVE'))).all())
    return {'id':str(gate.id),'name':gate.name,'mode':gate.mode,'default_policy':gate.default_policy,
            'allowed_department_ids':[str(id) for id in departments],'threshold_level':gate.threshold_level,
            'custom_threshold':gate.custom_threshold,'effective_threshold':threshold,'is_active':gate.is_active,
            'devices_online':sum(id in app.state.kiosk_connections for id in devices),'devices_total':len(devices)}


def check_threshold(values):
    custom=values.get('custom_threshold')
    if (values['threshold_level']=='CUSTOM') != (custom is not None) or (custom is not None and not -1<=custom<=1):
        raise ApiError(422,'VALIDATION_ERROR','Ngưỡng tùy chỉnh phải trong [-1,1] và chỉ có khi chọn CUSTOM.')


@router.get('',operation_id='getGates')
async def gates(session:Database,principal:Reader,request:Request)->list[dict]:
    rows=(await session.scalars(select(Gate).where(Gate.company_id==principal.account.company_id).order_by(Gate.name))).all()
    return [await gate_view(session,row,request.app) for row in rows]


@router.post('',operation_id='postGates',status_code=201)
async def create_gate(body:Annotated[dict,Depends(body_contract('GateInput'))],session:Database,principal:Owner,request:Request)->dict:
    if not all(key in body for key in ('name','mode','default_policy','threshold_level')):
        raise ApiError(400,'VALIDATION_ERROR','Vui lòng nhập đầy đủ thông tin cửa.')
    check_threshold(body)
    gate=Gate(company_id=principal.account.company_id,**body)
    session.add(gate);await session.flush();audit(session,principal,'GATE_CREATE','gate',gate.id)
    return await gate_view(session,gate,request.app)


@router.patch('/{id}',operation_id='patchGatesById')
async def patch_gate(id:UUID,body:Annotated[dict,Depends(body_contract('GateInput'))],session:Database,principal:Admin,request:Request)->dict:
    if not has_role(principal,'OWNER') and any(key!='default_policy' for key in body):
        raise ApiError(403,'FORBIDDEN','Nhân sự chỉ được sửa chính sách cửa.')
    gate=await scoped(session,Gate,id,principal,True)
    merged={key:getattr(gate,key) for key in ('threshold_level','custom_threshold')}
    merged.update(body);check_threshold(merged)
    for key,value in body.items():setattr(gate,key,value)
    await session.flush();audit(session,principal,'GATE_UPDATE','gate',id)
    result=await gate_view(session,gate,request.app)
    return result


@router.put('/{id}/allowed-departments',operation_id='putGatesAllowedDepartments')
async def allowed_departments(id:UUID,body:Annotated[dict,Depends(body_contract('IdList'))],session:Database,principal:Admin,request:Request)->dict:
    gate=await scoped(session,Gate,id,principal,True)
    ids=set(UUID(value) for value in body['department_ids'])
    for department_id in ids:await scoped(session,Department,department_id,principal)
    await session.execute(delete(t_gate_allowed_department).where(t_gate_allowed_department.c.gate_id==id))
    if ids:await session.execute(t_gate_allowed_department.insert(),[{'gate_id':id,'department_id':department_id} for department_id in ids])
    audit(session,principal,'GATE_POLICY_UPDATE','gate',id)
    return await gate_view(session,gate,request.app)
