import os
from pathlib import Path
import cv2
import numpy as np
import pytest
import torch
from app.recog.detector import Detector
from app.recog.embedder import Embedder
from app.recog.model_loader import frozen_features, load_verified


@pytest.mark.skipif(not os.environ.get('TEST_FACES_DIR'), reason='Chưa cung cấp ảnh webcam riêng qua TEST_FACES_DIR')
def test_actual_private_webcam_image_matches_vendor(model_row):
    device = torch.device('cpu')
    backbone, meta, _ = load_verified(model_row, device)
    detector = Detector(80, .35)
    candidates = sorted(Path(os.environ['TEST_FACES_DIR']).glob('*.png'))
    measured = []
    for path in candidates:
        image = cv2.imread(str(path))
        if image is None:
            continue
        observation = detector.observe(image)
        if not observation.valid:
            continue
        actual = Embedder(backbone, device).embed(image, observation.landmarks)
        from fr.align.template import norm_crop
        aligned, _ = norm_crop(image, observation.landmarks)
        rgb = np.ascontiguousarray(cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB).transpose(2, 0, 1))
        expected = frozen_features().extract_features(backbone, torch.from_numpy(rgb)[None], device)[0]
        delta = float(np.max(np.abs(actual - expected)))
        assert actual.shape == (512,) and delta <= 1e-6
        measured.append(delta)
    assert measured, 'Không có ảnh thật đạt kiểm chất lượng; không thay bằng ảnh giả'
    print(f'private_webcam_images={len(measured)}; device=cpu; amp={meta["amp"]}; max_abs_delta={max(measured)}')
