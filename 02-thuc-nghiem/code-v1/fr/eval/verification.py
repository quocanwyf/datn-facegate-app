"""Đánh giá 1:1 trên các file .bin (LFW, CFP-FP, AgeDB-30, CALFW, CPLFW).

Đặc trưng ảnh = embedding(ảnh) + embedding(ảnh lật ngang), rồi chuẩn hoá L2 (như insightface và
test của UniFace: "cộng feature ảnh gốc + ảnh lật"). Báo: accuracy 10-fold (± std), TAR@FAR 1e-2/1e-3
(FAR thấp hơn KHÔNG đo được trên .bin vì chỉ ~3,000 cặp âm — xem ke-hoach-du-lieu.md mục 2).
"""
from __future__ import annotations

import os
import time
from typing import Dict, Iterable

import numpy as np
import torch

from ..data.bin_loader import load_bin
from .metrics import tar_at_far, verification_accuracy_10fold, l2_normalize


@torch.no_grad()
def extract_embeddings(backbone: torch.nn.Module, images_u8: torch.Tensor, device, batch_size: int = 256,
                       flip: bool = True, amp: bool = False) -> np.ndarray:
    was_training = backbone.training
    backbone.eval()
    feats = []
    for i in range(0, images_u8.size(0), batch_size):
        x = images_u8[i:i + batch_size].to(device, non_blocking=True).float().div_(255).sub_(0.5).div_(0.5)
        with torch.autocast(device_type=device.type, enabled=amp and device.type == "cuda"):
            e = backbone(x).float()
            if flip:
                e = e + backbone(torch.flip(x, dims=[3])).float()
        feats.append(e.cpu())
    backbone.train(was_training)
    return l2_normalize(torch.cat(feats).numpy())


def evaluate_bin(backbone, path: str, device, batch_size: int = 256, amp: bool = False,
                 fars: Iterable[float] = (1e-2, 1e-3)) -> Dict[str, float]:
    t0 = time.time()
    imgs, issame = load_bin(path)
    emb = extract_embeddings(backbone, imgs, device, batch_size, flip=True, amp=amp)
    e1, e2 = emb[0::2], emb[1::2]
    res = verification_accuracy_10fold(e1, e2, issame)
    res.update(tar_at_far(np.sum(e1 * e2, axis=1), issame, fars))
    res["seconds"] = time.time() - t0
    del imgs
    return res


def evaluate_bins(backbone, bin_dir: str, names: Iterable[str], device, batch_size: int = 256, amp: bool = False):
    out = {}
    for name in names:
        p = os.path.join(bin_dir, f"{name}.bin")
        if not os.path.exists(p):
            out[name] = {"error": f"không thấy {p}"}
            continue
        out[name] = evaluate_bin(backbone, p, device, batch_size, amp)
    return out
