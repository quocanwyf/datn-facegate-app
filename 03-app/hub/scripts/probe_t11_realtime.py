"""kiosk_sim từ ảnh thật ngoài Git; không tự chèn event hoặc vector."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import httpx
from kiosk_sim import simulate

parser = argparse.ArgumentParser()
parser.add_argument('kind', choices=['known', 'unknown', 'suspended'])
parser.add_argument('photos', type=Path)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[3]
if args.photos.resolve().is_relative_to(ROOT):
    raise SystemExit('Ảnh thật phải nằm ngoài repo.')
async def main():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000/api/v1', timeout=30) as client:
        login = await client.post('/auth/login', json={'email': 'nv001@demo.local', 'password': 'Demo@123'})
        login.raise_for_status()
        client.headers['Authorization'] = 'Bearer '+login.json()['access_token']
        health = (await client.get('/health')).json()
        if not health['model_verified'] or health['gallery_size'] < 1:
            raise SystemExit('Cần gallery thật đã duyệt ở T08.')
        gates = (await client.get('/gates')).json()
        gate = next(row for row in gates if row['name'] == 'T08 review')
        invitation = await client.post('/devices', json={'gate_id': gate['id'], 'name': 'T11 kiosk_sim ảnh được đồng ý'})
        invitation.raise_for_status()
        paired = await client.post('/kiosk/pair', json={'code': invitation.json()['pairing_code']})
        paired.raise_for_status()
        token = paired.json()['device_token']
        employee = next(row for row in (await client.get('/employees', params={'q': 'NV006'})).json()['items'] if row['code'] == 'NV006')
        suspended = False
        try:
            if args.kind == 'suspended':
                (await client.post(f'/employees/{employee["id"]}/suspend')).raise_for_status()
                suspended = True
            messages = await simulate('http://127.0.0.1:8000', token, args.photos, repeat=2, limit=17)
            expected = ('DENY', 'INACTIVE') if suspended else ('DENY', 'UNKNOWN') if args.kind == 'unknown' else ('OK', None)
            assert any(row.get('type') == 'result' and row.get('result') == expected[0] and (expected[1] is None or row.get('reason') == expected[1]) for row in messages), 'Chưa có kết quả mong đợi từ ảnh thật.'
            print('PASS actual kiosk_sim '+args.kind)
        finally:
            if suspended:
                (await client.post(f'/employees/{employee["id"]}/reactivate')).raise_for_status()
            (await client.post(f'/devices/{invitation.json()["device"]["id"]}/revoke')).raise_for_status()
asyncio.run(main())
