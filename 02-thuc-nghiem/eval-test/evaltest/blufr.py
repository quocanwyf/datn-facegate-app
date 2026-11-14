"""Bước 3a — BLUFR (Liao, Lei, Yi, Li — IJCB 2014) trên LFW, 10 trial. Bản Python CHÉP THEO TỪNG DÒNG
``third_party/blufr/EvalROC.m`` và ``OpenSetROC.m`` (toolkit v1.0, 2014-07-22).

Vì sao không dùng ``fr/eval/openset.py`` cho BLUFR: hàm đó dùng quy ước insightface (ngưỡng ở người lạ thứ
int(N·FPIR)−1, so ``>``; TAR theo roc_curve "FPR gần nhất" — review 04 M1/M2), KHÁC quy ước của toolkit BLUFR
(``falseAlarms = round(FAR·Nimp)``, ngưỡng = điểm âm thứ falseAlarms, so ``>=``). Chỉ số chính phải theo đúng
giao thức BLUFR → port nguyên văn và đối chiếu với chính file .m bằng Octave (tests/test_blufr_octave.py).

Chi tiết giữ nguyên của .m:
  * ``round`` của MATLAB = làm tròn nửa ra xa 0 (numpy.round là làm tròn về chẵn → KHÔNG dùng).
  * FAR = 0: ngưỡng = (điểm âm lớn nhất + điểm dương nhỏ nhất còn lớn hơn nó)/2, hoặc + sqrt(eps).
  * FAR = 1: ngưỡng = min(điểm âm nhỏ nhất, điểm dương nhỏ nhất) − sqrt(eps).
  * sort 'descend' của MATLAB là ổn định (giữ thứ tự gốc khi bằng nhau); max trả chỉ số ĐẦU TIÊN.
  * Ma trận điểm: hàng = gallery, cột = probe. EvalROC không nhãn probe → ma trận vuông, tam giác dưới (−1).
Báo theo README BLUFR: VR@FAR=0,1% và DIR@FAR=1%, rank 1; "report the (mu − sigma) performance". σ = độ lệch chuẩn
mẫu (MATLAB ``std``, chia N−1).
"""
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

SQRT_EPS = float(np.sqrt(np.finfo(np.float64).eps))      # MATLAB sqrt(eps)

# chỉ số báo cáo (nhật ký Buổi 44): chính = DIR rank-1 @FAR 1% (= TPIR@FPIR 1e-2); KHÔNG báo FPIR 1e-3
OPEN_FARS = (0.01, 0.1)
VERIF_FARS = (1e-3, 1e-4)


def matlab_round(x):
    x = np.asarray(x, dtype=np.float64)
    return (np.sign(x) * np.floor(np.abs(x) + 0.5)).astype(np.int64)


def _thresholds(kth_desc, imp_max: float, imp_min: float, gen_score: np.ndarray, false_alarms: np.ndarray, n_imp: int):
    """Khối 'compute thresholds' — giống hệt ở EvalROC.m và OpenSetROC.m.
    ``kth_desc(ks)`` trả impScore(ks) (1-based, sắp giảm dần)."""
    is_zero = false_alarms == 0
    is_one = false_alarms == n_imp
    thr = np.zeros(len(false_alarms), dtype=np.float64)
    mid = ~is_zero & ~is_one
    if mid.any():
        thr[mid] = kth_desc(false_alarms[mid])                      # impScore(falseAlarms)
    high = gen_score[gen_score > imp_max]
    thr[is_zero] = imp_max + SQRT_EPS if high.size == 0 else (imp_max + high.min()) / 2
    thr[is_one] = min(imp_min, gen_score.min()) - SQRT_EPS
    return thr


def _kth_desc_sorted(imp_sorted_desc):
    return lambda ks: imp_sorted_desc[np.asarray(ks) - 1]


def _kth_desc_partition(imp):
    """Phần tử lớn thứ k (1-based) bằng np.partition — CÙNG giá trị với sort giảm dần rồi lấy (k−1), nhanh hơn
    nhiều với ~47 triệu điểm âm/trial (chỉ cần vài mức FAR)."""
    n = imp.size

    def f(ks):
        ks = np.asarray(ks)
        idx = n - ks                                                # vị trí trong thứ tự TĂNG dần
        part = np.partition(imp, np.unique(idx))
        return part[idx]
    return f


def _false_alarms(far_points: Optional[Sequence[float]], n_imp: int) -> np.ndarray:
    if far_points is None:
        return np.arange(0, n_imp + 1)
    fp = np.asarray(far_points, dtype=np.float64)
    if (fp < 0).any() or (fp > 1).any():
        raise ValueError("FAR should be in the range [0,1].")
    return matlab_round(fp * n_imp)


