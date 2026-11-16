"""T12: đối chiếu API với PostgreSQL; fixture 0/1/2 event được rollback.

Không dùng dữ liệu này làm bằng chứng quét người thật. Dùng pytest với
PYTHONPATH=hub;hub/tests và T03_TEST_DATABASE_URL trỏ DB test riêng.
"""
import os
from datetime import datetime
import pytest
from sqlalchemy import select
from app.db.models import AttendanceDay
from app.biz.attendance import recompute_day
import app.api.attendance as attendance_api
from test_attendance_api import setup, add_event, at, DAY
from test_admin_api import auth
from test_auth import runtime, validate

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(not os.environ.get('T03_TEST_DATABASE_URL'), reason='Cần DB test riêng')]


@pytest.mark.parametrize('times,status', [([], 'WAITING_IN'), (['08:41'], 'IN_PROGRESS'), (['08:41', '17:30'], 'IN_PROGRESS')])
async def test_today_matches_db_for_zero_one_two_events(runtime, monkeypatch, times, status):
    client, factory, _ = runtime
    monkeypatch.setattr(attendance_api, 'utcnow', lambda: at('18:00'))
    async with factory() as session, session.begin():
        employee, owner, gate, _ = await setup(session)
        for value in times:
            await add_event(session, employee, owner, gate, value)
        day = await recompute_day(session, employee.id, DAY, now=at('18:00'))
        day_id = day.id
    response = await client.get('/api/v1/me/today', headers=await auth(factory, 6))
    assert response.status_code == 200
    payload = response.json()
    validate('MeToday', payload)
    async with factory() as session:
        stored = await session.get(AttendanceDay, day_id)
        assert payload['day']['id'] == str(stored.id)
        assert payload['day']['status'] == stored.status == status
        assert payload['day']['finalized'] is stored.finalized is False
        for field in ('check_in_at', 'check_out_at'):
            actual = payload['day'][field]
            assert (datetime.fromisoformat(actual) if actual else None) == getattr(stored, field)
        assert payload['day']['late_min'] == stored.late_min
        assert payload['day']['worked_min'] == stored.worked_min
    assert len(payload['passes']) == len(times)
