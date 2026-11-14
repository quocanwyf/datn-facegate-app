"""Cấu hình YAML: mặc định ← file YAML ← ghi đè dòng lệnh (--set train.lr=0.05 head.m=0.4)."""
from __future__ import annotations

import copy
from typing import Any, Dict, List

import yaml

DEFAULTS: Dict[str, Any] = {
    "run_name": "run",
    "seed": 42,
    "output_dir": "./runs",
    "data": {"type": "rec", "root": None, "num_workers": 4,   # num_workers = TỔNG mọi GPU (DDP chia đều)
             "workers_per_rank": None, "prewarm": False,      # prewarm: đọc tuần tự train.rec vào page cache trước khi train
             # val: tách theo DANH TÍNH (fr/data/casia_split.py). ids_file None → sinh lại tất định từ (frac, seed);
             # ids_sha256 (nếu ghi) bắt buộc khớp → mọi run dùng đúng một tập val.
             "val": {"enabled": False, "ids_file": None, "ids_sha256": None, "frac": 0.05, "seed": 2026, "max_per_id": 10},
             "num_images": 256, "num_classes": 16, "size": 112},          # 3 khoá cuối chỉ cho type=synthetic
    "eval": {"bin_dir": None, "bins": ["lfw", "cfp_fp", "agedb_30", "calfw", "cplfw"],
             "every_epochs": 1, "at_end": True, "batch_size": 256,          # .bin = TEST: chỉ để báo cáo, không chọn gì
             "val_every_epochs": 1, "best_metric": "tar@far=0.001"},        # validation CASIA → best.pt
    "model": {"backbone": "r18", "emb_dim": 512, "dropout": 0.0},
    "head": {"name": "arcface", "s": 64.0, "m": 0.5, "lam": 1.0, "r": 1.0, "margin_type": "cos",
             "clamp": True, "w_init_std": 0.01},
    # global_batch: batch hiệu dụng TOÀN CỤC (mọi GPU). None → = micro_batch × accum_steps (cách ghi bản pilot).
    "train": {"global_batch": None, "micro_batch": 128, "accum_steps": 4, "epochs": 28, "lr": 0.1, "lr_steps": [16, 24],
              "lr_gamma": 0.1, "warmup_epochs": 0, "momentum": 0.9, "weight_decay": 5.0e-4,
              "clip_grad": 5.0, "amp": True, "max_iters": None, "log_every": 20,
              "ckpt_every_iters": 500, "save_epoch_ckpt": True, "deterministic": False, "device": "auto"},
}


def _merge(base: dict, upd: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _parse_value(s: str):
    return yaml.safe_load(s)


def load_config(path: str = None, overrides: List[str] = None) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            cfg = _merge(cfg, yaml.safe_load(f) or {})
    for item in overrides or []:
        key, val = item.split("=", 1)
        node = cfg
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = _parse_value(val)
    return cfg


# Khoá KHÔNG ảnh hưởng tới kết quả (đường dẫn máy, số worker, tần suất log/ghi checkpoint...) → bỏ khi tính
# fingerprint. Mọi khoá còn lại (seed, head, lịch LR, batch, val, epoch, max_iters...) đều nằm trong fingerprint.
# Số worker không ảnh hưởng vì cờ lật ảnh do sampler quyết định (B3). Số GPU (1 vs DDP 2) không nằm trong config;
# ghi ở run_info.json["world_size"] (tương đương thống kê — README B3).
NON_SCIENCE_KEYS = [("run_name",), ("output_dir",), ("data", "root"), ("data", "num_workers"),
                    ("data", "workers_per_rank"), ("data", "prewarm"), ("data", "val", "ids_file"),
                    ("eval", "bin_dir"), ("eval", "batch_size"), ("train", "device"), ("train", "log_every"),
                    ("train", "ckpt_every_iters"), ("train", "save_epoch_ckpt")]


def science_view(cfg: dict) -> dict:
    out = copy.deepcopy(cfg)
    for path in NON_SCIENCE_KEYS:
        node = out
        for k in path[:-1]:
            node = node.get(k, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict):
            node.pop(path[-1], None)
    return out


def config_fingerprint(cfg: dict) -> str:
    """sha256 của phần cấu hình ảnh hưởng tới kết quả (dùng để kiểm 'config đóng băng')."""
    import hashlib
    import json
    return hashlib.sha256(json.dumps(science_view(cfg), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def code_fingerprint(root: str) -> str:
    """sha256 của mã nguồn ảnh hưởng tới train: train.py + fr/**/*.py (không tính tools/, tests/)."""
    import hashlib
    import os
    h = hashlib.sha256()
    files = [os.path.join(root, "train.py")]
    for d, _, fs in os.walk(os.path.join(root, "fr")):
        files += [os.path.join(d, f) for f in fs if f.endswith(".py")]
    for f in sorted(files, key=lambda p: os.path.relpath(p, root).replace(os.sep, "/")):
        h.update(os.path.relpath(f, root).replace(os.sep, "/").encode())
        with open(f, "rb") as fh:
            h.update(fh.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def dump_config(cfg: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
