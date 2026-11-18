import os
import pytest
from app.biz.recognition_policy import lock_recognition_policy
from app.db.models import Company
from app.errors import ApiError
from sqlalchemy import select
from test_auth import runtime
from test_admin_api import auth

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB test riêng')]


async def test_owner_can_enable_liveness_and_invalid_change_preserves_settings(runtime):
    client, factory, _ = runtime
    headers = await auth(factory, 1)
    before = (await client.get('/api/v1/settings/recognition', headers=headers)).json()
    enabled = {'anti_spoof_enabled': True, 'liveness_threshold': 0.5}
    response = await client.put('/api/v1/settings/recognition', headers=headers, json=enabled)
    assert response.status_code == 200, response.text
    assert response.json()['anti_spoof_enabled'] is True
    valid = response.json()
    assert valid['liveness_threshold'] == 0.5
    async with factory() as session, session.begin():
        company = await session.scalar(select(Company))
        with pytest.raises(ApiError, match='Cấu hình vừa thay đổi'):
            await lock_recognition_policy(session, company.id, before)
        assert await lock_recognition_policy(session, company.id, valid) is None
    for invalid in ({'liveness_threshold': -0.1}, {'liveness_threshold': 1.1}, {'liveness_threshold': None}, {'window_size': 0}, {'spoof_min': 0}):
        assert (await client.put('/api/v1/settings/recognition', headers=headers, json=invalid)).status_code == 422
        assert (await client.get('/api/v1/settings/recognition', headers=headers)).json() == valid
    assert (await client.put('/api/v1/settings/recognition', headers=headers, json={'anti_spoof_enabled': False})).status_code == 200
