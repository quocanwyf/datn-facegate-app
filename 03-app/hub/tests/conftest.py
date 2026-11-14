"""Dữ liệu kiểm từ manifest/log thật; không tạo dữ liệu khuôn mặt."""
import json
import pytest
from app.recog.model_loader import BLUFR, MANIFEST, ROOT


@pytest.fixture
def model_row():
    rows = json.loads(MANIFEST.read_text(encoding='utf-8'))['checkpoints']
    row = next(item for item in rows if item['id'] == 'r18_uniface_v1_lam0.6_m0.45_s3_e28:best')
    reference = json.loads(BLUFR.read_text(encoding='utf-8'))['ket_qua'][row['id']]['meta']
    return {'manifest_id': row['id'], 'source_path': str(ROOT / '02-thuc-nghiem' / row['path']),
            'source_sha256': row['sha256'], 'stripped_sha256': reference['sha256'],
            'epoch': row['expected_epoch'], 't_bs': reference['t_eq30']}
