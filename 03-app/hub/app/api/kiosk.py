from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.auth.dependencies import Database
from app.auth.device import CurrentDevice
from app.auth.security import utcnow, verify_password
from app.db.models import Department, Employee, FaceProfile, UserAccount, UserRole
from app.errors import ApiError

router = APIRouter(prefix='/api/v1/kiosk', tags=['Kiosk'])


class SessionCreate(BaseModel):
    user_id: UUID
    pin: str = Field(pattern=r'^\d{4}$')


class ConsentInput(BaseModel):
    employee_id: UUID
    agree: bool


async def enroller(session, user_id, company_id, *, lock=False):
    query = select(UserAccount).where(UserAccount.id == user_id, UserAccount.company_id == company_id, UserAccount.status == 'ACTIVE',
            UserAccount.kiosk_pin_hash.is_not(None), select(UserRole.id).where(UserRole.user_id == UserAccount.id, UserRole.role.in_(('OWNER','HR'))).exists())
    return await session.scalar(query.with_for_update() if lock else query)


async def employee_view(session, employee):
    department = await session.get(Department, employee.department_id)
    status = await session.scalar(select(FaceProfile.status).where(FaceProfile.employee_id == employee.id).order_by(FaceProfile.created_at.desc()).limit(1))
    return {'id': str(employee.id), 'code': employee.code, 'full_name': employee.full_name, 'department_name': department.name,
            'attendance_method': employee.attendance_method, 'face_profile_status': status}


@router.get('/enrollers', operation_id='getKioskEnrollers')
async def list_enrollers(session: Database, device: CurrentDevice) -> list[dict]:
    accounts = (await session.scalars(select(UserAccount).where(UserAccount.company_id == device.company_id, UserAccount.status == 'ACTIVE',
                    UserAccount.kiosk_pin_hash.is_not(None), select(UserRole.id).where(UserRole.user_id == UserAccount.id,
                    UserRole.role.in_(('OWNER','HR'))).exists()).order_by(UserAccount.id))).all()
    result = []
    for account in accounts:
        employee = await session.get(Employee, account.employee_id) if account.employee_id else None
        result.append({'user_id': str(account.id), 'name': employee.full_name if employee else 'Người đăng ký'})
    return result


@router.post('/enroll/sessions', status_code=201, operation_id='postKioskEnrollSessions', response_model=None)
async def create_session(body: SessionCreate, session: Database, device: CurrentDevice, request: Request):
    account = await enroller(session, body.user_id, device.company_id, lock=True)
    if account is None:
        raise ApiError(403, 'PIN_INVALID', 'Người đăng ký không khả dụng.')
    now = utcnow()
    if account.pin_locked_until and account.pin_locked_until > now:
        raise ApiError(429, 'PIN_LOCKED', 'PIN đang bị khóa. Vui lòng thử lại sau 15 phút.')
    if account.pin_locked_until:
        account.pin_failed_count, account.pin_locked_until = 0, None
    if not await run_in_threadpool(verify_password, account.kiosk_pin_hash, body.pin):
        account.pin_failed_count += 1
        locked = account.pin_failed_count >= 5
        if locked:
            account.pin_locked_until = now + timedelta(minutes=15)
        # Trả Response để transaction commit bộ đếm, không raise rồi rollback lỗi PIN.
        return JSONResponse(status_code=429 if locked else 403, content={'error': {
            'code': 'PIN_LOCKED' if locked else 'PIN_INVALID',
            'message': 'PIN bị khóa trong 15 phút.' if locked else 'PIN không đúng.',
            'details': {'remaining': max(0, 5 - account.pin_failed_count)}}})
    account.pin_failed_count, account.pin_locked_until = 0, None
    enrollment = request.app.state.enroll_sessions.create(device, account.id)
    employee = await session.get(Employee, account.employee_id) if account.employee_id else None
    return {'enroll_session_id': str(enrollment.id), 'expires_at': enrollment.expires_at,
            'enroller_name': employee.full_name if employee else 'Người đăng ký'}


async def checked_session(request, session, id, device):
    enrollment = request.app.state.enroll_sessions.get(id, device.id)
    if await enroller(session, enrollment.user_id, device.company_id) is None:
        raise ApiError(422, 'SESSION_EXPIRED', 'Người đăng ký không còn quyền. Vui lòng nhập PIN lại.')
    return enrollment


@router.get('/enroll/sessions/{id}/employees', operation_id='getKioskEnrollSessionsEmployees')
async def list_employees(id: UUID, session: Database, device: CurrentDevice, request: Request, q: str | None = None) -> list[dict]:
    await checked_session(request, session, id, device)
    query = select(Employee).where(Employee.company_id == device.company_id, Employee.status == 'ACTIVE')
    if q:
        query = query.where(Employee.full_name.ilike('%' + q + '%') | Employee.code.ilike('%' + q + '%'))
    employees = (await session.scalars(query.order_by(Employee.code))).all()
    return [await employee_view(session, employee) for employee in employees]


@router.post('/enroll/sessions/{id}/consent', operation_id='postKioskEnrollSessionsConsent', response_model=None)
async def consent(id: UUID, body: ConsentInput, session: Database, device: CurrentDevice, request: Request):
    enrollment = await checked_session(request, session, id, device)
    employee = await session.scalar(select(Employee).where(Employee.id == body.employee_id, Employee.company_id == device.company_id,
                                                       Employee.status == 'ACTIVE').with_for_update())
    if employee is None:
        raise ApiError(404, 'HTTP_404', 'Không tìm thấy nhân viên đang hoạt động.')
    if body.agree:
        employee.face_consent_at, employee.face_consent_by = utcnow(), enrollment.user_id
        employee.attendance_method = 'FACE'
        enrollment.consent[employee.id] = employee.face_consent_at
        await session.flush()
        return await employee_view(session, employee)
    enrollment.consent.pop(employee.id, None)
    from app.biz.face_data import withdraw_consent
    return await withdraw_consent(request.app, session, employee, enrollment.user_id)
