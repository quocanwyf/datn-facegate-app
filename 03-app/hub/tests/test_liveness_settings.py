"""Fixture phê duyệt chỉ ở tmp_path; không dùng làm marker triển khai thật."""
from datetime import datetime, timezone
import json
import os
from types import SimpleNamespace
import pytest
from app.recog.liveness import POLICY_FIELDS, bundle_id
from app.biz.recognition_policy import lock_recognition_policy
from app.db.models import Company
from app.errors import ApiError
from sqlalchemy import select
from test_auth import runtime
from test_admin_api import auth

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB test riêng')]


async def test_enable_requires_matching_approval_and_failed_change_preserves_all_settings(runtime, tmp_path, monkeypatch):
    client, factory, _ = runtime
    monkeypatch.setattr('app.api.settings.get_settings', lambda: SimpleNamespace(hub_data_dir=tmp_path))
    monkeypatch.setattr('app.biz.recognition_policy.get_settings', lambda: SimpleNamespace(hub_data_dir=tmp_path))
    headers = await auth(factory, 1)
    before = (await client.get('/api/v1/settings/recognition', headers=headers)).json()
    enabled = {'anti_spoof_enabled': True, 'liveness_threshold': .7}
    assert (await client.put('/api/v1/settings/recognition', headers=headers, json=enabled)).status_code == 422
    policy = {key: before[key] for key in POLICY_FIELDS}
    marker = dict(threshold=.7, bundle_id=bundle_id(), policy=policy, approved_by='fixture',
        approved_at=datetime.now(timezone.utc).isoformat(), trial_counts={group: 2 for group in ('live','print','phone','replay')}, calibration_sha256='0'*64)
    (tmp_path/'liveness-approved.json').write_text(json.dumps(marker))
    response = await client.put('/api/v1/settings/recognition', headers=headers, json=enabled)
    assert response.status_code == 200, response.text
    assert response.json()['anti_spoof_enabled'] is True
    valid = response.json()
    async with factory() as session, session.begin():
        company = await session.scalar(select(Company))
        with pytest.raises(ApiError, match='Cấu hình vừa thay đổi'):
            await lock_recognition_policy(session, company.id, before)
        assert await lock_recognition_policy(session, company.id, valid) is None
    for invalid in ({'liveness_threshold': .8}, {'jpeg_quality': 70}, {'window_size': 0}, {'spoof_min': 0}):
        assert (await client.put('/api/v1/settings/recognition', headers=headers, json=invalid)).status_code == 422
        assert (await client.get('/api/v1/settings/recognition', headers=headers)).json() == valid
    (tmp_path/'liveness-approved.json').unlink()
    assert (await client.put('/api/v1/settings/recognition', headers=headers, json={'anti_spoof_enabled': False})).status_code == 200
