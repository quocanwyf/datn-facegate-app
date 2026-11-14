"""Đọc file đánh giá .bin của insightface (lfw.bin, cfp_fp.bin, agedb_30.bin, calfw.bin, cplfw.bin).

Định dạng (theo insightface arcface_torch/eval/verification.py, hàm load_bin):
    pickle (bins, issame_list); bins = 2·P ảnh đã mã hoá (cặp i = ảnh 2i, 2i+1), issame_list = P nhãn bool.
"""
from __future__ import annotations

import pickle
from typing import Tuple

import numpy as np
import torch

from .datasets import decode_image


def load_bin(path: str, image_size: int = 112) -> Tuple[torch.Tensor, np.ndarray]:
    """Trả về (images (2P,3,H,W) **uint8 RGB** — giữ uint8 để tiết kiệm RAM (LFW: ~0.45 GB thay vì 1.8 GB fp32);
    chuẩn hoá [−1,1] và lật ảnh làm theo batch khi trích đặc trưng), issame (P,) bool."""
    with open(path, "rb") as f:
        try:
            bins, issame = pickle.load(f)                    # file tạo bằng Python 3
        except UnicodeDecodeError:
            f.seek(0)
            bins, issame = pickle.load(f, encoding="bytes")  # file tạo bằng Python 2 (insightface gốc)
    imgs = torch.empty(len(bins), 3, image_size, image_size, dtype=torch.uint8)
    for i, b in enumerate(bins):
        if isinstance(b, np.ndarray):
            b = b.tobytes()
        img = decode_image(bytes(b))
        if img.shape[0] != image_size or img.shape[1] != image_size:
            import cv2
            img = cv2.resize(img, (image_size, image_size))
        imgs[i] = torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1)
    return imgs, np.asarray(issame, dtype=bool)
