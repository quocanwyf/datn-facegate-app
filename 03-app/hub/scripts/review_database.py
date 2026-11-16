"""Clone test từ nguồn T08 đã duyệt; không chèn event/ngày công/vector giả."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.config import get_settings


def context(tag, resume=False):
    if tag not in ('T13', 'T14'): raise ValueError('Tag review không hợp lệ')
    private = Path(os.environ['LOCALAPPDATA'])/'FaceGate'
    marker = private/f'{tag}-review-context.json'
    base = make_url(get_settings().database_url.get_secret_value())
    if resume:
        result = json.loads(marker.read_text())
    else:
        source = json.loads((private/'T08-last-context.json').read_text())
        if not source['database'].startswith('facegate_t08_') or not Path(source['data_dir']).resolve().is_relative_to(private.resolve()):
            raise ValueError('Nguồn phải là T08 riêng đã đăng ký thật.')
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result = dict(database=f'facegate_{tag.lower()}_{stamp}', data_dir=str(private/f'{tag}-review-{stamp}'))
        password = (private/'postgresql16/admin-password.txt').read_text().strip()
        admin = base.set(drivername='postgresql', username='postgres', password=password, database='postgres')
        with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True, connect_timeout=10) as connection:
            connection.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {} OWNER {}').format(
                sql.Identifier(result['database']), sql.Identifier(source['database']), sql.Identifier(base.username)))
        shutil.copytree(source['data_dir'], result['data_dir'])
        marker.write_text(json.dumps(result))
    if not result['database'].startswith(f'facegate_{tag.lower()}_') or not Path(result['data_dir']).resolve().is_relative_to(private.resolve()):
        raise ValueError('Context phải là DB/kho review riêng.')
    return result, base.set(database=result['database']).render_as_string(hide_password=False)
