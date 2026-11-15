"""Tạo lời mời bằng REST thật; Kiosk tự ghép/chụp, không tạo hồ sơ hay sự kiện giả."""
import json
import os
from pathlib import Path
import httpx

private_root = Path(os.environ['LOCALAPPDATA']) / 'FaceGate'
context = json.loads((private_root / 'T08-last-context.json').read_text(encoding='utf8'))
if not context['database'].startswith('facegate_t08_'):
    raise SystemExit('Chỉ dùng DB nghiệm thu T08.')
with httpx.Client(base_url='http://127.0.0.1:8000/api/v1', timeout=20) as client:
    health = client.get('/health'); health.raise_for_status()
    assert health.json()['model_verified'], 'Checkpoint chưa hợp lệ.'
    login = client.post('/auth/login', json={'email': 'nv001@demo.local', 'password': 'Demo@123'})
    login.raise_for_status()
    client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
    gates = client.get('/gates'); gates.raise_for_status()
    gate = next((item for item in gates.json() if item['name'] == 'T08 review'), None)
    if gate is None:
        response = client.post('/gates', json={'name': 'T08 review', 'mode': 'ACCESS_ONLY', 'default_policy': 'ALLOW_ALL_ACTIVE', 'threshold_level': 'DEFAULT_VAL'})
        response.raise_for_status(); gate = response.json()
    invitation = client.post('/devices', json={'gate_id': gate['id'], 'name': 'T08 native Android'})
    invitation.raise_for_status()
    destination = Path(context['data_dir']) / 'native-review-context.json'
    destination.write_text(json.dumps({'gate_id': gate['id'], **invitation.json()}, ensure_ascii=False, indent=2), encoding='utf8')
    print('Lời mời tạo bằng REST thật; mã chỉ lưu riêng ngoài repo: ' + str(destination))
    print('Chưa ghép/chụp/duyệt hồ sơ; thực hiện các bước đó trên Kiosk và web.')
