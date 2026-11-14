"""Tiện ích script M0; chỉ đọc nguồn, không ghi ảnh/vector hoặc train mô hình."""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import sys

HUB = Path(__file__).resolve().parents[1]
ROOT = HUB.parent.parent
VENDOR = HUB / 'vendor'
MODEL_ID = 'r18_uniface_v1_lam0.6_m0.45_s3_e28:best'
ALIGN_LOG = ROOT / '02-thuc-nghiem/results/2026-11-05_eval-lfw/align_log.csv'
BLUFR = ROOT / '02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json'
VAL_LOG = ROOT / '02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/val.jsonl'
sys.dont_write_bytecode = True
os.environ['DATN_CODE_DIR'] = str(VENDOR / 'code')
for directory in (HUB, VENDOR, VENDOR / 'code'):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def model_row():
    manifest = json.loads((VENDOR / 'manifest/manifest_24.json').read_text(encoding='utf-8'))
    row = next(item for item in manifest['checkpoints'] if item['id'] == MODEL_ID)
    reference = json.loads(BLUFR.read_text(encoding='utf-8'))['ket_qua'][MODEL_ID]['meta']
    return row, reference, {'manifest_id': MODEL_ID, 'source_path': str(ROOT / '02-thuc-nghiem' / row['path']),
                            'source_sha256': row['sha256'], 'stripped_sha256': reference['sha256']}


def select_device(name):
    import torch
    selected = 'cuda' if name == 'auto' and torch.cuda.is_available() else 'cpu' if name == 'auto' else name
    if selected == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('Không có torch CUDA khả dụng; không tự chuyển sang CPU để nghiệm thu GPU')
    return torch.device(selected)


def verified_model(device):
    from app.recog.model_loader import load_verified
    return load_verified(model_row()[2], device)


def write_report(path, data):
    print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), flush=True)
    if path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')


def reference_rows():
    with ALIGN_LOG.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def detect_like_lfw(detector, image):
    from fr.align.detector import pick_center_face
    faces, method = detector.detect(image), 'detect'
    if not faces:
        faces, method = detector.detect(image, score_threshold=0.3), 'detect_retry'
    return pick_center_face(faces, image.shape), faces, method


def aligned_sample(lfw, image_name, detector):
    import cv2
    from fr.align.template import norm_crop
    root = Path(lfw).resolve()
    path = (root / image_name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Đường dẫn ảnh ngoài thư mục LFW')
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f'Không đọc được ảnh LFW: {image_name}')
    face, _, _ = detect_like_lfw(detector, image)
    if face is None:
        raise RuntimeError(f'Không detect được ảnh đã chọn: {image_name}; không thay ảnh để lấy kết quả đạt')
    aligned, _ = norm_crop(image, face['landmarks'])
    return aligned
