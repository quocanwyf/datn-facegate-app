from dataclasses import dataclass
from typing import Annotated
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import decode_token
from app.db.models import UserAccount, UserRole
from app.db.session import get_session
from app.errors import ApiError

Database = Annotated[AsyncSession, Depends(get_session, scope='function')]
bearer = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    account: UserAccount
    roles: list[UserRole]


async def current_user(session: Database, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Principal:
    if credentials is None:
        raise ApiError(401, 'UNAUTHORIZED', 'Vui lòng đăng nhập.')
    user_id = decode_token(credentials.credentials, 'access')
    account = await session.get(UserAccount, user_id)
    if account is None or account.status != 'ACTIVE':
        raise ApiError(401, 'UNAUTHORIZED', 'Tài khoản không khả dụng.')
    roles = list((await session.scalars(select(UserRole).where(UserRole.user_id == user_id))).all())
    return Principal(account, roles)


CurrentUser = Annotated[Principal, Depends(current_user)]


def require_roles(*allowed: str):
    async def dependency(principal: CurrentUser) -> Principal:
        if not any(grant.role in allowed for grant in principal.roles):
            raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền thực hiện thao tác này.')
        return principal
    return dependency


def department_scope(principal: Principal) -> set[UUID] | None:
    # None là toàn công ty; tập rỗng không được xem team nào.
    if any(grant.role in ('OWNER', 'HR') for grant in principal.roles):
        return None
    return {grant.scope_department_id for grant in principal.roles if grant.role == 'MANAGER'}


def ensure_department(principal: Principal, company_id: UUID, department_id: UUID):
    scopes = department_scope(principal)
    if company_id != principal.account.company_id or (scopes is not None and department_id not in scopes):
        raise ApiError(403, 'FORBIDDEN', 'Bạn không có quyền truy cập phòng ban này.')