def eval_roc_scores(gen_score: np.ndarray, imp_score: np.ndarray, far_points: Optional[Sequence[float]] = None,
                    fast: bool = True):
    """Phần sau khi đã tách genScore/impScore của EvalROC.m → (VR, FAR, thresholds).
    ``fast``: lấy điểm âm thứ k bằng np.partition (giá trị y hệt sort; tests kiểm hai đường bằng nhau)."""
    gen = np.asarray(gen_score, dtype=np.float64).ravel()
    imp = np.asarray(imp_score, dtype=np.float64).ravel()
    n_imp = imp.size
    fa = _false_alarms(far_points, n_imp)
    kth = _kth_desc_partition(imp) if fast else _kth_desc_sorted(-np.sort(-imp, kind="stable"))
    thr = _thresholds(kth, float(imp.max()), float(imp.min()), gen, fa, n_imp)
    vr = np.array([np.count_nonzero(gen >= t) for t in thr], dtype=np.float64) / gen.size   # mean(genScore >= thr)
    return vr, fa / n_imp, thr


def eval_roc(score: np.ndarray, gal_labels, prob_labels=None, far_points=None):
    """EvalROC.m: ``score`` hàng = gallery, cột = probe. prob_labels rỗng → ma trận vuông, tam giác dưới (−1)."""
    score = np.asarray(score, dtype=np.float64)
    gal = np.asarray(gal_labels).ravel()
    if prob_labels is None or len(prob_labels) == 0:
        prob = gal
        mask = np.tril(np.ones(score.shape, dtype=bool), -1)
    else:
        prob, mask = np.asarray(prob_labels).ravel(), None
    binary = gal[:, None] == prob[None, :]
    if score.shape != binary.shape:
        raise ValueError("The size of labels is not the same as the size of the score matrix.")
    if mask is not None:
        # MATLAB score(scoreMask) lấy theo thứ tự cột (Fortran) — giữ đúng thứ tự cho trọn vẹn
        s, b = score.T[mask.T], binary.T[mask.T]
    else:
        s, b = score.ravel(order="F"), binary.ravel(order="F")
    return eval_roc_scores(s[b], s[~b], far_points)


def _open_set_scores(score: np.ndarray, gal: np.ndarray, prob: np.ndarray):
    """Phần 'get detection scores and matching ranks' của OpenSetROC.m → (impScore sắp giảm, genScore, probRanks)."""
    binary = gal[:, None] == prob[None, :]
    t = binary.any(axis=0)
    gen_idx, imp_idx = np.flatnonzero(t), np.flatnonzero(~t)
    n_gen = gen_idx.size
    imp_score = -np.sort(-score[:, imp_idx].max(axis=0), kind="stable")
    S = score[:, gen_idx]
    sorted_index = np.argsort(-S, axis=0, kind="stable")                  # sort(S,'descend') ổn định
    S = np.where(binary[:, gen_idx], S, -np.inf)
    gen_gal_index = S.argmax(axis=0)                                       # chỉ số đầu tiên của max
    gen_score = S[gen_gal_index, np.arange(n_gen)]
    prob_ranks = 1 + np.argmax(sorted_index == gen_gal_index[None, :], axis=0)   # hàng (1-based) chứa match
    return imp_score, gen_score, prob_ranks


def open_set_at_threshold(score: np.ndarray, gal_labels, prob_labels, thresholds: Sequence[float]) -> Dict:
    """CH2 — tỉ lệ tại NGƯỠNG CỐ ĐỊNH (không lấy từ test), cùng luật quyết định với OpenSetROC.m:
    người lạ bị nhận nhầm khi điểm max ``>=`` ngưỡng → FPIR = tỉ lệ đó;
    người đã đăng ký đúng khi rank-1 đúng VÀ điểm match ``>=`` ngưỡng → FNIR (rank-1) = 1 − tỉ lệ đó (= 1 − DIR rank 1)."""
    imp_score, gen_score, prob_ranks = _open_set_scores(np.asarray(score, np.float64), np.asarray(gal_labels).ravel(),
                                                        np.asarray(prob_labels).ravel())
    thr = np.asarray(thresholds, dtype=np.float64).ravel()
    fpir = (imp_score[:, None] >= thr[None, :]).mean(axis=0)
    hit = (gen_score[:, None] >= thr[None, :]) & (prob_ranks[:, None] == 1)
    return {"fpir": fpir, "fnir": 1.0 - hit.mean(axis=0), "n_imp": int(imp_score.size), "n_gen": int(gen_score.size)}


