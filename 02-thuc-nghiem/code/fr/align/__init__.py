"""Căn chỉnh khuôn mặt về 112×112 theo template 5 điểm ArcFace — dùng chung cho đánh giá (LFW open-set) và Mobile App.

    from fr.align import FaceAligner
    aligner = FaceAligner()                       # YuNet (OpenCV, MIT) + template ArcFace
    out = aligner(img_bgr)                        # dict: aligned (112,112,3) BGR uint8 | None, landmarks, score, ...

Thành phần:
  - template.py : ARCFACE_DST (toạ độ 5 điểm ArcFace 112×112) + estimate_norm / norm_crop — chép từ insightface.
  - detector.py : YuNetDetector — bọc cv2.FaceDetectorYN, chọn mặt gần tâm ảnh nhất, trả 5 điểm mốc.
  - pipeline.py : FaceAligner — detect → căn chỉnh; có chế độ dự phòng (fallback) khi không thấy mặt.
"""
from .template import ARCFACE_DST, estimate_norm, norm_crop          # noqa: F401
from .detector import YuNetDetector, DEFAULT_YUNET_PATH               # noqa: F401
from .pipeline import FaceAligner                                     # noqa: F401
