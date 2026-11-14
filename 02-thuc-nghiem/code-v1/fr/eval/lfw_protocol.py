"""Sinh file chia (split) open-set trên LFW — chỉ danh sách tên ảnh + nhãn + vai trò, KHÔNG chứa ảnh.

Hai họ protocol, cùng một định dạng CSV (cột ``image,identity,role``):
  ``image``    : đường dẫn tương đối "Ten_Nguoi/Ten_Nguoi_0001.jpg" (giống cấu trúc thư mục LFW / lfw-deepfunneled)
  ``identity`` : tên người (chuỗi)
  ``role``     : gallery | probe_known | probe_unknown

(A) Protocol tự dựng — ``02-thuc-nghiem/ke-hoach-du-lieu.md`` mục 4 (phương án A) [ngoài nguồn — đề xuất]:
  1. 1,680 người có ≥ 2 ảnh → hoán vị ngẫu nhiên theo seed, chia đôi thành nửa P0 (840) và P1 (840).
  2. fold 0: K = P0 (đã đăng ký), U = P1 (người lạ); fold 1: đảo vai (kiểu G1/G2 của IJB-C).
  3. Gallery: mỗi người trong K đúng 1 ảnh (kịch bản "đăng ký 1 ảnh"); ảnh được chọn ngẫu nhiên theo seed,
     chọn MỘT LẦN cho mọi người (nên cùng một người có cùng ảnh gallery ở fold nào nó thuộc K).
  4. probe_known: các ảnh còn lại của người trong K.
  5. probe_unknown: toàn bộ ảnh của người trong U + toàn bộ 4,069 người chỉ có 1 ảnh.
  6. 5 seed × 2 fold = 10 split → báo mean ± std.
  Bộ sinh số: ``numpy.random.default_rng(seed)`` (PCG64) → cùng seed cho cùng split trên mọi máy.

(B) BLUFR (Liao, Lei, Yi, Li — IJCB 2014) — protocol CÔNG BỐ SẴN trên toàn bộ 13,233 ảnh LFW, 10 trial:
  gallery 1,000 người × 1 ảnh, probe gồm người đã đăng ký và người lạ; verification trên mọi cặp của tập test
  (~157K cặp dương, ~47M cặp âm mỗi trial). Chuyển từ ``blufr_lfw_config.mat`` (biến galIndex/probIndex/testIndex,
  chỉ số 1-based theo imageList) sang cùng định dạng CSV; tập test của trial = gallery ∪ probe (theo README BLUFR).
  Chỉ dùng phần TEST (phần train của BLUFR dành cho thuật toán học trên LFW — mô hình của mình train trên CASIA).
"""
from __future__ import annotations

import collections
import hashlib
import os
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

ROLES = ("gallery", "probe_known", "probe_unknown")
DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_FOLDS = (0, 1)


def image_name(person: str, k: int) -> str:
    return f"{person}/{person}_{k:04d}.jpg"


def read_people_csv(path: str) -> Dict[str, int]:
    """Đọc ``lfw_people.csv`` (cột name,images) — cùng nội dung ``lfw_allnames.csv`` của Kaggle jessicali9530/lfw-dataset."""
    df = pd.read_csv(path)
    return {str(n): int(c) for n, c in zip(df["name"], df["images"])}


def people_from_blufr(mat_path: str) -> Tuple[Dict[str, int], List[str], np.ndarray]:
    import scipy.io as sio
    m = sio.loadmat(mat_path)
    image_list = [str(x[0][0]) for x in m["imageList"]]
    names = ["_".join(f.split("_")[:-1]) for f in image_list]
    return dict(collections.Counter(names)), image_list, m


