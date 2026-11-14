"""Bộ phát hiện mặt + 5 điểm mốc: YuNet (OpenCV Zoo).

Vì sao YuNet (so với RetinaFace/SCRFD của insightface, MTCNN, MediaPipe):
  - License rõ: model + code **MIT** (``LICENSES/opencv_zoo_yunet_MIT.txt``); model insightface (RetinaFace/SCRFD
    đóng gói sẵn) chỉ cho nghiên cứu phi thương mại.
  - Có sẵn trong OpenCV ≥ 4.5.4 (``cv2.FaceDetectorYN``) → không cần thêm thư viện; Kaggle, laptop, server đều chạy.
  - Rất nhẹ (file .onnx ~233 KB) → dùng lại được cho Mobile App/server.
  - Trả đúng 5 điểm mốc cùng ngữ nghĩa với template ArcFace (2 mắt, mũi, 2 khoé miệng). MediaPipe BlazeFace
    không có 2 khoé miệng nên không khớp template.
  Hạn chế [ngoài nguồn — nhận định]: dữ liệu train CASIA bản insightface được căn bằng detector khác (MTCNN/RetinaFace),
  nên điểm mốc của YuNet có thể lệch nhẹ → ảnh căn chỉnh hơi khác phân phối train. Ảnh hưởng như nhau cho mọi
  phương pháp (baseline và proposed dùng cùng ảnh đã căn) nên so sánh vẫn công bằng.

Model: ``models/face_detection_yunet_2023mar.onnx`` — opencv/opencv_zoo commit 48b10fa505aeb51fbd127fc60a5c660040e823b7,
sha256 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4. Bản 2023mar có kích thước vào cố định,
chạy được với OpenCV 4.x (README opencv_zoo); bản 2026may dành cho OpenCV 5.x.

Định dạng đầu ra của ``cv2.FaceDetectorYN.detect`` (mỗi hàng 15 số, theo tài liệu OpenCV):
  0-3 hộp (x, y, w, h); 4-5 mắt phải (của người, nằm bên TRÁI ảnh); 6-7 mắt trái; 8-9 đầu mũi;
  10-11 khoé miệng phải; 12-13 khoé miệng trái; 14 điểm tin cậy.
  → thứ tự 5 điểm trùng thứ tự template ArcFace (xem template.py). Unit test kiểm tra mắt[0].x < mắt[1].x trên ảnh thật.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import cv2
import numpy as np

DEFAULT_YUNET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_detection_yunet_2023mar.onnx")


class YuNetDetector:
    def __init__(self, model_path: str = DEFAULT_YUNET_PATH, score_threshold: float = 0.6,
                 nms_threshold: float = 0.3, top_k: int = 50):
        if not hasattr(cv2, "FaceDetectorYN"):
            raise RuntimeError("OpenCV quá cũ: cần cv2.FaceDetectorYN (OpenCV ≥ 4.5.4)")
        if not os.path.exists(model_path):
            raise FileNotFoundError(model_path)
        self.model_path, self.score_threshold = model_path, score_threshold
        self._det = cv2.FaceDetectorYN.create(model_path, "", (320, 320), score_threshold, nms_threshold, top_k)

    def detect(self, img_bgr: np.ndarray, score_threshold: Optional[float] = None) -> List[Dict]:
        """Trả danh sách mặt: {'box': (x,y,w,h), 'landmarks': (5,2) float32, 'score': float}."""
        h, w = img_bgr.shape[:2]
        if score_threshold is not None:
            self._det.setScoreThreshold(float(score_threshold))
        self._det.setInputSize((w, h))
        _, faces = self._det.detect(img_bgr)
        if score_threshold is not None:
            self._det.setScoreThreshold(float(self.score_threshold))
        out = []
        if faces is None:
            return out
        for f in faces:
            out.append({"box": tuple(float(v) for v in f[:4]),
                        "landmarks": np.asarray(f[4:14], dtype=np.float32).reshape(5, 2),
                        "score": float(f[14])})
        return out


def pick_center_face(faces: List[Dict], img_shape) -> Optional[Dict]:
    """Chọn mặt có tâm hộp gần tâm ảnh nhất (quy ước LFW: người được gán nhãn nằm giữa ảnh);
    bằng nhau thì chọn hộp lớn hơn."""
    if not faces:
        return None
    h, w = img_shape[:2]
    cx, cy = w / 2.0, h / 2.0

    def key(f):
        x, y, bw, bh = f["box"]
        d = ((x + bw / 2 - cx) ** 2 + (y + bh / 2 - cy) ** 2) ** 0.5
        return (round(d, 3), -bw * bh)
    return min(faces, key=key)
