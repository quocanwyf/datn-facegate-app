from dataclasses import dataclass
import math
import numpy as np
from app.recog.model_loader import frozen_features


@dataclass(frozen=True)
class FrameObs:
    valid: bool
    reason: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    landmarks: np.ndarray | None = None
    det_score: float | None = None
    yaw_ratio: float | None = None


class Detector:
    def __init__(self, min_face_px: float, max_abs_yaw_ratio: float):
        frozen_features()
        from fr.align.detector import YuNetDetector
        self.detector = YuNetDetector(score_threshold=0.6)
        self.min_face_px, self.max_abs_yaw_ratio = min_face_px, max_abs_yaw_ratio

    def observe(self, img_bgr: np.ndarray) -> FrameObs:
        faces = self.detector.detect(img_bgr)
        if not faces:
            return FrameObs(False, 'NO_FACE')
        face = max(faces, key=lambda item: item['box'][2] * item['box'][3])
        points = face['landmarks']
        distance = float(np.linalg.norm(points[1] - points[0]))
        yaw = float((points[2, 0] - (points[0, 0] + points[1, 0]) / 2) / distance) if distance > 0 else None
        reason = ('FACE_TOO_SMALL' if min(face['box'][2:]) < self.min_face_px else
                  'BAD_POSE' if yaw is None or not math.isfinite(yaw) or abs(yaw) > self.max_abs_yaw_ratio else None)
        return FrameObs(reason is None, reason, face['box'], points, face['score'], yaw)
