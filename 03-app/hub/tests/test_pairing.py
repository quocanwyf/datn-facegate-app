import asyncio
from datetime import timedelta
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, update
from app.auth.pairing import PairingAttempts
from app.auth.security import token_hash, utcnow
from app.db.models import Device, Gate
from app.errors import ApiError
from test_auth import runtime, login, headers, validate


def test_ip_lock_exact_expiry_and_isolation():
    now = [100.0]
    attempts = PairingAttempts(clock=lambda: now[0])
    for expected in (404, 404, 404, 404, 429):
        with pytest.raises(ApiError) as caught:
            attempts.failed('192.0.2.1')
        assert caught.value.status == expected
    attempts.check('192.0.2.2')
    for time in (100, 699.999):
        now[0] = time
        with pytest.raises(ApiError) as caught:
            attempts.check('192.0.2.1')
        assert caught.value.code == 'PAIRING_LOCKED'
    now[0] = 700
    attempts.check('192.0.2.1')
    with pytest.raises(ApiError) as caught:
        attempts.failed('192.0.2.1')
    assert caught.value.status == 404
    attempts.succeeded('192.0.2.1')
    for _ in range(4):
        with pytest.raises(ApiError) as caught:
            attempts.failed('192.0.2.1')
        assert caught.value.status == 404


def test_failures_are_atomic_without_extending_lock():
    now = [0.0]
    attempts = PairingAttempts(clock=lambda: now[0])
    def wrong(_):
        try:
            attempts.failed('192.0.2.1')
        except ApiError as error:
            return error.status
    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(pool.map(wrong, range(20)))
    assert statuses.count(404) == 4 and statuses.count(429) == 16
    now[0] = 600
    attempts.check('192.0.2.1')


integration = pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB kiểm thử PostgreSQL riêng')


async def provision(client, factory):
    pair = await login(client)
    async with factory() as session:
        gate = await session.scalar(select(Gate).order_by(Gate.name))
    response = await client.post('/api/v1/devices', headers=headers(pair), json={'gate_id': str(gate.id), 'name': 'Tablet kiểm thử T05'})
    assert response.status_code == 201, response.text
    validate('DevicePairing', response.json())
    return pair, response.json()


@integration
@pytest.mark.asyncio
async def test_pair_token_hash_expiry_and_revoke(runtime):
    client, factory, app = runtime
    owner, invitation = await provision(client, factory)
    assert len(invitation['pairing_code']) == 6
    assert json.loads(invitation['qr_payload'])['code'] == invitation['pairing_code']
    response = await client.post('/api/v1/kiosk/pair', json={'code': invitation['pairing_code'], 'device_info': {'app_version': 'test'}})
    assert response.status_code == 200, response.text
    paired = response.json()
    validate('PairResponse', paired)
    async with factory() as session:
        device = await session.get(Device, uuid.UUID(paired['device_id']))
        assert device.status == 'ACTIVE'
        assert device.token_hash == token_hash(paired['device_token']) and device.token_hash != paired['device_token']
        assert 2591990 <= (device.token_expires_at - utcnow()).total_seconds() <= 2592000
        assert device.pairing_attempts == 0  # không gán lỗi IP cho một mã đích
    second = await client.post('/api/v1/kiosk/pair', json={'code': invitation['pairing_code']})
    assert second.status_code == 404
    revoked = await client.post('/api/v1/devices/' + paired['device_id'] + '/revoke', headers=headers(owner))
    assert revoked.status_code == 200 and revoked.json()['status'] == 'REVOKED'
    from app.auth.device import find_device
    async with factory() as session:
        with pytest.raises(ApiError) as caught:
            await find_device(session, paired['device_token'])
        assert caught.value.code == 'DEVICE_REVOKED'


@integration
@pytest.mark.asyncio
async def test_wrong_code_locks_ip_not_device_and_recovers(runtime):
    client, factory, app = runtime
    _, invitation = await provision(client, factory)
    invalid = '000000' if invitation['pairing_code'] != '000000' else '000001'
    clock = [0.0]
    app.state.pairing_attempts = PairingAttempts(clock=lambda: clock[0])
    for status in (404, 404, 404, 404, 429):
        result = await client.post('/api/v1/kiosk/pair', json={'code': invalid})
        assert result.status_code == status
    assert 'máy này' in result.json()['error']['message']
    blocked = await client.post('/api/v1/kiosk/pair', json={'code': invitation['pairing_code']}, headers={'X-Forwarded-For': '192.0.2.99'})
    assert blocked.status_code == 429
    async with factory() as session:
        device = await session.get(Device, uuid.UUID(invitation['device']['id']))
        assert device.status == 'PENDING' and device.pairing_attempts == 0
    clock[0] = 600
    result = await client.post('/api/v1/kiosk/pair', json={'code': invitation['pairing_code']})
    assert result.status_code == 200


@integration
@pytest.mark.asyncio
async def test_expired_code_and_owner_permissions(runtime):
    client, factory, _ = runtime
    _, invitation = await provision(client, factory)
    async with factory() as session, session.begin():
        await session.execute(update(Device).where(Device.id == uuid.UUID(invitation['device']['id'])).values(pairing_expires_at=utcnow() - timedelta(seconds=1)))
    expired = await client.post('/api/v1/kiosk/pair', json={'code': invitation['pairing_code']})
    assert expired.status_code == 422 and expired.json()['error']['code'] == 'PAIRING_EXPIRED'
    hr = await login(client, 2)
    assert (await client.get('/api/v1/devices', headers=headers(hr))).status_code == 403
    assert (await client.post('/api/v1/devices', headers=headers(hr), json={'name':'x','gate_id':invitation['device']['gate_id']})).status_code == 403
    malformed = await client.post('/api/v1/kiosk/pair', json={'code':'123'})
    assert malformed.status_code == 400
