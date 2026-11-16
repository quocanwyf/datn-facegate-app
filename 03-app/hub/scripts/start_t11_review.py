"""Hub CPU thật, tiếp tục gallery đã được duyệt ở T08; không tạo hồ sơ/event giả."""
import json
import os
from pathlib import Path
import sys
import time

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB))
os.chdir(HUB)
from sqlalchemy.engine import make_url
from app.config import get_settings

private = Path(os.environ['LOCALAPPDATA']) / 'FaceGate'
context = json.loads((private / 'T08-last-context.json').read_text())
if not context['database'].startswith('facegate_t08_') or not Path(context['data_dir']).is_dir():
    raise SystemExit('Cần DB/gallery T08 đã đăng ký và duyệt bằng app thật.')
base = make_url(get_settings().database_url.get_secret_value())
os.environ.update(DATABASE_URL=base.set(database=context['database']).render_as_string(hide_password=False),
    HUB_DATA_DIR=context['data_dir'], HUB_PUBLIC_URL='http://10.0.2.2:8000', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONUTF8='1')
get_settings.cache_clear()
from app.main import create_app
app = create_app()
publish = app.state.monitor.publish
def observe_commit(kind, identity):
    if kind == 'event':
        print('MONITOR_COMMIT '+json.dumps({'event_id': str(identity), 'commit_observed_ms': time.time()*1000}), flush=True)
    publish(kind, identity)
app.state.monitor.publish = observe_commit
print('Review T11: gallery T08, Hub CPU port 8000; timestamp ghi sau commit thật.', flush=True)
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=8000)
