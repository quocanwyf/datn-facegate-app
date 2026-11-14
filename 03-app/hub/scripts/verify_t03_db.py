"""Kiểm T03 trên hai DB mới riêng biệt; không xóa/thay DB demo hiện tại."""
from datetime import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import ROOT, get_settings


def run(command, output, env):
    process = subprocess.run(command, text=True, encoding='utf-8', errors='replace', capture_output=True, env=env)
    output.write_text(process.stdout + process.stderr, encoding='utf-8')
    if process.returncode:
        raise RuntimeError(f'Lệnh kiểm tra lỗi; xem {output.name}')
    print(f'{output.name}: exit 0', flush=True)
    return process.stdout


def normalize_dump(data):
    # Hai dòng nonce pg_dump 16.14 khác nhau mỗi lần; Alembic có bảng đánh dấu revision riêng.
    data = re.sub(r'^\\(?:un)?restrict .*\n', '', data, flags=re.M)
    return '\n'.join(line for line in data.splitlines() if line.strip()) + '\n'


def main():
    report = ROOT / '03-app/ket-qua-kiem-thu/2026-11-15_T03'
    report.mkdir(parents=True, exist_ok=True)
    base = make_url(get_settings().database_url.get_secret_value())
    suffix = datetime.now().strftime('%Y%m%d%H%M%S')
    names = {kind: f'facegate_t03_{kind}_{suffix}' for kind in ('ref', 'migrated')}
    admin_file = Path(os.environ['LOCALAPPDATA']) / 'FaceGate/postgresql16/admin-password.txt'
    admin_url = os.environ.get('T03_ADMIN_URL')
    if not admin_url:
        admin_url = base.set(drivername='postgresql', username='postgres', password=admin_file.read_text().strip(), database='postgres').render_as_string(hide_password=False)
    with psycopg.connect(admin_url, autocommit=True) as admin:
        for name in names.values():
            admin.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(name), sql.Identifier(base.username)))
    (report / 'test-databases.json').write_text(json.dumps(names, indent=2), encoding='utf-8')
    env = dict(os.environ, PYTHONUTF8='1', PGCLIENTENCODING='UTF8', PGPASSWORD=base.password)
    pg = Path(os.environ.get('T03_PG_BIN', Path(os.environ['LOCALAPPDATA']) / 'FaceGate/postgresql16/pgsql/bin'))
    def psql(name, source, log):
        return run([str(pg / 'psql.exe'), '-h', base.host, '-p', str(base.port or 5432), '-U', base.username,
                    '-d', name, '-v', 'ON_ERROR_STOP=1', '-f', str(source)], report / log, env)
    psql(names['ref'], ROOT / '03-app/db/schema.sql', 'reference-schema.log')
    migrated_url = base.set(database=names['migrated']).render_as_string(hide_password=False)
    env['DATABASE_URL'] = migrated_url
    run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], report / 'alembic-upgrade.log', env)
    run([sys.executable, 'scripts/seed.py'], report / 'seed.log', env)
    output = psql(names['migrated'], ROOT / '03-app/db/test_constraints.sql', 'constraints.log')
    if not re.search(r'44\s*\|\s*44', output):
        raise RuntimeError('Chưa xác nhận 44/44; xem constraints.log')
    dumps = {}
    for kind, name in names.items():
        dumps[kind] = run([str(pg / 'pg_dump.exe'), '-h', base.host, '-p', str(base.port or 5432), '-U', base.username,
                           '-d', name, '--schema-only', '--no-owner', '--no-privileges', '--exclude-table=public.alembic_version'], report / f'{kind}-schema.sql', env)
    raw_diff = ''.join(difflib.unified_diff(dumps['ref'].splitlines(True), dumps['migrated'].splitlines(True), fromfile='reference', tofile='alembic'))
    (report / 'schema-raw.diff').write_text(raw_diff, encoding='utf-8')
    diff = ''.join(difflib.unified_diff(normalize_dump(dumps['ref']).splitlines(True), normalize_dump(dumps['migrated']).splitlines(True), fromfile='reference', tofile='alembic'))
    (report / 'schema.diff').write_text(diff, encoding='utf-8')
    if diff:
        raise RuntimeError('Schema dump khác nhau; xem schema.diff')
    env['T03_TEST_DATABASE_URL'] = migrated_url
    run([sys.executable, '-m', 'pytest', '-q'], report / 'pytest.log', env)
    print('Đã kiểm Alembic, 44/44, schema diff và pytest. DB demo không bị thay đổi.')


if __name__ == '__main__':
    main()
