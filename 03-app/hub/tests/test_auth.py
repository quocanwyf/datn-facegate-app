"""T03 tích hợp PostgreSQL thật; mọi thay đổi mỗi test được rollback."""
from datetime import timedelta
import asyncio
import os
from pathlib import Path
from typing import Annotated
import uuid
import httpx
import jwt
import pytest
import pytest_asyncio
from fastapi import Depends
from jsonschema import Draft202012Validator
from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
import yaml
from app.auth.dependencies import Principal, require_roles, department_scope, ensure_department
from app.auth.security import utcnow, token_hash
from app.config import ROOT, get_settings
from app.db.models import AuthRefreshToken, UserAccount, UserRole, Employee, Base
from app.db.session import get_session
from app.main import create_app

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB riêng tạo bởi verify_t03_db.py')]


@pytest_asyncio.fixture
async def runtime():
    engine = create_async_engine(os.environ['T03_TEST_DATABASE_URL'], poolclass=NullPool, hide_parameters=True)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
        async def override():
            async with factory() as session:
                async with session.begin():
                    yield session
        app = create_app()
        app.dependency_overrides[get_session] = override
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            yield client, factory, app
        await transaction.rollback()
    await engine.dispose()


async def login(client, number=1):
    response = await client.post('/api/v1/auth/login', json={'email': f'nv{number:03}@demo.local', 'password': 'Demo@123'})
    assert response.status_code == 200, response.text
    return response.json()


def headers(pair):
    return {'Authorization': 'Bearer ' + pair['access_token']}


def validate(schema, payload):
    source = yaml.safe_load((ROOT / '03-app/openapi/openapi.yaml').read_text(encoding='utf-8'))
    Draft202012Validator({'$ref': '#/components/schemas/' + schema, 'components': source['components']}).validate(payload)


async def test_login_identity_and_contract(runtime):
    client, factory, _ = runtime
    pair = await login(client)
    validate('TokenPair', pair)
    assert pair['expires_in'] == 900 and pair['must_change_password'] is False  # seed demo đã đổi lần đầu
    assert pair['user']['employee']['code'] == 'NV001'
    assert {g['role'] for g in pair['user']['roles']} == {'OWNER', 'EMPLOYEE'}
    me = await client.get('/api/v1/me', headers=headers(pair))
    assert me.status_code == 200
    validate('UserMe', me.json())
    async with factory() as session:
        stored = await session.scalar(select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash(pair['refresh_token'])))
        assert stored and stored.token_hash != pair['refresh_token']
        assert 604790 <= (stored.expires_at - utcnow()).total_seconds() <= 604800


async def test_must_change_password_reflects_database(runtime):
    client, factory, _ = runtime
    async with factory() as session, session.begin():
        await session.execute(update(UserAccount).where(UserAccount.email == 'nv001@demo.local').values(must_change_password=True))
    assert (await login(client))['must_change_password'] is True


