"""Đánh giá trên VALIDATION CASIA (danh tính không có trong train) — mọi cặp (i < j) trong tập ảnh val.

Cùng cách trích đặc trưng như test (.bin): embedding(ảnh) + embedding(ảnh lật), chuẩn hoá L2, cosine.
Metric chọn checkpoint / siêu tham số: TAR@FAR=1e-3 (``tar@far=0.001``). Báo thêm 1e-2, 1e-4, 1e-5
để theo dõi (FAR 1e-5 có ý nghĩa khi số cặp âm ≥ ~10⁶).
"""
from __future__ import annotations

import time
from typing import Dict, Iterable

import numpy as np
import torch

from ..data.datasets import decode_image
from ..data.recordio import unpack_record
from .metrics import tar_at_far
from .verification import extract_embeddings

VAL_FARS = (1e-2, 1e-3, 1e-4, 1e-5)


def load_val_u8(rec_dataset, positions: np.ndarray) -> torch.Tensor:
    """Giải mã 1 lần các ảnh val → uint8 (N,3,112,112) RGB, giữ trong RAM (~5k ảnh ≈ 0.2 GB)."""
    imgs = None
    for k, p in enumerate(positions):
        _, _, buf = unpack_record(rec_dataset.reader.read(int(rec_dataset.imgidx[int(p)])))
        img = decode_image(buf)
        if imgs is None:
            imgs = torch.empty(len(positions), 3, img.shape[0], img.shape[1], dtype=torch.uint8)
        imgs[k] = torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1)
    return imgs


def all_pairs_scores(emb: np.ndarray, labels: np.ndarray):
    """(scores, issame) của mọi cặp i < j."""
    labels = np.asarray(labels)
    iu = np.triu_indices(len(labels), k=1)
    sim = emb @ emb.T
    return sim[iu].astype(np.float32), (labels[iu[0]] == labels[iu[1]])


def evaluate_val(backbone, images_u8: torch.Tensor, labels: np.ndarray, device, batch_size: int = 256,
                 amp: bool = False, fars: Iterable[float] = VAL_FARS) -> Dict[str, float]:
    t0 = time.time()
    emb = extract_embeddings(backbone, images_u8, device, batch_size, flip=True, amp=amp)
    scores, same = all_pairs_scores(emb, labels)
    res = tar_at_far(scores, same, fars)
    res["mean_cos_pos"] = float(scores[same].mean())
    res["mean_cos_neg"] = float(scores[~same].mean())
    res["n_images"] = int(len(labels))
    res["seconds"] = time.time() - t0
    return res
