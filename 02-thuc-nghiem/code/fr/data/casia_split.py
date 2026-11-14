"""Tách CASIA-WebFace theo DANH TÍNH: ~95% danh tính để train, ~5% danh tính làm validation (B3, theo mentor).

Vì sao theo danh tính (không theo ảnh): bài toán là 1:N open-set → mô hình phải nhận/so khớp người CHƯA thấy
lúc train. Validation gồm những người không xuất hiện trong tập train, giống điều kiện test (LFW/BLUFR/IJB-C).
Validation dùng để: theo dõi hội tụ mỗi epoch, chọn checkpoint "best", chọn siêu tham số (vd. m của CosFace).
Tập test (.bin, BLUFR, IJB-C) KHÔNG được dùng cho bất kỳ lựa chọn nào.

Quy trình (tất định, giống nhau cho MỌI run):
  1. ``make_val_ids(num_classes, frac, seed)`` — chọn round(frac·N) nhãn làm validation bằng
     torch.randperm(seed). Không cần đọc dữ liệu → danh sách lưu được trước:
     ``02-thuc-nghiem/data_splits/casia_val/val_ids.csv`` (+ manifest.json với sha256).
  2. ``scan_labels`` — đọc NHÃN của mọi ảnh (chỉ header record, không giải mã ảnh).
  3. ``build_split`` — ảnh thuộc nhãn val → tập ảnh validation (tối đa ``max_per_id`` ảnh/người, chọn tất
     định theo seed, cần ≥ 2 ảnh để có cặp dương); ảnh còn lại → train, nhãn đánh lại liên tục 0..N_train−1.
     Ảnh của người val vượt quá max_per_id bị BỎ (không vào train) → train và val không chung danh tính.
  4. Cặp verification = MỌI cặp (i < j) trong tập ảnh validation: cùng nhãn → cặp dương, khác nhãn → cặp âm.
     Với ~529 người × ≤10 ảnh ≈ 5k ảnh → ~1.3·10⁷ cặp âm, đủ đo TAR@FAR = 1e-3 (và 1e-4, 1e-5) ổn định
     (tại FAR 1e-3 có ~1.3·10⁴ cặp âm vượt ngưỡng).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import struct
from typing import Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import Dataset

from .recordio import _IR_FORMAT, _IR_SIZE, _MAGIC

DEFAULT_FRAC = 0.05
DEFAULT_SEED = 2026          # seed RIÊNG cho việc tách (độc lập seed train s1/s2)
DEFAULT_MAX_PER_ID = 10


def make_val_ids(num_classes: int, frac: float = DEFAULT_FRAC, seed: int = DEFAULT_SEED) -> List[int]:
    n_val = int(round(frac * num_classes))
    g = torch.Generator().manual_seed(int(seed))
    return sorted(torch.randperm(num_classes, generator=g)[:n_val].tolist())


def ids_sha256(ids: List[int]) -> str:
    return hashlib.sha256(",".join(map(str, sorted(ids))).encode()).hexdigest()


def write_val_ids(out_dir: str, num_classes: int, frac: float = DEFAULT_FRAC, seed: int = DEFAULT_SEED) -> dict:
    ids = make_val_ids(num_classes, frac, seed)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "val_ids.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label"])
        w.writerows([[i] for i in ids])
    man = {"what": "CASIA-WebFace (insightface faces_webface_112x112) — nhãn (danh tính) dành cho validation",
           "num_classes_total": num_classes, "frac": frac, "seed": seed, "n_val_ids": len(ids),
           "n_train_ids": num_classes - len(ids), "max_per_id": DEFAULT_MAX_PER_ID,
           "method": "sorted(torch.randperm(num_classes, generator=manual_seed(seed))[:round(frac*num_classes)])",
           "val_ids_sha256": ids_sha256(ids), "code": "fr/data/casia_split.py"}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)
    return man


def read_val_ids(path: str) -> List[int]:
    with open(path, newline="") as f:
        return sorted(int(r["label"]) for r in csv.DictReader(f))


def scan_labels(rec_dataset) -> np.ndarray:
    """Nhãn của từng ảnh trong RecordFaceDataset — chỉ đọc 8 + 24 byte header mỗi record (nhanh, không giải mã)."""
    reader = rec_dataset.reader
    labels = np.empty(len(rec_dataset), dtype=np.int64)
    with open(reader.rec_path, "rb") as fh:
        for i, key in enumerate(rec_dataset.imgidx):
            fh.seek(reader.offsets[int(key)])
            magic, _ = struct.unpack("<II", fh.read(8))
            if magic != _MAGIC:
                raise IOError(f"sai magic tại khoá {key}")
            flag, label, _, _ = struct.unpack(_IR_FORMAT, fh.read(_IR_SIZE))
            if flag > 0:   # nhãn dạng mảng: phần tử đầu
                label = struct.unpack("<f", fh.read(4))[0]
            labels[i] = int(label)
    return labels


def build_split(labels: np.ndarray, val_ids: List[int], max_per_id: int = DEFAULT_MAX_PER_ID,
                seed: int = DEFAULT_SEED) -> Dict[str, np.ndarray]:
    """→ train_pos, train_labels (đánh lại 0..N_train−1), val_pos, val_labels (nhãn GỐC), dropped_pos, label_map."""
    labels = np.asarray(labels, dtype=np.int64)
    val_set = np.zeros(int(labels.max()) + 1 if labels.size else 0, dtype=bool)
    val_set[[v for v in val_ids if v < val_set.size]] = True
    is_val = val_set[labels]
    train_pos = np.nonzero(~is_val)[0]
    train_old = labels[train_pos]
    uniq = np.unique(train_old)
    label_map = -np.ones(val_set.size, dtype=np.int64)
    label_map[uniq] = np.arange(uniq.size)
    g = np.random.default_rng(int(seed))
    val_pos, dropped = [], []
    for v in sorted(val_ids):
        pos = np.nonzero(labels == v)[0]
        if pos.size < 2:
            dropped.extend(pos.tolist())
            continue
        pick = np.sort(g.permutation(pos)[:max_per_id])
        val_pos.extend(pick.tolist())
        dropped.extend(sorted(set(pos.tolist()) - set(pick.tolist())))
    val_pos = np.asarray(val_pos, dtype=np.int64)
    return {"train_pos": train_pos, "train_labels": label_map[train_old], "num_train_classes": int(uniq.size),
            "val_pos": val_pos, "val_labels": labels[val_pos], "dropped_pos": np.asarray(dropped, dtype=np.int64),
            "label_map": label_map}


def split_summary(sp: Dict[str, np.ndarray]) -> dict:
    n = sp["val_pos"].size
    _, counts = np.unique(sp["val_labels"], return_counts=True)
    n_pos = int(np.sum(counts * (counts - 1) // 2))
    return {"n_train_images": int(sp["train_pos"].size), "n_train_classes": sp["num_train_classes"],
            "n_val_images": int(n), "n_val_ids_used": int(counts.size), "n_val_dropped_images": int(sp["dropped_pos"].size),
            "n_val_pairs_pos": n_pos, "n_val_pairs_neg": int(n * (n - 1) // 2 - n_pos),
            "val_images_sha256": hashlib.sha256(sp["val_pos"].tobytes()).hexdigest()}


def write_val_images(path: str, rec_dataset, sp: Dict[str, np.ndarray]):
    """Danh sách ảnh validation: vị trí trong dataset, khoá record, nhãn gốc."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pos", "rec_key", "label"])
        for p, l in zip(sp["val_pos"], sp["val_labels"]):
            w.writerow([int(p), int(rec_dataset.imgidx[int(p)]), int(l)])


