import asyncio
from sqlalchemy import select, delete, update
from fastapi.responses import JSONResponse
from app.auth.security import utcnow
from app.biz.files import delete_private
from app.db.models import AuditLog, EventHandling, FaceProfile, FaceSample, RecognitionEvent


async def withdraw_consent(app, session, employee, user_id):
    from app.api.kiosk import employee_view
    runtime = getattr(app.state, 'recognition', None)
    if runtime:
        runtime.paused.set()
    profile_ids = list((await session.scalars(select(FaceProfile.id).where(FaceProfile.employee_id == employee.id))).all())
    paths = list((await session.scalars(select(FaceSample.image_path).where(FaceSample.profile_id.in_(profile_ids)))).all()) if profile_ids else []
    events = (await session.execute(select(RecognitionEvent.id, RecognitionEvent.snapshot_path).join(EventHandling, EventHandling.event_id == RecognitionEvent.id)
                                  .where(EventHandling.linked_employee_id == employee.id, RecognitionEvent.snapshot_path.is_not(None)))).all()
    paths.extend(path for _, path in events)
    employee.face_consent_at = employee.face_consent_by = None
    employee.attendance_method, employee.biometric_deleted_at = 'MANUAL', utcnow()
    session.add(AuditLog(company_id=employee.company_id, actor_user_id=user_id, action='FACE_CONSENT_WITHDRAW', entity='employee', entity_id=str(employee.id)))
    await session.commit()  # Từ đây không được rollback consent để khôi phục quyền nhận dạng.
    if runtime:
        await asyncio.wrap_future(runtime.worker.submit('discard_employee',employee.id))
    deletion_error = False
    try:
        await asyncio.to_thread(delete_private, paths)
    except OSError:
        deletion_error = True
    if not deletion_error:
        async with session.begin():
            if profile_ids:
                await session.execute(delete(FaceProfile).where(FaceProfile.id.in_(profile_ids)))
            if events:
                await session.execute(update(RecognitionEvent).where(RecognitionEvent.id.in_([id for id, _ in events])).values(snapshot_path=None))
    reload_error = False
    if runtime:
        try:
            await app.state.kiosk_service.reload()
        except Exception:
            reload_error = True
    if deletion_error or reload_error:
        return JSONResponse(status_code=503, content={'error':{'code':'BIOMETRIC_DELETE_INCOMPLETE' if deletion_error else 'RECOGNITION_UNAVAILABLE',
                'message':'Chưa xóa xong dữ liệu khuôn mặt. Vui lòng thử lại.' if deletion_error else 'Máy chủ tạm ngưng nhận dạng.'}})
    # session.begin của dependency đã kết thúc bằng commit; dùng transaction riêng cho view.
    async with session.begin():
        return await employee_view(session, employee)
