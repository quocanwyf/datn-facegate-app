from fastapi import APIRouter, Response
from sqlalchemy import func, select, update
from starlette.concurrency import run_in_threadpool
from app.api.schemas import ChangePassword, EmployeeBrief, LoginRequest, RefreshRequest, RoleGrant, TokenPair, UserMe
from app.auth.dependencies import CurrentUser, Database
from app.auth.security import ACCESS_SECONDS, decode_token, encode_token, password_hasher, token_hash, utcnow, verify_password
from app.db.models import AuthRefreshToken, Department, Employee, UserAccount, UserRole
from app.errors import ApiError

router = APIRouter(prefix='/api/v1/auth', tags=['Auth'])
me_router = APIRouter(prefix='/api/v1', tags=['Me'])


async def user_view(session, account) -> UserMe:
    grants = (await session.scalars(select(UserRole).where(UserRole.user_id == account.id).order_by(UserRole.role))).all()
    employee = None
    if account.employee_id:
        row = (await session.execute(select(Employee, Department.name).join(Department, Department.id == Employee.department_id)
                                   .where(Employee.id == account.employee_id, Employee.company_id == account.company_id))).first()
        if row:
            item, department_name = row
            employee = EmployeeBrief(id=item.id, code=item.code, full_name=item.full_name,
                                     department_id=item.department_id, department_name=department_name)
    return UserMe(id=account.id, email=account.email, roles=[RoleGrant(role=g.role, scope_department_id=g.scope_department_id) for g in grants], employee=employee)


async def issue_pair(session, account) -> TokenPair:
    access, _ = encode_token(account.id, 'access')
    refresh, expires = encode_token(account.id, 'refresh')
    session.add(AuthRefreshToken(user_id=account.id, token_hash=token_hash(refresh), expires_at=expires))
    await session.flush()
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=ACCESS_SECONDS,
                     must_change_password=account.must_change_password, user=await user_view(session, account))


@router.post('/login', operation_id='postAuthLogin')
async def login(body: LoginRequest, session: Database) -> TokenPair:
    account = await session.scalar(select(UserAccount).where(func.lower(UserAccount.email) == str(body.email).lower()).with_for_update())
    if account is None or account.status != 'ACTIVE' or not await run_in_threadpool(verify_password, account.password_hash, body.password):
        raise ApiError(401, 'UNAUTHORIZED', 'Email hoặc mật khẩu không đúng.')
    account.last_login_at = utcnow()
    return await issue_pair(session, account)


@router.post('/refresh', operation_id='postAuthRefresh')
async def refresh(body: RefreshRequest, session: Database) -> TokenPair:
    user_id = decode_token(body.refresh_token, 'refresh')
    # Khóa cùng thứ tự với đổi mật khẩu, ngăn cấp token sau khi đã thu hồi.
    account = await session.scalar(select(UserAccount).where(UserAccount.id == user_id).with_for_update())
    stored = await session.scalar(select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash(body.refresh_token),
                                                                 AuthRefreshToken.user_id == user_id).with_for_update())
    if account is None or account.status != 'ACTIVE' or stored is None or stored.revoked_at or stored.expires_at <= utcnow():
        raise ApiError(401, 'UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.')
    stored.revoked_at = utcnow()
    return await issue_pair(session, account)


@router.post('/logout', operation_id='postAuthLogout', status_code=204)
async def logout(body: RefreshRequest, session: Database, principal: CurrentUser) -> Response:
    user_id = decode_token(body.refresh_token, 'refresh')
    if user_id != principal.account.id:
        raise ApiError(401, 'UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ.')
    await session.execute(update(AuthRefreshToken).where(AuthRefreshToken.user_id == user_id,
                          AuthRefreshToken.token_hash == token_hash(body.refresh_token), AuthRefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    return Response(status_code=204)


@router.post('/change-password', operation_id='postAuthChangePassword', status_code=204)
async def change_password(body: ChangePassword, session: Database, principal: CurrentUser) -> Response:
    account = await session.scalar(select(UserAccount).where(UserAccount.id == principal.account.id).with_for_update().execution_options(populate_existing=True))
    if not await run_in_threadpool(verify_password, account.password_hash, body.old_password):
        raise ApiError(400, 'VALIDATION_ERROR', 'Mật khẩu hiện tại không đúng.')
    account.password_hash = await run_in_threadpool(password_hasher.hash, body.new_password)
    account.must_change_password = False
    await session.execute(update(AuthRefreshToken).where(AuthRefreshToken.user_id == account.id, AuthRefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    return Response(status_code=204)


@me_router.get('/me', operation_id='getMe')
async def me(session: Database, principal: CurrentUser) -> UserMe:
    return await user_view(session, principal.account)
