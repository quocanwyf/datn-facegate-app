"""Bước 2 — TRÍCH FEATURE: MỘT hàm duy nhất cho mọi mô hình (ArcFace/CosFace/SphereFace2/UniFace/UniFace+V1).

Quy ước (giống hệt validation CASIA đã dùng để chọn best.pt — ``fr/eval/val_casia.py``):
  - chỉ BACKBONE (``ck["backbone"]``); bỏ head (W, b̃, buffer ``proto``/``proto_seen`` của V1); ``eval()``;
  - ảnh 112×112 RGB uint8 → (x/255 − 0,5)/0,5;
  - FLIP TEST = CỘNG: f = emb(ảnh) + emb(ảnh lật ngang), rồi chuẩn hoá L2; so bằng cosine (= tích vô hướng).
    Lý do chọn: (1) đúng cách val CASIA đã đo khi chọn best.pt (đổi quy ước ở test sẽ làm số test và số val không
    cùng thước); (2) đúng giao thức insightface cho .bin và IJB-C (TestMode F2) và cách test của UniFace;
    (3) áp như nhau cho 24 checkpoint. Phương án khác (không lật) KHÔNG dùng.
  - GPU: backbone fp16 bên trong khối conv (``get_backbone(fp16=True)`` + autocast) — giống lúc train/val trên T4;
    CPU: fp32. cuDNN deterministic để chạy lại cho cùng feature.
Hàm lõi gọi thẳng ``fr.eval.verification.extract_embeddings`` của code đóng băng (cùng một dòng code với val).
"""
from __future__ import annotations

import math
import os
from typing import Dict, Optional

import numpy as np
import torch

from .common import import_code, sha256_file

import_code()
from fr.backbones import get_backbone                        # noqa: E402
from fr.eval.verification import extract_embeddings          # noqa: E402
from fr.utils.checkpoint import load_checkpoint              # noqa: E402
from fr.utils.config import config_fingerprint               # noqa: E402

FLIP_MODE = "sum"            # emb(x) + emb(flip(x)) → L2 ; ghi vào mọi file kết quả
PREPROCESS = "RGB uint8 112x112 -> (x/255-0.5)/0.5; flip ngang (dims=[3]); cộng; L2-normalize; cosine"


def setup_determinism():
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def pick_device(name: Optional[str] = None) -> torch.device:
    if name:
        return torch.device(name)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def verify_checkpoint(ck: dict, row: dict) -> Dict:
    """Kiểm phần nằm TRONG checkpoint (cần torch): config fingerprint, loại head, epoch, giá trị val của best."""
    cfg = ck.get("config") or {}
    out = {"config_fp_ok": config_fingerprint(cfg) == row["config_fingerprint"] if cfg else None,
           "head_ok": (cfg.get("head") or {}).get("name") == row["loss"] if cfg else None,
           "epoch_ok": int(ck.get("epoch", -1)) == int(row["expected_epoch"])}
    if row["kind"] == "best" and row.get("best_metric_value") is not None:
        v = (ck.get("val") or {}).get(row.get("best_metric", "tar@far=0.001"))
        out["best_val_ok"] = v is not None and abs(float(v) - float(row["best_metric_value"])) < 1e-12
    bad = [k for k, v in out.items() if v is False or v is None]
    if bad:
        raise SystemExit(f"DỪNG — {row['id']}: checkpoint lệch manifest ({', '.join(bad)})")
    return out


def load_backbone(path: str, device: torch.device, row: Optional[dict] = None, expected_sha: Optional[str] = None,
                  strip_map: Optional[dict] = None):
    """Nạp backbone từ checkpoint đầy đủ (best/last.pt) hoặc bản đã trích chỉ-backbone (``strip_backbone.py``).

    - ``expected_sha``: sha256 file gốc trong manifest. Với bản trích, ``strip_map`` (đích → nguồn) phải nối được
      sha256 file đích về đúng sha256 gốc.
    - ``load_state_dict(strict=True)``: thiếu/thừa khoá → lỗi (không bao giờ nạp nhầm head vào backbone).
    Trả (backbone ở eval(), meta)."""
    sha = sha256_file(path)
    if expected_sha is not None:
        src_sha = sha
        if sha != expected_sha:
            src_sha = (strip_map or {}).get(sha, {}).get("source_sha256")
        if src_sha != expected_sha:
            raise SystemExit(f"DỪNG — sha256 {os.path.basename(path)} không khớp manifest")
    ck = load_checkpoint(path)
    if row is not None:
        verify_checkpoint(ck, row)
    cfg = ck["config"]
    amp = device.type == "cuda"
    bb = get_backbone(cfg["model"]["backbone"], int(cfg["model"]["emb_dim"]), 0.0, fp16=amp)
    res = bb.load_state_dict(ck["backbone"], strict=True)
    bb = bb.to(device).eval()
    for p in bb.parameters():
        p.requires_grad_(False)
    head = ck.get("head") or {}
    meta = {"sha256": sha, "epoch": int(ck["epoch"]), "global_step": int(ck.get("global_step", -1)),
            "head_name": cfg["head"]["name"], "backbone": cfg["model"]["backbone"], "amp": amp,
            "head_keys_ignored": sorted(head.keys()) if head else list(ck.get("head_keys", [])),
            "missing_keys": list(res.missing_keys), "unexpected_keys": list(res.unexpected_keys),
            "is_stripped": bool(ck.get("stripped", False))}
    b = head.get("bias") if isinstance(head, dict) else None
    if b is None and "head_bias" in ck:
        b = ck["head_bias"]
    if b is not None and torch.as_tensor(b).numel() == 1 and cfg["head"]["name"] in ("uniface", "uniface_v1"):
        s = float(cfg["head"].get("s", 64.0))
        meta["t_eq30"] = float(torch.as_tensor(b).item()) / s          # ngưỡng học được t = b̃/s (chỉ mô tả)
    return bb, meta


def extract_features(backbone: torch.nn.Module, images_u8: torch.Tensor, device: torch.device,
                     batch_size: int = 256) -> np.ndarray:
    """HÀM DUY NHẤT trích feature cho mọi mô hình. (N,3,112,112) uint8 RGB → (N,d) float32 đã L2, flip cộng."""
    if images_u8.dtype != torch.uint8 or images_u8.dim() != 4 or tuple(images_u8.shape[1:]) != (3, 112, 112):
        raise ValueError(f"cần uint8 (N,3,112,112), nhận {images_u8.dtype} {tuple(images_u8.shape)}")
    setup_determinism()
    f = extract_embeddings(backbone, images_u8, device, batch_size=batch_size, flip=True, amp=device.type == "cuda")
    f = np.ascontiguousarray(f, dtype=np.float32)
    if not np.isfinite(f).all():
        raise FloatingPointError("feature có NaN/Inf")
    n = np.linalg.norm(f, axis=1)
    if not np.allclose(n, 1.0, atol=1e-3):
        raise FloatingPointError("feature chưa chuẩn hoá L2")
    return f
