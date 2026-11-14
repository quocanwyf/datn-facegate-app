"""Ảnh LFW 112×112 cho BLUFR và Giao thức A.

Hai đường vào (cùng định dạng ``aligned_u8.npy`` (N,3,112,112) RGB + ``index.csv`` cột image):
  (1) LFW gốc deep-funneled → căn chỉnh bằng ``code/tools/align_lfw.py`` (YuNet + template ArcFace, điểm mốc trung
      vị cho ảnh không detect được) — đúng pipeline B1 (protocol-lfw-openset.md §2). Căn chỉnh không phụ thuộc mô hình
      → làm MỘT lần, dùng chung 24 checkpoint; ghi sha256 của mảng ảnh.
  (2) Thư mục đã căn sẵn (có aligned_u8.npy + index.csv) — dùng cho chạy thử với ảnh giả.
Kiểm toàn vẹn: sha256 file chia khớp manifest của data_splits; mọi ảnh trong mọi split phải có trong index.
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .common import import_code, load_json, sha256_file

import_code()


def ensure_aligned(lfw_root: str, people_csv: str, work_dir: str, log=print) -> str:
    if os.path.isfile(os.path.join(lfw_root, "aligned_u8.npy")):
        return lfw_root
    out = os.path.join(work_dir, "lfw_aligned")
    if not os.path.isfile(os.path.join(out, "aligned_u8.npy")):
        from tools.align_lfw import align_lfw                        # code/tools (chỉ đọc)
        align_lfw(lfw_root, people_csv, out, log=log)
    return out


def load_aligned(aligned_dir: str) -> Tuple[np.ndarray, Dict[str, int], Dict]:
    arr = np.load(os.path.join(aligned_dir, "aligned_u8.npy"))
    idx = pd.read_csv(os.path.join(aligned_dir, "index.csv"))
    if arr.dtype != np.uint8 or arr.shape[1:] != (3, 112, 112) or len(idx) != arr.shape[0]:
        raise SystemExit("DỪNG — aligned_u8.npy/index.csv sai định dạng")
    info = {"n_images": int(arr.shape[0]), "aligned_sha256": sha256_file(os.path.join(aligned_dir, "aligned_u8.npy"))}
    s = os.path.join(aligned_dir, "align_summary.json")
    if os.path.isfile(s):
        info["align_summary"] = load_json(s)
    return arr, {n: i for i, n in enumerate(idx.image)}, info


def check_split_dir(split_dir: str, image_index: Dict[str, int]) -> Dict:
    """sha256 từng split = manifest.json của data_splits; đếm ảnh thiếu (phải = 0)."""
    man = load_json(os.path.join(split_dir, "manifest.json"))["splits"]
    rep = {}
    for fn, st in sorted(man.items()):
        p = os.path.join(split_dir, fn)
        sha = sha256_file(p)
        df = pd.read_csv(p)
        miss = int((~df.image.isin(image_index.keys())).sum())
        rep[fn] = {"sha256_ok": sha == st["sha256"], "n_images": int(len(df)), "n_missing_images": miss}
        if sha != st["sha256"]:
            raise SystemExit(f"DỪNG — {fn}: sha256 lệch manifest data_splits")
        if miss:
            raise SystemExit(f"DỪNG — {fn}: n_missing_images = {miss}")
    return rep
