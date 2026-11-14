"""Cổng kiểm mô hình bốn bước; không sửa hoặc trích lại checkpoint nguồn."""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

HUB = Path(__file__).resolve().parents[2]
ROOT = HUB.parent.parent
VENDOR = HUB / 'vendor'
MANIFEST = VENDOR / 'manifest/manifest_24.json'
STRIP_MAP = VENDOR / 'manifest/strip_map_ban_sao.json'
BLUFR = ROOT / '02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json'


class ModelNotVerified(RuntimeError):
    code = 'MODEL_NOT_VERIFIED'

    def __init__(self, step: int, message: str, report: dict):
        super().__init__(f'Bước {step}: {message}')
        self.step = step
        self.report = report


def frozen_features():
    # Bắt buộc đặt trước import; vendor tự đặt dont_write_bytecode cho code đóng băng.
    os.environ['DATN_CODE_DIR'] = str(VENDOR / 'code')
    sys.dont_write_bytecode = True
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    return importlib.import_module('evaltest.features')


def extract_aligned_bgr(backbone, aligned_bgr, device):
    """Biên ảnh đã căn chỉnh dùng chung cho parity T02 và worker T04.

    Chỉ chuyển BGR sang RGB uint8; toàn bộ chuẩn hóa/lật/L2 thuộc hàm vendor.
    Caller phải gọi trong worker khi phục vụ yêu cầu nhận dạng.
    """
    import cv2
    import numpy as np
    import torch

    if not isinstance(aligned_bgr, np.ndarray) or aligned_bgr.dtype != np.uint8 or aligned_bgr.shape != (112, 112, 3):
        raise ValueError('Cần ảnh BGR uint8 đã căn chỉnh kích thước 112x112')
    rgb = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
    tensor = torch.from_numpy(np.ascontiguousarray(rgb))[None]
    return frozen_features().extract_features(backbone, tensor, device)


def load_verified(model_row: Mapping[str, Any], device, *,
                  manifest_path: Path = MANIFEST, strip_map_path: Path = STRIP_MAP,
                  blufr_path: Path = BLUFR):
    """Trả (backbone, meta, verify_report); lỗi luôn giữ bước và mã MODEL_NOT_VERIFIED.

    Các đường dẫn keyword chỉ để kiểm nguồn/test bản sao tạm; Hub dùng nguồn mặc định.
    """
    report = {'manifest_id': model_row.get('manifest_id'), 'device': str(device), 'steps': []}
    step = 1
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        row = next(item for item in manifest['checkpoints'] if item['id'] == model_row['manifest_id'])
        source = Path(model_row['source_path'])
        if not source.is_absolute():
            source = ROOT / source
        with source.open('rb') as stream:
            actual_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual_sha != row['sha256'] or model_row['source_sha256'] != row['sha256']:
            raise ValueError('SHA256 checkpoint không khớp manifest')
        report['steps'].append({'step': step, 'ok': True, 'sha256': actual_sha})

        step = 2
        expected = json.loads(Path(blufr_path).read_text(encoding='utf-8'))['ket_qua'][row['id']]['meta']
        strip_map = json.loads(Path(strip_map_path).read_text(encoding='utf-8'))
        link = strip_map.get(expected['sha256'])
        if (not link or link['source_sha256'] != actual_sha or link['dest_sha256'] != expected['sha256']
                or link['id'] != row['id'] or model_row['stripped_sha256'] != expected['sha256']):
            raise ValueError('Không có chuỗi nối checkpoint tới bản backbone đã tạo số liệu BLUFR')
        report['steps'].append({'step': step, 'ok': True, 'stripped_sha256': expected['sha256']})

        step = 3
        features = frozen_features()
        backbone, meta = features.load_backbone(str(source), device, row=row, expected_sha=actual_sha)
        report['steps'].append({'step': step, 'ok': True, 'epoch': meta['epoch'], 'amp': meta['amp'],
                                'missing_keys': meta['missing_keys'], 'unexpected_keys': meta['unexpected_keys']})

        step = 4
        actual_t = float(meta['t_eq30'])
        expected_t = float(expected['t_eq30'])
        if not math.isfinite(actual_t) or not math.isfinite(expected_t) or abs(actual_t - expected_t) > 1e-6:
            raise ValueError('Ngưỡng học được t_eq30 không khớp số liệu BLUFR')
        report['steps'].append({'step': step, 'ok': True, 't_eq30': actual_t, 'reference_t_eq30': expected_t})
        return backbone, meta, report
    except (Exception, SystemExit) as error:
        report['steps'].append({'step': step, 'ok': False, 'message': str(error)})
        raise ModelNotVerified(step, str(error), report) from error
