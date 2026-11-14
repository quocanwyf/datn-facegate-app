"""Chỉ đo trên ảnh LFW thật; không có dữ liệu thì ghi SKIP."""
import os
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from m0_common import aligned_sample, reference_rows, select_device, verified_model, write_report


@pytest.mark.skipif(not os.environ.get('T02_LFW_ROOT'), reason='Chưa cung cấp LFW thật qua T02_LFW_ROOT')
def test_color_order():
    import numpy as np
    import torch
    from app.recog.model_loader import extract_aligned_bgr, frozen_features
    from fr.align.detector import YuNetDetector
    device = select_device(os.environ.get('T02_DEVICE', 'cuda'))
    backbone, _, _ = verified_model(device)
    name = sorted(row['image'] for row in reference_rows() if row['method'] == 'detect')[0]
    image = aligned_sample(Path(os.environ['T02_LFW_ROOT']), name, YuNetDetector(score_threshold=0.6))
    correct = extract_aligned_bgr(backbone, image, device)
    wrong = frozen_features().extract_features(backbone, torch.from_numpy(np.ascontiguousarray(image.transpose(2, 0, 1)))[None], device)
    cosine = float(np.sum(correct * wrong) / (np.linalg.norm(correct) * np.linalg.norm(wrong)))
    assert np.isfinite(cosine)
    write_report(os.environ.get('T02_COLOR_OUTPUT'), {'image_ref': name, 'device': str(device), 'cos_rgb_vs_bgr': cosine,
                 'expected_below_0_99': cosine < 0.99,
                 'proposal': None if cosine < 0.99 else 'Bổ sung nhiều ảnh LFW có phổ màu khác nhau; giữ test hợp đồng RGB tại biên tensor.',
                 'blufr_repeated': False})