async def test_concurrent_refresh_only_one_rotation():
    engine = create_async_engine(os.environ['T03_TEST_DATABASE_URL'], poolclass=NullPool, hide_parameters=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async def override():
        async with factory() as session, session.begin():
            yield session
    app = create_app()
    app.dependency_overrides[get_session] = override
    first = None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            first = await login(client, 24)
            responses = await asyncio.gather(*[client.post('/api/v1/auth/refresh', json={'refresh_token': first['refresh_token']}) for _ in range(2)])
            assert sorted(response.status_code for response in responses) == [200, 401]
    finally:
        if first:
            async with factory() as session, session.begin():
                await session.execute(delete(AuthRefreshToken).where(AuthRefreshToken.user_id == uuid.UUID(first['user']['id'])))
        await engine.dispose()


async def test_wrong_password_and_validation_do_not_leak(runtime):
    client, _, _ = runtime
    response = await client.post('/api/v1/auth/login', json={'email': 'nv001@demo.local', 'password': 'wrong-private-password'})
    assert response.status_code == 401
    validate('Error', response.json())
    assert 'wrong-private-password' not in response.text
    invalid = await client.post('/api/v1/auth/login', json={'email': 'invalid', 'password': 'private'})
    assert invalid.status_code == 400
    assert 'private' not in invalid.text
    assert (await client.get('/api/v1/me')).status_code == 401


async def test_rotation_logout_and_replay(runtime):
    client, _, _ = runtime
    first = await login(client)
    rotated = await client.post('/api/v1/auth/refresh', json={'refresh_token': first['refresh_token']})
    assert rotated.status_code == 200
    second = rotated.json()
    assert second['refresh_token'] != first['refresh_token']
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': first['refresh_token']})).status_code == 401
    assert (await client.get('/api/v1/me', headers={'Authorization': 'Bearer ' + second['refresh_token']})).status_code == 401
    response = await client.post('/api/v1/auth/logout', headers=headers(second), json={'refresh_token': second['refresh_token']})
    assert response.status_code == 204 and not response.content
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': second['refresh_token']})).status_code == 401


async def test_expired_and_database_revoked_tokens(runtime):
    client, factory, _ = runtime
    pair = await login(client)
    claims = {'sub': pair['user']['id'], 'type': 'access', 'iat': utcnow() - timedelta(hours=1), 'exp': utcnow() - timedelta(seconds=1), 'jti': str(uuid.uuid4())}
    expired = jwt.encode(claims, get_settings().jwt_secret.get_secret_value(), algorithm='HS256')
    assert (await client.get('/api/v1/me', headers={'Authorization': 'Bearer ' + expired})).status_code == 401
    async with factory() as session, session.begin():
        await session.execute(update(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash(pair['refresh_token'])).values(expires_at=utcnow() - timedelta(seconds=1)))
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': pair['refresh_token']})).status_code == 401


async def test_change_password_revokes_all_refresh(runtime):
    client, _, _ = runtime
    first, second = await login(client), await login(client)
    response = await client.post('/api/v1/auth/change-password', headers=headers(first), json={'old_password': 'Demo@123', 'new_password': 'NewDemo@456'})
    assert response.status_code == 204
    for pair in (first, second):
        assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': pair['refresh_token']})).status_code == 401
    assert (await client.post('/api/v1/auth/login', json={'email': 'nv001@demo.local', 'password': 'Demo@123'})).status_code == 401
    new = await client.post('/api/v1/auth/login', json={'email': 'nv001@demo.local', 'password': 'NewDemo@456'})
    assert new.status_code == 200 and not new.json()['must_change_password']


@pytest.mark.parametrize('number,role,denied', [(1,'OWNER','HR'), (2,'HR','SECURITY'), (5,'MANAGER','OWNER'), (20,'SECURITY','HR'), (6,'EMPLOYEE','OWNER')])
async def test_role_dependencies_reject_missing_permission(runtime, number, role, denied):
    client, _, app = runtime
    @app.get('/_test/allowed')
    async def allowed(principal: Annotated[Principal, Depends(require_roles(role))]):
        return {'ok': True}
    @app.get('/_test/forbidden')
    async def forbidden(principal: Annotated[Principal, Depends(require_roles(denied))]):
        return {'ok': True}
    pair = await login(client, number)
    assert (await client.get('/_test/allowed', headers=headers(pair))).status_code == 200
    assert (await client.get('/_test/forbidden', headers=headers(pair))).status_code == 403


async def test_roles_and_disabled_account_are_reread(runtime):
    client, factory, app = runtime
    @app.get('/_test/owner')
    async def owner(principal: Annotated[Principal, Depends(require_roles('OWNER'))]):
        return {'ok': True}
    pair = await login(client)
    user_id = uuid.UUID(pair['user']['id'])
    async with factory() as session, session.begin():
        await session.execute(delete(UserRole).where(UserRole.user_id == user_id, UserRole.role == 'OWNER'))
    assert (await client.get('/_test/owner', headers=headers(pair))).status_code == 403
    async with factory() as session, session.begin():
        await session.execute(update(UserAccount).where(UserAccount.id == user_id).values(status='DISABLED'))
    assert (await client.get('/api/v1/me', headers=headers(pair))).status_code == 401
    assert (await client.post('/api/v1/auth/refresh', json={'refresh_token': pair['refresh_token']})).status_code == 401


async def test_manager_scope_and_waiting_in(runtime):
    client, factory, _ = runtime
    pair = await login(client, 5)
    async with factory() as session, session.begin():
        account = await session.get(UserAccount, uuid.UUID(pair['user']['id']))
        roles = list((await session.scalars(select(UserRole).where(UserRole.user_id == account.id))).all())
        principal = Principal(account, roles)
        scope = department_scope(principal)
        assert len(scope) == 1
        ensure_department(principal, account.company_id, next(iter(scope)))
        from app.errors import ApiError
        with pytest.raises(ApiError):
            ensure_department(principal, account.company_id, uuid.uuid4())
        employee = await session.get(Employee, account.employee_id)
        statement = text("INSERT INTO attendance_day(company_id,employee_id,work_date,status,finalized) VALUES (:c,:e,'2099-01-01','WAITING_IN',false)")
        await session.execute(statement, {'c': account.company_id, 'e': employee.id})
        count = await session.scalar(text("SELECT count(*) FROM attendance_day WHERE status='WAITING_IN' AND check_in_at IS NULL AND NOT finalized"))
        assert count == 1
        # Cả hai nhánh vi phạm CHECK phải lỗi, luôn rollback savepoint.
        from sqlalchemy.exc import IntegrityError
        for change in ("finalized=true", "check_in_at=now()"):
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(text('UPDATE attendance_day SET ' + change))


async def test_health_version_cors_and_operation_contract(runtime):
    client, _, app = runtime
    health = await client.get('/api/v1/health')
    assert health.status_code == 200
    validate('Health', health.json())
    assert health.json()['db'] is True and health.json()['model_verified'] is False
    assert health.json()['status'] == 'degraded' and not app.state.recognition_ready
    assert (await client.get('/api/v1/version')).json()['api'] == 'v1'
    trusted = get_settings().cors_origins.split(',')[0].strip()
    assert (await client.get('/api/v1/version', headers={'Origin': trusted})).headers['access-control-allow-origin'] == trusted
    assert 'access-control-allow-origin' not in (await client.get('/api/v1/version', headers={'Origin': 'http://untrusted.invalid'})).headers
    source = yaml.safe_load((ROOT / '03-app/openapi/openapi.yaml').read_text(encoding='utf-8'))
    for path, operations in app.openapi()['paths'].items():
        if path.startswith('/_test'):
            continue
        for method, operation in operations.items():
            assert source['paths'][path.removeprefix('/api/v1')][method]['operationId'] == operation['operationId']
    assert len(Base.metadata.tables) == 23