def open_set_roc(score: np.ndarray, gal_labels, prob_labels, far_points=None, rank_points=None):
    """OpenSetROC.m → (DIR [số rank × số FAR], FAR, thresholds). ``score`` hàng = gallery, cột = probe."""
    score = np.asarray(score, dtype=np.float64)
    gal = np.asarray(gal_labels).ravel()
    prob = np.asarray(prob_labels).ravel()
    if rank_points is None:
        rank_points = [r for r in list(range(1, 11)) + list(range(20, 101, 10)) if r <= len(gal)]
    rank_points = np.asarray(rank_points).ravel()
    imp_score, gen_score, prob_ranks = _open_set_scores(score, gal, prob)
    n_imp = imp_score.size
    fa = _false_alarms(far_points, n_imp)
    thr = _thresholds(_kth_desc_sorted(imp_score), float(imp_score[0]), float(imp_score[-1]), gen_score, fa, n_imp)
    T1 = gen_score[:, None] >= thr[None, :]                                 # Ngen × F
    T2 = prob_ranks[:, None] <= rank_points[None, :]                        # Ngen × R
    DIR = (T1[:, None, :] & T2[:, :, None]).mean(axis=0)                    # R × F
    return DIR, fa / n_imp, thr


# ------------------------------------------------------------------------------------------------------------
# Áp lên đặc trưng + file chia BLUFR (data_splits/lfw_blufr/split_tXX.csv)
# ------------------------------------------------------------------------------------------------------------
def _codes(ids: Sequence[str]) -> np.ndarray:
    _, inv = np.unique(np.asarray(ids, dtype=object).astype(str), return_inverse=True)
    return inv.astype(np.int64)


