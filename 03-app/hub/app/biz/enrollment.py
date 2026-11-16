import asyncio
from uuid import uuid4
from sqlalchemy import select, delete
from app.biz.files import write_private, delete_private
from app.db.models import Employee, FaceProfile, FaceSample, FaceEmbedding, FaceTemplate, AuditLog,Device,UserAccount,UserRole
from app.errors import ApiError
from app.auth.security import utcnow


async def persist_enrollment(factory, device, enrollment, employee_id, prepared):
    profile_id = uuid4()
    written, old_paths = [], []
    committed = False
    try:
        if len(prepared['samples']) != 5:
            raise ValueError('Phải có đúng 5 mẫu hợp lệ')
        # Mẫu mới được ghi trước khi đụng PENDING cũ; lỗi IO không xóa hồ sơ cũ.
        for index, sample in enumerate(prepared['samples']):
            relative = f'faces/{profile_id}/{index + 1}.png'
            written.append(relative)
            await asyncio.to_thread(write_private, relative, sample['png'])
        async with factory() as session, session.begin():
            if 'recognition_settings' in prepared:
                from app.biz.recognition_policy import lock_recognition_policy
                await lock_recognition_policy(session, device.company_id, prepared['recognition_settings'])
            if enrollment.expires_at <= utcnow():
                raise ApiError(422, 'SESSION_EXPIRED', 'Phiên đăng ký đã hết hạn.')
            current_device=await session.get(Device,device.id)
            actor=await session.scalar(select(UserAccount.id).where(UserAccount.id==enrollment.user_id,UserAccount.status=='ACTIVE',
                select(UserRole.id).where(UserRole.user_id==UserAccount.id,UserRole.role.in_(('OWNER','HR'))).exists()))
            if current_device is None or current_device.status!='ACTIVE' or actor is None:
                raise ApiError(422,'SESSION_EXPIRED','Thiết bị hoặc người đăng ký không còn quyền.')
            employee = await session.scalar(select(Employee).where(Employee.id == employee_id, Employee.company_id == device.company_id).with_for_update())
            if (employee is None or employee.status != 'ACTIVE' or employee.attendance_method != 'FACE'
                    or employee.face_consent_at != enrollment.consent.get(employee_id) or employee.face_consent_by != enrollment.user_id):
                raise ApiError(422, 'SESSION_EXPIRED', 'Đồng ý đăng ký không còn hiệu lực.')
            old_ids = list((await session.scalars(select(FaceProfile.id).where(FaceProfile.employee_id == employee_id, FaceProfile.status == 'PENDING_REVIEW'))).all())
            if old_ids:
                old_paths = list((await session.scalars(select(FaceSample.image_path).where(FaceSample.profile_id.in_(old_ids)))).all())
                await session.execute(delete(FaceProfile).where(FaceProfile.id.in_(old_ids)))
                await session.flush()
            profile = FaceProfile(id=profile_id, company_id=device.company_id, employee_id=employee_id, status='PENDING_REVIEW',
                                  enrolled_by_user_id=enrollment.user_id, enrolled_device_id=device.id,
                                  duplicate_of_employee_id=prepared['duplicate_id'], duplicate_score=prepared['duplicate_score'])
            session.add(profile)
            await session.flush()
            for relative, sample in zip(written, prepared['samples'], strict=True):
                sample_id = uuid4()
                session.add(FaceSample(id=sample_id, profile_id=profile_id, image_path=relative, det_score=sample['det_score'], yaw_ratio=sample['yaw_ratio'], p_live=sample['p_live']))
                await session.flush()
                session.add(FaceEmbedding(sample_id=sample_id, model_id=prepared['model_id'], vector=sample['vector'].tolist()))
            session.add(FaceTemplate(profile_id=profile_id, model_id=prepared['model_id'], vector=prepared['template'].tolist(), n_samples=5))
            session.add(AuditLog(company_id=device.company_id, actor_user_id=enrollment.user_id, actor_device_id=device.id,
                                 action='FACE_ENROLL', entity='face_profile', entity_id=str(profile_id)))
        committed = True
        await asyncio.to_thread(delete_private, old_paths)
        return {'type':'enroll_done','profile_id':str(profile_id),'profile_status':'PENDING_REVIEW','duplicate_warning':prepared['duplicate_id'] is not None}
    except BaseException:
        if not committed:
            await asyncio.to_thread(delete_private, written)
        raise
