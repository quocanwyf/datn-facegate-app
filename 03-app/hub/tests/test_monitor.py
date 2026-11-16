"""WS/DB thật trong DB kiểm riêng; manual event sinh từ API, không giả quét AI."""
from datetime import timedelta
import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.auth.security import utcnow
from app.config import get_settings
from app.db.session import get_session
from app.main import create_app

pytestmark = pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB kiểm T11 riêng')


@pytest.fixture
def monitor_client():
    engine = create_async_engine(os.environ['T03_TEST_DATABASE_URL'], poolclass=NullPool, hide_parameters=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app = create_app(attendance_factory=None, monitor_factory=factory)
    # Test quyền/giao thức không tải model hoặc giả kết quả nhận dạng.
    app.state.kiosk_service = SimpleNamespace()
    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as client:
        yield client, app
    asyncio.run(engine.dispose())


def login(client, email='nv001@demo.local'):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Demo@123'})
    assert response.status_code == 200
    pair = response.json()
    return pair, {'Authorization': 'Bearer '+pair['access_token']}


@pytest.mark.parametrize('first', [{'type': 'ping'}, {'type': 'auth'}, {'type': 'auth', 'access_token': 'invalid'}])
def test_monitor_rejects_invalid_first_message(monitor_client, first):
    client, _ = monitor_client
    with client.websocket_connect('/api/v1/ws/monitor') as socket:
        socket.send_json(first)
        assert socket.receive_json()['type'] == 'error'
        assert socket.receive()['code'] == 4401


def test_monitor_owner_receives_event_after_manual_api_commit(monitor_client):
    client, _ = monitor_client
    pair, headers = login(client)
    gate = client.get('/api/v1/gates', headers=headers).json()[0]
    with client.websocket_connect('/api/v1/ws/monitor') as socket:
        socket.send_json({'type': 'auth', 'access_token': pair['access_token']})
        first = socket.receive_json()
        assert first['type'] == 'counters'
        opened = client.post(f'/api/v1/gates/{gate["id"]}/manual-open', headers=headers, json={'reason': 'API manual thật trong DB kiểm T11'})
        assert opened.status_code == 201
        event = socket.receive_json()
        assert event['type'] == 'event' and event['id'] == opened.json()['id'] and event['result'] == 'MANUAL_OPEN'


def test_monitor_manager_only_receives_team_event(monitor_client):
    client, app = monitor_client
    _, owner = login(client)
    employees = client.get('/api/v1/employees', headers=owner, params={'attendance_method': 'MANUAL', 'size': 100}).json()['items']
    target = next(row for row in employees if row['code'] == 'NV022')
    users = client.get('/api/v1/users', headers=owner, params={'size': 100}).json()['items']
    manager = next(row for row in users if any(role['role'] == 'MANAGER' and role['scope_department_id'] == target['department_id'] for role in row['roles']))
    pair, _ = login(client, manager['email'])
    gate = next(row for row in client.get('/api/v1/gates', headers=owner).json() if row['mode'] == 'ATTENDANCE_ACCESS')
    with client.websocket_connect('/api/v1/ws/monitor') as socket:
        socket.send_json({'type': 'auth', 'access_token': pair['access_token']})
        async def authenticated():
            for _ in range(200):
                if app.state.monitor.queues:
                    return
                await asyncio.sleep(.01)
            raise AssertionError('Monitor chưa xác thực.')
        client.portal.call(authenticated)
        outside = client.post(f'/api/v1/gates/{gate["id"]}/manual-open', headers=owner, json={'reason': 'Không thuộc team vì không có NV'})
        assert outside.status_code == 201
        inside = client.post('/api/v1/attendance/manual', headers=owner, json={'gate_id': gate['id'], 'employee_id': target['id'], 'reason': 'Chấm hộ thật qua API DB kiểm'})
        assert inside.status_code == 201, inside.text
        event = socket.receive_json()
        assert event['type'] == 'event' and event['id'] == inside.json()['id']
        assert event['employee']['id'] == target['id']


def test_monitor_employee_forbidden_and_access_token_expires(monitor_client):
    client, _ = monitor_client
    employee, _ = login(client, 'nv006@demo.local')
    with client.websocket_connect('/api/v1/ws/monitor') as socket:
        socket.send_json({'type': 'auth', 'access_token': employee['access_token']})
        assert socket.receive_json()['code'] == 'FORBIDDEN'
        assert socket.receive()['code'] == 4403
    owner, _ = login(client)
    now = utcnow()
    token = jwt.encode({'sub': owner['user']['id'], 'type': 'access', 'jti': str(uuid4()), 'iat': now,
                        'exp': now+timedelta(seconds=2)}, get_settings().jwt_secret.get_secret_value(), algorithm='HS256')
    with client.websocket_connect('/api/v1/ws/monitor') as socket:
        socket.send_json({'type': 'auth', 'access_token': token})
        assert socket.receive_json()['type'] == 'counters'
        assert socket.receive_json()['code'] == 'TOKEN_EXPIRED'
        assert socket.receive()['code'] == 4401
