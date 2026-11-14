"""Đánh giá open-set 1:N + 1:1 FAR thấp trên các split LFW (protocol A tự dựng, BLUFR) — xem fr/eval/lfw_protocol.py.

Nguyên tắc: TÁI DÙNG hàm tính metric của code tham chiếu insightface (đã chép nguyên ở fr/eval/ijbc.py), không viết
thuật toán metric mới:
  - 1:N open-set : ``ijbc.evaluation_1N`` ([R2] ijb_evals.py) — TPIR@FPIR, rank-1/5/10. Mỗi người trong gallery là
                   một template (``ijbc.image2template_feature_1N``: cộng đặc trưng các ảnh rồi chuẩn hoá L2 — ở đây
                   1 ảnh/người nên template = chính ảnh đó). Mỗi probe là 1 template.
  - 1:1 FAR thấp : ``ijbc.safe_tpr_at_fpr`` → ``ijbc.tpr_at_fpr_table`` ([R1] eval_ijbc.py, roc_curve).
  - Tại ngưỡng t : ``metrics.rates_at_threshold`` (đã unit test ở B0) — FNIR/FPIR (1:N) và TAR/FAR (1:1),
                   để kiểm tra ngưỡng học được của UniFace (t = b/s) có dùng trực tiếp làm ngưỡng cổng được không.

Cách lập cặp 1:1:
  - ``gallery_probe`` (protocol A): mọi cặp (ảnh gallery, ảnh probe) — dương khi cùng người.
  - ``all_pairs`` (BLUFR, theo EvalROC.m): mọi cặp không thứ tự trong tập test (= gallery ∪ probe), tam giác dưới.
In ra số cặp dương/âm và FAR nhỏ nhất đo được = 1/số cặp âm. FAR có ý nghĩa thống kê cần nhiều hơn 1 cặp âm
vượt ngưỡng; quy ước báo cáo đề xuất [ngoài nguồn]: chỉ báo FAR ≥ 10/số cặp âm (``far_floor_10``).
Đối với 1:N: FPIR nhỏ nhất đo được = 1/số probe người lạ.
"""
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from .ijbc import DEFAULT_FPRS_11, evaluation_1N, image2template_feature_1N, safe_tpr_at_fpr
from .lfw_protocol import check_split
from .metrics import l2_normalize, rates_at_threshold

DEFAULT_FPIRS = (1e-3, 1e-2, 1e-1)


def _codes(identities: Sequence[str], vocab: Dict[str, int]) -> np.ndarray:
    return np.array([vocab.setdefault(i, len(vocab)) for i in identities], dtype=np.int64)


