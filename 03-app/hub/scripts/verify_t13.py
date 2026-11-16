"""T13: DB test riêng, kiểm liveness/approval; không tạo marker triển khai hay dữ liệu hiệu chỉnh giả."""
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB))
from app.config import ROOT, get_settings

report = ROOT / '03-app/ket-qua-kiem-thu/2026-11-16_T13'
report.mkdir(parents=True, exist_ok=True)
private = Path(os.environ['LOCALAPPDATA']) / 'FaceGate/T13-test-context.json'
base = make_url(get_settings().database_url.get_secret_value())
if '--resume' in sys.argv:
    database = json.loads(private.read_text())['database']
    if not database.startswith('facegate_t13_'):
        raise SystemExit('DB không phải DB kiểm thử T13.')
else:
    database = 'facegate_t13_' + datetime.now().strftime('%Y%m%d%H%M%S')
    password = (Path(os.environ['LOCALAPPDATA']) / 'FaceGate/postgresql16/admin-password.txt').read_text().strip()
    admin = base.set(drivername='postgresql', database='postgres', username='postgres', password=password)
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True, connect_timeout=10) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database), sql.Identifier(base.username)))
    private.write_text(json.dumps({'database': database}))
url = base.set(database=database).render_as_string(hide_password=False)
environment = dict(os.environ, DATABASE_URL=url, T03_TEST_DATABASE_URL=url, PYTHONUTF8='1', T13_REPORT_DIR=str(report))
commands = [] if '--resume' in sys.argv else [('alembic', ['-m', 'alembic', 'upgrade', 'head']), ('seed', ['scripts/seed.py'])]
commands.append(('pytest', ['-m', 'pytest', '-v', '-s', *(['tests/test_liveness.py', 'tests/test_liveness_settings.py', 'tests/test_admin_api.py', 'tests/test_openapi_contract.py'] if '--all' not in sys.argv else [])]))
for name, arguments in commands:
    result = subprocess.run([sys.executable, *arguments], cwd=HUB, env=environment, capture_output=True, text=True, encoding='utf8', errors='replace')
    filename = ('pytest-full' if '--all' in sys.argv else 'pytest-focused') if name == 'pytest' else name
    (report / (filename + '.log')).write_text(result.stdout + result.stderr, encoding='utf8')
    print(f'{name}: exit={result.returncode}; log={report / (filename + ".log")}', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
print('PASS: dùng DB T13 riêng; không sửa DB demo hay DB camera review.')