def make_protocol_a(people: Dict[str, int], seed: int, fold: int) -> pd.DataFrame:
    assert fold in (0, 1)
    multi = sorted(n for n, c in people.items() if c >= 2)
    single = sorted(n for n, c in people.items() if c == 1)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(multi))
    half = len(multi) // 2
    p0 = [multi[i] for i in perm[:half]]
    p1 = [multi[i] for i in perm[half:]]
    # ảnh gallery của MỌI người ≥2 ảnh được bốc một lần (độc lập với fold) — chỉ số 1-based
    gal_k = {n: int(rng.integers(1, people[n] + 1)) for n in multi}
    K, U = (p0, p1) if fold == 0 else (p1, p0)
    rows = []
    for n in sorted(K):
        for k in range(1, people[n] + 1):
            rows.append((image_name(n, k), n, "gallery" if k == gal_k[n] else "probe_known"))
    for n in sorted(U) + single:
        for k in range(1, people[n] + 1):
            rows.append((image_name(n, k), n, "probe_unknown"))
    return pd.DataFrame(rows, columns=["image", "identity", "role"])


def make_blufr_trial(mat, image_list: Sequence[str], trial: int) -> pd.DataFrame:
    """trial: 0..9. Chuyển chỉ số 1-based của MATLAB → 0-based."""
    labels = mat["labels"].ravel()
    gal = mat["galIndex"][trial, 0].ravel().astype(int) - 1
    prob = mat["probIndex"][trial, 0].ravel().astype(int) - 1
    test = mat["testIndex"][trial, 0].ravel().astype(int) - 1
    assert set(gal) | set(prob) == set(test) and not (set(gal) & set(prob))
    gal_labels = set(labels[gal].tolist())
    rows = []
    for i in gal:
        f = image_list[i]
        rows.append((f"{'_'.join(f.split('_')[:-1])}/{f}", "_".join(f.split("_")[:-1]), "gallery"))
    for i in prob:
        f = image_list[i]
        role = "probe_known" if labels[i] in gal_labels else "probe_unknown"
        rows.append((f"{'_'.join(f.split('_')[:-1])}/{f}", "_".join(f.split("_")[:-1]), role))
    return pd.DataFrame(rows, columns=["image", "identity", "role"])


def split_stats(df: pd.DataFrame) -> Dict[str, int]:
    g = df[df.role == "gallery"]
    pk = df[df.role == "probe_known"]
    pu = df[df.role == "probe_unknown"]
    n_gal_ids = g.identity.nunique()
    return {"n_images": int(len(df)), "n_gallery_images": int(len(g)), "n_gallery_ids": int(n_gal_ids),
            "n_probe_known": int(len(pk)), "n_probe_unknown": int(len(pu)),
            "n_probe_unknown_ids": int(pu.identity.nunique()),
            # 1:1 kiểu "mọi cặp gallery–probe": số cặp dương = số probe đã biết (1 ảnh gallery/người)
            "pairs_gallery_probe_pos": int(len(pk)),
            "pairs_gallery_probe_neg": int(len(g) * (len(pk) + len(pu)) - len(pk)),
            # 1:1 kiểu "mọi cặp trong split" (BLUFR EvalROC.m)
            "pairs_all_pos": int(sum(c * (c - 1) // 2 for c in df.identity.value_counts())),
            "pairs_all_neg": int(len(df) * (len(df) - 1) // 2 - sum(c * (c - 1) // 2 for c in df.identity.value_counts()))}


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_split(df: pd.DataFrame) -> None:
    """Bất biến bắt buộc của một split open-set (dùng trong unit test và khi nạp split)."""
    assert set(df.role.unique()) <= set(ROLES)
    assert df.image.is_unique, "ảnh trùng trong split"
    g = df[df.role == "gallery"]
    assert g.identity.is_unique, "mỗi người chỉ 1 ảnh gallery"
    gal_ids = set(g.identity)
    assert set(df[df.role == "probe_known"].identity) <= gal_ids, "probe_known phải có người trong gallery"
    assert not (set(df[df.role == "probe_unknown"].identity) & gal_ids), "probe_unknown không được có trong gallery"
