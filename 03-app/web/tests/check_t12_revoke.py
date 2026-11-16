"""Read-only DB/file evidence on T12 clone and unchanged T08 original; no vectors output."""
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '03-app/hub'))
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.config import get_settings

base = make_url(get_settings().database_url.get_secret_value()).set(drivername='postgresql+psycopg')
private = Path(os.environ['LOCALAPPDATA']) / 'FaceGate'
def snapshot(name):
    context = json.loads((private / name).read_text())
    if not context['database'].startswith(('facegate_t08_', 'facegate_t12_')):
        raise SystemExit('Chỉ đọc DB review T08/T12.')
    engine = create_engine(base.set(database=context['database']), hide_parameters=True)
    with engine.connect() as connection:
        row = connection.execute(text("SELECT id, attendance_method, face_consent_at, face_consent_by FROM employee WHERE code='NV006'")).mappings().one()
        employee_id = row['id']
        values = dict(method=row['attendance_method'], consent_at_null=row['face_consent_at'] is None, consent_by_null=row['face_consent_by'] is None)
        for label, query in {
            'profiles': 'SELECT count(*) FROM face_profile WHERE employee_id=:id',
            'samples': 'SELECT count(*) FROM face_sample WHERE profile_id IN (SELECT id FROM face_profile WHERE employee_id=:id)',
            'templates': 'SELECT count(*) FROM face_template WHERE profile_id IN (SELECT id FROM face_profile WHERE employee_id=:id)',
            'embeddings': 'SELECT count(*) FROM face_embedding WHERE sample_id IN (SELECT s.id FROM face_sample s JOIN face_profile p ON p.id=s.profile_id WHERE p.employee_id=:id)',
            'events': 'SELECT count(*) FROM recognition_event WHERE employee_id=:id',
            'days': 'SELECT count(*) FROM attendance_day WHERE employee_id=:id',
        }.items(): values[label] = connection.scalar(text(query), {'id': employee_id})
        paths = connection.scalars(text('SELECT s.image_path FROM face_sample s JOIN face_profile p ON p.id=s.profile_id WHERE p.employee_id=:id'), {'id': employee_id}).all()
        values['sample_files_present'] = sum((Path(context['data_dir']) / path).is_file() for path in paths)
        values['sample_paths'] = paths  # Relative paths only, no image/vector bytes.
    engine.dispose()
    return values, context
clone, context = snapshot('T12-test-context.json')
source, _ = snapshot('T08-last-context.json')
report = ROOT / '03-app/ket-qua-kiem-thu/2026-11-16_T12'
phase = sys.argv[1]
if phase not in ('before', 'after'): raise SystemExit('before|after')
if phase == 'after':
    before = json.loads((report / 'revoke-before.json').read_text())
    assert clone['method'] == 'MANUAL' and clone['consent_at_null'] and clone['consent_by_null']
    assert all(clone[key] == 0 for key in ('profiles', 'samples', 'templates', 'embeddings'))
    assert clone['events'] == before['clone']['events'] and clone['days'] == before['clone']['days']
    assert all(not (Path(context['data_dir']) / path).exists() for path in before['clone']['sample_paths'])
    assert source == before['source'], 'Nguồn T08 phải giữ nguyên'
else:
    assert clone['method'] == 'FACE' and clone['samples'] >= 5 and clone['sample_files_present'] >= 5
(report / f'revoke-{phase}.json').write_text(json.dumps({'clone': clone, 'source': source}, ensure_ascii=False, indent=2), encoding='utf8')
print(f'PASS {phase}: clone riêng, không xuất ảnh/vector, nguồn T08 được đối chiếu.')
