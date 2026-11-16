"""Chạy fixture T12 trên DB test T11 (rollback), không dùng DB T08/clone sinh trắc."""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / '03-app/hub'
sys.path.insert(0, str(HUB))
from app.config import get_settings
from sqlalchemy.engine import make_url
database = json.loads((Path(os.environ['LOCALAPPDATA']) / 'FaceGate/T11-test-context.json').read_text())['database']
if not database.startswith('facegate_t11_'): raise SystemExit('Cần DB test riêng từ verify_t11.py')
url = make_url(get_settings().database_url.get_secret_value()).set(database=database).render_as_string(hide_password=False)
environment = dict(os.environ, T03_TEST_DATABASE_URL=url, DATABASE_URL=url, PYTHONUTF8='1', PYTHONPATH=os.pathsep.join([str(HUB), str(HUB / 'tests')]))
result = subprocess.run([sys.executable, '-m', 'pytest', '-c', str(HUB / 'pyproject.toml'), '-v', str(Path(__file__).with_name('test_me_contract.py'))], cwd=HUB, env=environment, capture_output=True, text=True, encoding='utf8')
(ROOT / '03-app/ket-qua-kiem-thu/2026-11-16_T12/pytest-db.log').write_text(result.stdout + result.stderr, encoding='utf8')
print('T12 PostgreSQL 0/1/2 event, exit=', result.returncode)
raise SystemExit(result.returncode)
