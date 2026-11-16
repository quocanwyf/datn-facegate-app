"""Hub CPU thật cho review web T10; DB và file riêng ngoài dữ liệu demo."""
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / '03-app/hub'
os.chdir(HUB)
sys.path.insert(0, str(HUB))
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import get_settings

report = ROOT / '03-app/ket-qua-kiem-thu/2026-11-16_T10'
report.mkdir(parents=True, exist_ok=True)
base = make_url(get_settings().database_url.get_secret_value())
private_root = Path(os.environ['LOCALAPPDATA']) / 'FaceGate'
context_file = private_root / 'T10-test-context.json'
if '--resume' in sys.argv:
    context = json.loads(context_file.read_text())
    database = context['database']
    private = Path(context['data_dir'])
    if not database.startswith('facegate_t10_'):
        raise SystemExit('Context không phải T10.')
else:
    stamp = datetime.now().strftime('%Y%m%d%H%M%S')
    database = 'facegate_t10_' + stamp
    private = private_root / ('T10-' + stamp)
    password = (private_root / 'postgresql16/admin-password.txt').read_text().strip()
    admin = base.set(drivername='postgresql', username='postgres', password=password, database='postgres')
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True, connect_timeout=10) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database), sql.Identifier(base.username)))
    context_file.write_text(json.dumps({'database': database, 'data_dir': str(private)}))
os.environ.update(DATABASE_URL=base.set(database=database).render_as_string(hide_password=False), HUB_DATA_DIR=str(private),
                  HUB_PUBLIC_URL='http://10.0.2.2:8010', PYTHONUTF8='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
get_settings.cache_clear()
if '--resume' not in sys.argv:
    for name, arguments in [('alembic', ['-m', 'alembic', 'upgrade', 'head']), ('seed', ['scripts/seed.py'])]:
        result = subprocess.run([sys.executable, *arguments], capture_output=True, text=True, encoding='utf8')
        (report / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf8')
        if result.returncode:
            raise SystemExit(result.returncode)
print('T10 Hub thật: port 8010, DB mới từ seed; không seed event/ngày công/khuôn mặt.', flush=True)
import uvicorn
from app.main import create_app
uvicorn.run(create_app(), host='127.0.0.1', port=8010)
