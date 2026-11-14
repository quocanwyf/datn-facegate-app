"""Metric đánh giá — thuần numpy, dùng chung cho .bin, IJB-C 1:1 và open-set 1:N.

* verification_accuracy_10fold: giao thức LFW/insightface — 10 fold liên tiếp (không xáo), chọn ngưỡng
  tốt nhất trên 9 fold, đo trên fold còn lại; khoảng cách = ||e1 − e2||² của embedding đã chuẩn hoá,
  ngưỡng 0..4 bước 0.01 (theo insightface arcface_torch/eval/verification.py, calculate_roc).
* tar_at_far: TAR tại FAR cho trước trên toàn bộ cặp (score = cosine, càng lớn càng giống).
  Trả NaN nếu FAR·(số cặp âm) < 1 — tức FAR đó không đo được với số cặp hiện có.
* tpir_at_fpir: open-set identification 1:N (kiểu IJB-C 1:N): probe người lạ quyết định ngưỡng theo FPIR;
  TPIR = tỉ lệ probe đã đăng ký có rank-1 đúng VÀ điểm ≥ ngưỡng.
* rates_at_threshold: FNIR/FPIR (1:N) hoặc TAR/FAR (1:1) tại một ngưỡng cố định (vd. ngưỡng t học được).
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

import numpy as np


def l2_normalize(x: np.ndarray, axis: int = 1) -> np.ndarray:
    return x / np.clip(np.linalg.norm(x, axis=axis, keepdims=True), 1e-12, None)


def verification_accuracy_10fold(emb1: np.ndarray, emb2: np.ndarray, issame: np.ndarray, n_folds: int = 10) -> Dict[str, float]:
    emb1, emb2 = l2_normalize(emb1), l2_normalize(emb2)
    dist = np.sum((emb1 - emb2) ** 2, axis=1)
    thresholds = np.arange(0, 4, 0.01)
    n = len(issame)
    folds = np.array_split(np.arange(n), n_folds)
    accs, best_ths = [], []
    for k in range(n_folds):
        test = folds[k]
        train = np.concatenate([folds[j] for j in range(n_folds) if j != k])
        acc_train = [np.mean((dist[train] < t) == issame[train]) for t in thresholds]
        t_best = thresholds[int(np.argmax(acc_train))]
        accs.append(np.mean((dist[test] < t_best) == issame[test]))
        best_ths.append(t_best)
    accs = np.asarray(accs)
    # ngưỡng khoảng cách d ↔ cosine: d = 2 − 2cos → cos = 1 − d/2
    return {"acc": float(accs.mean()), "acc_std": float(accs.std()),
            "best_cos_threshold_mean": float(1 - np.mean(best_ths) / 2)}


def tar_at_far(scores: np.ndarray, issame: np.ndarray, fars: Iterable[float] = (1e-2, 1e-3)) -> Dict[str, float]:
    scores = np.asarray(scores, dtype=np.float64)
    issame = np.asarray(issame, dtype=bool)
    pos, neg = scores[issame], np.sort(scores[~issame])[::-1]
    out = {"n_pos": int(pos.size), "n_neg": int(neg.size)}
    for far in fars:
        key = f"tar@far={far:g}"
        if far * neg.size < 1:
            out[key] = float("nan")          # không đủ cặp âm để đo FAR này
            continue
        k = int(np.floor(far * neg.size))     # cho phép tối đa k cặp âm vượt ngưỡng
        thr = neg[k] if k < neg.size else neg[-1] - 1e-12
        out[key] = float(np.mean(pos > thr))
        out[f"thr@far={far:g}"] = float(thr)
    return out


def _gallery_scores(probe: np.ndarray, gallery: np.ndarray, gallery_ids: np.ndarray):
    """Điểm cosine probe×ID (lấy max nếu một ID có nhiều ảnh gallery)."""
    probe, gallery = l2_normalize(probe), l2_normalize(gallery)
    s = probe @ gallery.T
    ids = np.unique(gallery_ids)
    S = np.full((probe.shape[0], ids.size), -np.inf)
    for j, gid in enumerate(ids):
        S[:, j] = s[:, gallery_ids == gid].max(axis=1)
    return S, ids


def tpir_at_fpir(gallery: np.ndarray, gallery_ids: np.ndarray, probe_known: np.ndarray, probe_known_ids: np.ndarray,
                 probe_unknown: np.ndarray, fpirs: Iterable[float] = (1e-2, 1e-1)) -> Dict[str, float]:
    Sk, ids = _gallery_scores(probe_known, gallery, gallery_ids)
    Su, _ = _gallery_scores(probe_unknown, gallery, gallery_ids)
    top_k = Sk.max(axis=1)
    correct = ids[Sk.argmax(axis=1)] == probe_known_ids
    unk_max = np.sort(Su.max(axis=1))[::-1]
    out = {"rank1": float(correct.mean()), "n_known": int(len(top_k)), "n_unknown": int(len(unk_max))}
    for f in fpirs:
        key = f"tpir@fpir={f:g}"
        if f * unk_max.size < 1:
            out[key] = float("nan")
            continue
        k = int(np.floor(f * unk_max.size))
        thr = unk_max[k] if k < unk_max.size else unk_max[-1] - 1e-12
        out[key] = float(np.mean(correct & (top_k > thr)))
        out[f"thr@fpir={f:g}"] = float(thr)
    return out


def rates_at_threshold(threshold: float, *, scores: Optional[np.ndarray] = None, issame: Optional[np.ndarray] = None,
                       gallery=None, gallery_ids=None, probe_known=None, probe_known_ids=None, probe_unknown=None) -> Dict[str, float]:
    """Tại ngưỡng cosine cố định: 1:1 → TAR/FAR ; 1:N → FNIR/FPIR."""
    out: Dict[str, float] = {"threshold": float(threshold)}
    if scores is not None:
        scores, issame = np.asarray(scores), np.asarray(issame, dtype=bool)
        out["tar"] = float(np.mean(scores[issame] > threshold))
        out["far"] = float(np.mean(scores[~issame] > threshold))
    if gallery is not None:
        Sk, ids = _gallery_scores(probe_known, gallery, gallery_ids)
        Su, _ = _gallery_scores(probe_unknown, gallery, gallery_ids)
        correct = (ids[Sk.argmax(axis=1)] == probe_known_ids) & (Sk.max(axis=1) > threshold)
        out["fnir"] = float(1 - correct.mean())
        out["fpir"] = float(np.mean(Su.max(axis=1) > threshold))
    return out