def canonical_scores(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """CÁCH TÍNH ĐIỂM DUY NHẤT cho BLUFR (verification, open-set, CH2) và cho ma trận đối chiếu Octave:
    cosine = tích vô hướng tính bằng float64 (tích hai số float32 là chính xác trong float64) rồi LÀM TRÒN về float32,
    trả float64 (giá trị biểu diễn được bằng float32).
    Lý do (eval-test-ban-giao.md, LƯỢT 3): kết quả GEMM phụ thuộc thứ tự cộng của BLAS (cỡ khối, số luồng, OpenBLAS/MKL,
    CPU/GPU) ở bit cuối — float64 lệch ~1e-16, float32 lệch ~1e-7. Làm tròn kết quả float64 về float32 xoá lệch đó
    (chỉ còn khi tổng float64 rơi đúng sát điểm giữa hai số float32: xác suất ~1e-9/phần tử) → cùng điểm cho mọi
    cách chia khối / mọi máy, VR/DIR/ngưỡng lặp lại được."""
    return (np.asarray(a, np.float64) @ np.asarray(b, np.float64).T).astype(np.float32).astype(np.float64)


def lower_triangle_scores(feats: np.ndarray, labels: np.ndarray, chunk: int = 2048):
    """(genScore, impScore) mọi cặp i > j của tập test — đúng tập cặp của EvalROC.m (square, tril −1),
    tính theo khối (điểm bằng ``canonical_scores``) để không giữ ma trận N×N float64."""
    gen, imp = [], []
    n = len(labels)
    for i0 in range(0, n, chunk):
        i1 = min(i0 + chunk, n)
        blk = canonical_scores(feats[i0:i1], feats[:i1])                     # (b, i1)
        ii = np.arange(i0, i1)[:, None]
        m = np.arange(i1)[None, :] < ii
        same = labels[i0:i1, None] == labels[None, :i1]
        gen.append(blk[m & same])
        imp.append(blk[m & ~same])
    return np.concatenate(gen), np.concatenate(imp)


def evaluate_trial(feats: np.ndarray, image_index: Dict[str, int], split: pd.DataFrame,
                   open_fars: Sequence[float] = OPEN_FARS, verif_fars: Sequence[float] = VERIF_FARS,
                   fixed_thresholds: Optional[Dict[str, float]] = None) -> Dict:
    """Một trial BLUFR. ``feats`` đã L2 (float32). Ảnh thiếu → n_missing_images > 0 → DỪNG (không lặng lẽ bỏ)."""
    missing = [x for x in split.image if x not in image_index]
    if missing:
        raise SystemExit(f"DỪNG — BLUFR: n_missing_images = {len(missing)} (vd. {missing[:3]})")
    test_idx = np.array([image_index[x] for x in split.image])
    labels = _codes(split.identity.tolist())
    # --- verification: mọi cặp trong tập test (= gallery ∪ probe), EvalROC square ---
    gen, imp = lower_triangle_scores(feats[test_idx], labels)
    vr, far, thr = eval_roc_scores(gen, imp, verif_fars)
    # --- open-set: gallery × probe ---
    g = (split.role == "gallery").to_numpy()
    p = ~g
    sc = canonical_scores(feats[test_idx[g]], feats[test_idx[p]])           # hàng gallery, cột probe
    DIR, ofar, othr = open_set_roc(sc, labels[g], labels[p], open_fars, [1])
    out = {"n_missing_images": 0, "n_test_images": int(len(split)), "n_gallery": int(g.sum()),
           "n_genuine_probe": int((split.role == "probe_known").sum()),
           "n_impostor_probe": int((split.role == "probe_unknown").sum()),
           "n_gen_pairs": int(gen.size), "n_imp_pairs": int(imp.size)}
    for f, v, fr_, t in zip(verif_fars, vr, far, thr):
        out[f"VR@FAR={f:g}"] = float(v); out[f"FAR_actual@{f:g}"] = float(fr_); out[f"thr_VR@{f:g}"] = float(t)
    for j, f in enumerate(open_fars):
        out[f"DIR_rank1@FAR={f:g}"] = float(DIR[0, j]); out[f"FPIR_actual@{f:g}"] = float(ofar[j])
        out[f"thr_DIR@{f:g}"] = float(othr[j])
    if fixed_thresholds:
        names = list(fixed_thresholds)
        r = open_set_at_threshold(sc, labels[g], labels[p], [fixed_thresholds[n] for n in names])
        out["tai_nguong_co_dinh"] = {n: {"threshold": float(fixed_thresholds[n]), "FPIR": float(r["fpir"][i]),
                                         "FNIR_rank1": float(r["fnir"][i])} for i, n in enumerate(names)}
    return out


METRIC_KEYS = ["DIR_rank1@FAR=0.01", "DIR_rank1@FAR=0.1", "VR@FAR=0.001", "VR@FAR=0.0001"]


def summarize_trials(per_trial: List[Dict], keys: Iterable[str] = METRIC_KEYS) -> Dict:
    out = {}
    for k in keys:
        a = np.array([t[k] for t in per_trial], dtype=np.float64)
        mu, sd = float(a.mean()), float(a.std(ddof=1)) if a.size > 1 else float("nan")
        out[k] = {"mu": mu, "sigma": sd, "mu_minus_sigma": mu - sd, "n_trials": int(a.size)}
    return out


def summarize_fixed(per_trial: List[Dict]) -> Dict:
    """TB ± SD (ddof=1) qua 10 trial của FPIR, FNIR tại từng ngưỡng cố định."""
    first = per_trial[0].get("tai_nguong_co_dinh") or {}
    out = {}
    for n, v in first.items():
        row = {"threshold": v["threshold"]}
        for k in ("FPIR", "FNIR_rank1"):
            a = np.array([t["tai_nguong_co_dinh"][n][k] for t in per_trial], dtype=np.float64)
            row[k] = {"TB": float(a.mean()), "SD": float(a.std(ddof=1)) if a.size > 1 else float("nan"),
                      "n_trials": int(a.size)}
        out[n] = row
    return out


def evaluate_blufr(feats: np.ndarray, image_index: Dict[str, int], split_dir: str, log=print,
                   fixed_thresholds: Optional[Dict[str, float]] = None) -> Dict:
    files = sorted(f for f in os.listdir(split_dir) if f.startswith("split_t") and f.endswith(".csv"))
    if len(files) != 10:
        raise SystemExit(f"DỪNG — BLUFR cần 10 trial, thấy {len(files)}")
    per = {}
    for fn in files:
        per[fn] = evaluate_trial(feats, image_index, pd.read_csv(os.path.join(split_dir, fn)),
                                 fixed_thresholds=fixed_thresholds)
        log(f"  BLUFR {fn}: DIR@1%={per[fn]['DIR_rank1@FAR=0.01']:.4f} VR@0.1%={per[fn]['VR@FAR=0.001']:.4f}")
    res = {"per_trial": per, "summary": summarize_trials(list(per.values())),
            "protocol": "BLUFR LFW test, 10 trial; port EvalROC.m/OpenSetROC.m; σ ddof=1"}
    if fixed_thresholds:
        res["CH2_tai_nguong_co_dinh"] = summarize_fixed(list(per.values()))
    return res
