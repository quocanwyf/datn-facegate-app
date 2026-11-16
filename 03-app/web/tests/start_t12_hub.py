"""Clone dữ liệu đã đăng ký thật T08 để thử rút consent; giữ nguyên bản gốc.

Cần dừng Hub T08/T11 trước lần tạo clone (Postgres TEMPLATE không cho kết nối
nguồn đang mở). Ảnh/vector được sao chép vào kho riêng ngoài repo, không Git.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / '03-app/hub'
os.chdir(HUB)
sys.path.insert(0, str(HUB))
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import get_settings

private_root = Path(os.environ['LOCALAPPDATA']) / 'FaceGate'
context_file = private_root / 'T12-test-context.json'
base = make_url(get_settings().database_url.get_secret_value())
if '--resume' in sys.argv:
    context = json.loads(context_file.read_text())
else:
    source = json.loads((private_root / 'T08-last-context.json').read_text())
    if not source['database'].startswith('facegate_t08_') or not Path(source['data_dir']).is_relative_to(private_root):
        raise SystemExit('Cần dữ liệu thật T08 trong kho riêng FaceGate.')
    stamp = datetime.now().strftime('%Y%m%d%H%M%S')
    context = {'database': 'facegate_t12_' + stamp, 'data_dir': str(private_root / ('T12-' + stamp))}
    password = (private_root / 'postgresql16/admin-password.txt').read_text().strip()
    admin = base.set(drivername='postgresql', username='postgres', password=password, database='postgres')
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True, connect_timeout=10) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {} OWNER {}').format(
            sql.Identifier(context['database']), sql.Identifier(source['database']), sql.Identifier(base.username)))
    shutil.copytree(source['data_dir'], context['data_dir'])
    context_file.write_text(json.dumps(context))
if not context['database'].startswith('facegate_t12_') or not Path(context['data_dir']).is_relative_to(private_root):
    raise SystemExit('Context phải là clone T12 riêng.')
os.environ.update(DATABASE_URL=base.set(database=context['database']).render_as_string(hide_password=False),
    HUB_DATA_DIR=context['data_dir'], HUB_PUBLIC_URL='http://10.0.2.2:8012', PYTHONUTF8='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
get_settings.cache_clear()
print('T12 CPU Hub port 8012; clone T08 riêng, nguồn T08 giữ nguyên.', flush=True)
from app.main import create_app
import uvicorn
uvicorn.run(create_app(), host='127.0.0.1', port=8012)
