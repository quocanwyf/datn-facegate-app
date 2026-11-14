"""Pipeline detect → căn chỉnh 112×112 (dùng lại được cho Mobile App: ảnh camera → mặt căn chỉnh → embedding).

Quy tắc khi KHÔNG phát hiện được mặt (để mọi phương pháp dùng đúng cùng một tập ảnh):
  1) chạy lại YuNet với ngưỡng tin cậy thấp hơn (``retry_threshold``);
  2) vẫn không thấy → nếu có ``fallback_landmarks`` (vd. trung vị điểm mốc trên toàn bộ ảnh đã detect được của
     LFW deep-funneled — ảnh LFW đã được căn giữa sẵn) thì căn theo điểm mốc cố định đó, ``method='fallback'``;
  3) không có fallback → ``aligned=None`` (App: báo "không thấy khuôn mặt").
Kết quả ghi rõ ``method`` cho từng ảnh để báo tỉ lệ detect thất bại.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from .detector import DEFAULT_YUNET_PATH, YuNetDetector, pick_center_face
from .template import norm_crop


class FaceAligner:
    def __init__(self, model_path: str = DEFAULT_YUNET_PATH, score_threshold: float = 0.6,
                 retry_threshold: float = 0.3, image_size: int = 112,
                 fallback_landmarks: Optional[np.ndarray] = None):
        self.detector = YuNetDetector(model_path, score_threshold)
        self.retry_threshold = retry_threshold
        self.image_size = image_size
        self.fallback_landmarks = None if fallback_landmarks is None else np.asarray(fallback_landmarks, np.float32)

    def __call__(self, img_bgr: np.ndarray) -> Dict:
        faces = self.detector.detect(img_bgr)
        method = "detect"
        if not faces and self.retry_threshold is not None:
            faces = self.detector.detect(img_bgr, score_threshold=self.retry_threshold)
            method = "detect_retry"
        face = pick_center_face(faces, img_bgr.shape)
        if face is not None:
            lmk, score, n = face["landmarks"], face["score"], len(faces)
        elif self.fallback_landmarks is not None:
            lmk, score, n, method = self.fallback_landmarks, float("nan"), 0, "fallback"
        else:
            return {"aligned": None, "landmarks": None, "score": float("nan"), "n_faces": 0, "method": "failed"}
        aligned, M = norm_crop(img_bgr, lmk, self.image_size)
        return {"aligned": aligned, "landmarks": np.asarray(lmk, np.float32), "M": M, "score": score,
                "n_faces": n, "method": method}
