"""Căn chỉnh toàn bộ 13,233 ảnh LFW (deep-funneled 250×250) về 112×112 theo template ArcFace.

    python tools/align_lfw.py --lfw_root <thư mục chứa Aaron_Eckhart/...> --people ../data_splits/lfw_people.csv --out <dir>

Hai lượt:
  1) YuNet detect (ngưỡng 0.6, thử lại 0.3) → chọn mặt gần tâm ảnh → 5 điểm mốc.
  2) Ảnh không detect được → dùng điểm mốc dự phòng = TRUNG VỊ điểm mốc của mọi ảnh detect được (LFW đã căn giữa
     sẵn nên vị trí mặt gần như cố định). Mọi ảnh vẫn có mặt trong protocol; số ảnh dự phòng được báo cáo.
Đầu ra (``--out``):
  aligned_u8.npy     (N,3,112,112) uint8 RGB — cùng định dạng ảnh của load_bin → dùng thẳng extract_embeddings
  index.csv          thứ tự ảnh (cột image) khớp hàng trong aligned_u8.npy
  align_log.csv      image, method (detect / detect_retry / fallback / read_error), score, n_faces, 10 toạ độ điểm mốc
  align_summary.json số lượng theo method, tỉ lệ detect thất bại, điểm mốc dự phòng, phiên bản OpenCV, thời gian
"""
import argparse
import json
import os
import sys
import time
import warnings

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore", category=FutureWarning)
from fr.align.detector import DEFAULT_YUNET_PATH, YuNetDetector, pick_center_face  # noqa: E402
from fr.align.template import norm_crop                                           # noqa: E402
from fr.eval.lfw_protocol import image_name, read_people_csv                      # noqa: E402


def align_lfw(lfw_root, people_csv, out_dir, model_path=DEFAULT_YUNET_PATH, limit=None, log=print):
    os.makedirs(out_dir, exist_ok=True)
    people = read_people_csv(people_csv)
    images = [image_name(n, k) for n in sorted(people) for k in range(1, people[n] + 1)]
    if limit:
        images = images[:limit]
    det = YuNetDetector(model_path, score_threshold=0.6)
    t0 = time.time()
    rows, lmks, raw = [], np.full((len(images), 5, 2), np.nan, np.float32), {}
    for i, im in enumerate(images):
        img = cv2.imread(os.path.join(lfw_root, im))
        if img is None:
            rows.append((im, "read_error", np.nan, 0)); continue
        faces, method = det.detect(img), "detect"
        if not faces:
            faces, method = det.detect(img, score_threshold=0.3), "detect_retry"
        f = pick_center_face(faces, img.shape)
        if f is None:
            rows.append((im, "fallback", np.nan, 0))
        else:
            lmks[i] = f["landmarks"]; rows.append((im, method, f["score"], len(faces)))
        if (i + 1) % 2000 == 0:
            log(f"  detect {i + 1}/{len(images)}  ({time.time() - t0:.0f}s)")
    ok = ~np.isnan(lmks[:, 0, 0])
    fallback = np.median(lmks[ok], axis=0) if ok.any() else None
    aligned = np.zeros((len(images), 3, 112, 112), np.uint8)
    for i, im in enumerate(images):
        if rows[i][1] == "read_error":
            continue
        img = cv2.imread(os.path.join(lfw_root, im))
        lm = lmks[i] if ok[i] else fallback
        warped, _ = norm_crop(img, lm)
        aligned[i] = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
        if not ok[i]:
            lmks[i] = fallback
    np.save(os.path.join(out_dir, "aligned_u8.npy"), aligned)
    keep = [r[1] != "read_error" for r in rows]
    pd.DataFrame({"image": images}).to_csv(os.path.join(out_dir, "index.csv"), index=False)
    log_df = pd.DataFrame(rows, columns=["image", "method", "score", "n_faces"])
    for j, c in enumerate(["x0", "y0", "x1", "y1", "x2", "y2", "x3", "y3", "x4", "y4"]):
        log_df[c] = lmks.reshape(len(images), 10)[:, j]
    log_df.to_csv(os.path.join(out_dir, "align_log.csv"), index=False)
    counts = log_df.method.value_counts().to_dict()
    n = len(images)
    summary = {"n_images": n, "counts": {k: int(v) for k, v in counts.items()},
               "detect_fail_rate": float((counts.get("fallback", 0) + counts.get("read_error", 0)) / n),
               "detect_fail_rate_first_pass": float((n - counts.get("detect", 0)) / n),
               "multi_face_images": int((log_df.n_faces > 1).sum()),
               "fallback_landmarks_median": None if fallback is None else np.round(fallback, 3).tolist(),
               "detector": os.path.basename(model_path), "opencv": cv2.__version__,
               "seconds": time.time() - t0, "n_usable": int(sum(keep))}
    json.dump(summary, open(os.path.join(out_dir, "align_summary.json"), "w"), indent=2)
    log(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lfw_root", required=True); ap.add_argument("--people", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    align_lfw(a.lfw_root, a.people, a.out, limit=a.limit)