class RelabeledSubset(Dataset):
    """Tập con của dataset gốc với nhãn đánh lại (train). Hỗ trợ chỉ số (i, cờ_lật) từ EpochSampler."""

    def __init__(self, base, positions: np.ndarray, new_labels: np.ndarray, num_classes: int):
        self.base, self.positions, self.new_labels = base, np.asarray(positions), np.asarray(new_labels)
        self.num_classes = int(num_classes)

    def __len__(self):
        return len(self.positions)

    def __getitem__(self, i):
        if isinstance(i, (tuple, list)):
            j, flip = int(i[0]), bool(i[1])
            x, _ = self.base[(int(self.positions[j]), flip)]
        else:
            j = int(i)
            x, _ = self.base[int(self.positions[j])]
        return x, int(self.new_labels[j])


def resolve_val_ids(vcfg: dict, num_classes: int) -> List[int]:
    """Đọc val_ids.csv nếu có; nếu không, sinh lại tất định. Luôn kiểm sha256 với config (nếu config ghi)."""
    frac, seed = float(vcfg.get("frac", DEFAULT_FRAC)), int(vcfg.get("seed", DEFAULT_SEED))
    path: Optional[str] = vcfg.get("ids_file")
    ids = read_val_ids(path) if path and os.path.exists(path) else make_val_ids(num_classes, frac, seed)
    want = vcfg.get("ids_sha256")
    got = ids_sha256(ids)
    if want and want != got:
        raise ValueError(f"danh sách ID validation khác bản đã chốt (sha256 {got[:12]} ≠ {want[:12]}) — "
                         f"kiểm tra data_splits/casia_val/ hoặc num_classes={num_classes}")
    return ids
