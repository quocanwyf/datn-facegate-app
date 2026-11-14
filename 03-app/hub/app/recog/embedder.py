import numpy as np
import torch
from app.recog.model_loader import extract_aligned_bgr, frozen_features


class Embedder:
    def __init__(self, backbone, device: torch.device):
        self.backbone, self.device = backbone, device

    def embed(self, img_bgr: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        frozen_features()
        from fr.align.template import norm_crop
        warped_bgr, _ = norm_crop(img_bgr, landmarks)
        # Biên RGB đã dùng chung với parity T02; không chuẩn hóa/lật/L2 lần nữa.
        return extract_aligned_bgr(self.backbone, warped_bgr, self.device)[0]
