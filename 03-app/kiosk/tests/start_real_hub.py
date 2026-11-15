"""Hub nghiệm thu Kiosk: DB mới, seed chính thức; đăng ký/nhận dạng do app thật gửi."""
from datetime import datetime
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / '03-app/hub'
os.chdir(HUB)
sys.path.insert(0, str(HUB))
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ['PYTHONUTF8'] = '1'

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import get_settings

parser = argparse.ArgumentParser()
parser.add_argument('--resume', action='store_true', help='Dùng lại DB/dữ liệu của lần chạy gần nhất.')
args = parser.parse_args()
context_file = Path(os.environ['LOCALAPPDATA']) / 'FaceGate/T08-last-context.json'
stamp = datetime.now().strftime('%Y%m%d%H%M%S')
if args.resume:
    context = json.loads(context_file.read_text(encoding='utf8'))
    database = context['database']
    private = Path(context['data_dir'])
    if not database.startswith('facegate_t08_') or not private.is_dir():
        raise SystemExit('Context T08 không hợp lệ; không khởi động.')
else:
    database = 'facegate_t08_' + stamp
    private = Path(os.environ['LOCALAPPDATA']) / 'FaceGate' / ('T08-' + stamp)
    private.mkdir(parents=True)
report = ROOT / '03-app/ket-qua-kiem-thu/2026-11-15_T08'
report.mkdir(parents=True, exist_ok=True)
base = make_url(get_settings().database_url.get_secret_value())
password = (Path(os.environ['LOCALAPPDATA']) / 'FaceGate/postgresql16/admin-password.txt').read_text().strip()
admin = base.set(drivername='postgresql', database='postgres', username='postgres', password=password).render_as_string(hide_password=False)
if not args.resume:
    with psycopg.connect(admin, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database), sql.Identifier(base.username)))
os.environ.update(DATABASE_URL=base.set(database=database).render_as_string(hide_password=False), HUB_DATA_DIR=str(private), HUB_PUBLIC_URL='http://10.0.2.2:8000')
get_settings.cache_clear()
for name, command in ([] if args.resume else [('alembic', [sys.executable, '-m', 'alembic', 'upgrade', 'head']), ('seed', [sys.executable, 'scripts/seed.py'])]):
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf8')
    (report / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf8')
    if result.returncode:
        raise RuntimeError(name + ' thất bại; xem log, không tiếp tục.')
(private / 'test-context.json').write_text(json.dumps({'database': database, 'data_dir': str(private)}, indent=2), encoding='utf8')
context_file.write_text(json.dumps({'database': database, 'data_dir': str(private)}, indent=2), encoding='utf8')
print('T08_READY port=8000 database=' + database, flush=True)
print('Private test context: ' + str(private / 'test-context.json'), flush=True)
import uvicorn
from app.main import create_app
uvicorn.run(create_app(), host='127.0.0.1', port=8000, proxy_headers=False)