def evaluate_split(feats: np.ndarray, image_index: Dict[str, int], split: pd.DataFrame,
                   pair_mode: str = "gallery_probe", fpirs: Sequence[float] = DEFAULT_FPIRS,
                   fars: Sequence[float] = DEFAULT_FPRS_11, threshold: Optional[float] = None,
                   pair_chunk: int = 2048) -> Dict[str, object]:
    """``feats``: (N, d) đặc trưng ảnh (đã cộng ảnh lật + chuẩn hoá L2 — như evaluate .bin);
    ``image_index``: tên ảnh → hàng trong feats. Ảnh không có trong index (vd. lỗi đọc) bị bỏ và được đếm."""
    check_split(split)
    present = split.image.map(lambda x: x in image_index)
    n_missing = int((~present).sum())
    df = split[present].reset_index(drop=True)
    vocab: Dict[str, int] = {}
    g, pk, pu = (df[df.role == r] for r in ("gallery", "probe_known", "probe_unknown"))
    gf = feats[[image_index[x] for x in g.image]]
    g_ids = _codes(g.identity, vocab)
    pf = feats[[image_index[x] for x in pd.concat([pk.image, pu.image])]]
    p_ids = _codes(pd.concat([pk.identity, pu.identity]), vocab)
    n_known, n_unknown = len(pk), len(pu)

    # ---- 1:N open-set: tái dùng [R2] ----
    # template gallery theo người (mỗi ảnh là một "media" riêng) — đúng cách [R2] dựng template
    g_feats, _, g_unique_ids = image2template_feature_1N(gf, templates=g_ids, medias=np.arange(len(g_ids)),
                                                         choose_templates=g_ids, choose_ids=g_ids)
    p_feats = l2_normalize(pf.astype(np.float64))
    top1, top5, top10, threshes, recalls, _, n_counts = evaluation_1N(p_feats, g_feats, p_ids, g_unique_ids, list(fpirs))
    res: Dict[str, object] = {"n_missing_images": n_missing, "n_gallery_ids": int(len(g_unique_ids)),
                              "n_probe_known": n_known, "n_probe_unknown": n_unknown,
                              "rank1": top1 / max(n_counts["n_mated"], 1), "rank5": top5 / max(n_counts["n_mated"], 1),
                              "min_measurable_fpir": 1.0 / n_unknown if n_unknown else float("nan")}
    for f, t, r in zip(fpirs, threshes, recalls):
        ok = f * n_unknown >= 1
        res[f"tpir@fpir={f:g}"] = float(r) if ok else float("nan")
        res[f"thr@fpir={f:g}"] = float(t) if ok else float("nan")

    # ---- 1:1: tái dùng [R1] ----
    if pair_mode == "gallery_probe":
        scores = (p_feats @ g_feats.T)                          # (P, G)
        labels = (p_ids[:, None] == g_unique_ids[None, :])
        scores, labels = scores.ravel(), labels.ravel()
    elif pair_mode == "all_pairs":
        allf = l2_normalize(feats[[image_index[x] for x in df.image]].astype(np.float32))
        all_ids = _codes(df.identity, vocab)
        sc, lb = [], []
        for i0 in range(0, len(allf), pair_chunk):
            blk = allf[i0:i0 + pair_chunk] @ allf.T                       # (b, N)
            ii = np.arange(i0, min(i0 + pair_chunk, len(allf)))[:, None]
            mask = np.arange(len(allf))[None, :] < ii                     # tam giác dưới (j < i), như EvalROC.m
            sc.append(blk[mask])
            lb.append((all_ids[ii] == all_ids[None, :])[mask])
        scores, labels = np.concatenate(sc), np.concatenate(lb)
    else:
        raise ValueError(pair_mode)
    r11 = safe_tpr_at_fpr(labels.astype(int), scores, fars)
    r11["far_floor_10"] = 10.0 / r11["n_neg"] if r11["n_neg"] else float("nan")
    res["1:1"] = r11

    # ---- tại ngưỡng cố định t ----
    if threshold is not None:
        known = np.isin(p_ids, g_unique_ids)
        z = rates_at_threshold(threshold, scores=scores, issame=labels.astype(bool), gallery=g_feats,
                               gallery_ids=g_unique_ids, probe_known=p_feats[known], probe_known_ids=p_ids[known],
                               probe_unknown=p_feats[~known])
        res["at_threshold"] = z
    return res


def summarize(results: List[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    """mean ± std (độ lệch chuẩn mẫu, ddof=1) qua các split cho mọi chỉ số số học."""
    flat: Dict[str, List[float]] = {}
    for r in results:
        for k, v in r.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, (int, float, np.floating)):
                        flat.setdefault(f"{k}/{k2}", []).append(float(v2))
            elif isinstance(v, (int, float, np.floating)):
                flat.setdefault(k, []).append(float(v))
    out = {}
    for k, vs in flat.items():
        a = np.asarray(vs, dtype=float)
        out[k] = {"mean": float(np.nanmean(a)) if np.isfinite(a).any() else float("nan"),
                  "std": float(np.nanstd(a, ddof=1)) if np.isfinite(a).sum() > 1 else float("nan"),
                  "n": int(np.isfinite(a).sum())}
    return out


def evaluate_openset(feats: np.ndarray, image_index: Dict[str, int], split_dir: str, pair_mode: str,
                     threshold: Optional[float] = None, fpirs: Sequence[float] = DEFAULT_FPIRS,
                     fars: Sequence[float] = DEFAULT_FPRS_11, log=print) -> Dict[str, object]:
    """Chạy mọi file ``split_*.csv`` trong ``split_dir``; trả kết quả từng split + mean ± std."""
    files = sorted(f for f in os.listdir(split_dir) if f.startswith("split_") and f.endswith(".csv"))
    per = {}
    for fn in files:
        df = pd.read_csv(os.path.join(split_dir, fn))
        r = evaluate_split(feats, image_index, df, pair_mode, fpirs, fars, threshold)
        per[fn] = r
        log(f"{fn}: gallery={r['n_gallery_ids']} known={r['n_probe_known']} unknown={r['n_probe_unknown']} "
            f"| 1:1 pos={r['1:1']['n_pos']} neg={r['1:1']['n_neg']} minFAR={r['1:1']['min_measurable_far']:.2e} "
            f"| minFPIR={r['min_measurable_fpir']:.2e}")
    return {"per_split": per, "summary": summarize(list(per.values())), "pair_mode": pair_mode}


def evaluate_ijbc_1to1(*args, **kwargs):
    """Giữ tên cũ (B0) cho tương thích — IJB-C nay ở fr/eval/ijbc.py."""
    from .ijbc import evaluate_ijbc
    return evaluate_ijbc(*args, **kwargs)
