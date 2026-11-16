"""MiniFASNet ensemble theo nguồn ghim T13; p_live là xác suất class thật."""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

BUNDLE = Path(__file__).resolve().parents[2] / 'vendor/silentface'
POLICY_FIELDS = ('frame_long_side', 'jpeg_quality', 'min_face_px', 'max_abs_yaw_ratio',
                 'max_fps', 'window_size', 'match_min', 'unknown_min', 'spoof_min',
                 'lost_face_sec', 'iou_reset')
GROUPS = ('live', 'print', 'phone', 'replay')
MODELS = (
    ('resources/anti_spoof_models/2.7_80x80_MiniFASNetV2.pth', 'MiniFASNetV2', 2.7),
    ('resources/anti_spoof_models/4_0_0_80x80_MiniFASNetV1SE.pth', 'MiniFASNetV1SE', 4.0),
)


def bundle_id():
    return hashlib.sha256((BUNDLE / 'manifest.json').read_bytes()).hexdigest()


def verify_bundle():
    manifest = json.loads((BUNDLE / 'manifest.json').read_text(encoding='utf8'))
    if manifest['license'] != 'Apache-2.0' or manifest['commit'] != 'b6d5f04ad78778917853b25c778acef6d5626d15':
        raise ValueError('Nguồn chống giả mạo không đúng bản đã kiểm.')
    for name, expected in manifest['sha256'].items():
        path = (BUNDLE / name).resolve()
        if not path.is_relative_to(BUNDLE.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Checksum chống giả mạo không khớp.')
    return manifest


def require_approval(data_dir: Path, threshold: float, settings: dict):
    """Marker do CLI phê duyệt ghi trong kho riêng; REST không tự tạo marker."""
    path = Path(data_dir) / 'liveness-approved.json'
    if path.stat().st_size > 65536:
        raise ValueError('Phê duyệt chống giả mạo không hợp lệ.')
    approval = json.loads(path.read_text(encoding='utf8'))
    if (not isinstance(approval, dict) or not isinstance(approval.get('trial_counts'), dict)
            or not isinstance(approval.get('approved_by'), str)
            or type(approval.get('threshold')) not in (int, float)
            or not isinstance(approval.get('calibration_sha256'), str)):
        raise ValueError('Phê duyệt chống giả mạo không hợp lệ.')
    if (type(threshold) not in (float, int) or not math.isfinite(threshold) or not 0 <= threshold <= 1
            or approval.get('threshold') != threshold or approval.get('bundle_id') != bundle_id()
            or approval.get('policy') != {key: settings[key] for key in POLICY_FIELDS}
            or not str(approval.get('approved_by', '')).strip()
            or datetime.fromisoformat(approval['approved_at']).tzinfo is None
            or not all(type(approval['trial_counts'].get(group)) is int and approval['trial_counts'][group] > 0 for group in GROUPS)
            or len(approval.get('calibration_sha256', '')) != 64):
        raise ValueError('Cần hiệu chỉnh và chốt L đúng mô hình/cấu hình camera.')
    return approval


def input_tensor(patch):
    # Upstream functional.py:37–60: numpy BGR HWC → CHW float32 [0,255].
    # KHÔNG RGB, KHÔNG /255; docstring ToTensor khác mã upstream thực chạy.
    return torch.from_numpy(np.ascontiguousarray(patch.transpose(2, 0, 1))).float().unsqueeze(0)


class Liveness:
    def __init__(self, device='cpu'):
        self.device = torch.device(device)
        self.models = None

    def load(self):
        if self.models is not None:
            return
        verify_bundle()  # Trước khi import mã và deserialise trọng số.
        from vendor.silentface.src.model_lib import MiniFASNet
        from vendor.silentface.src.generate_patches import CropImage
        models = []
        for filename, architecture, scale in MODELS:
            state = torch.load(BUNDLE / filename, map_location='cpu', weights_only=True)
            state = {name.removeprefix('module.'): value for name, value in state.items()}
            model = getattr(MiniFASNet, architecture)(conv6_kernel=(5, 5)).to(self.device)
            model.load_state_dict(state, strict=True)
            model.eval()
            models.append((model, scale))
        self.cropper = CropImage()
        self.models = models

    def probabilities(self, img_bgr, bbox):
        if (img_bgr.dtype != np.uint8 or img_bgr.ndim != 3 or img_bgr.shape[2] != 3
                or len(bbox) != 4 or not all(math.isfinite(float(value)) for value in bbox)
                or bbox[2] <= 0 or bbox[3] <= 0):
            raise ValueError('Khung/BBox chống giả mạo không hợp lệ.')
        self.load()
        prediction = np.zeros(3, dtype=np.float64)
        with torch.inference_mode():
            for model, scale in self.models:
                patch = self.cropper.crop(img_bgr, bbox, scale, out_w=80, out_h=80)
                logits = model(input_tensor(patch).to(self.device))
                prediction += torch.softmax(logits, dim=1)[0].cpu().numpy()
        prediction /= len(self.models)
        if not np.isfinite(prediction).all():
            raise ValueError('Điểm chống giả mạo không hữu hạn.')
        return prediction

    def score(self, img_bgr, bbox) -> float:
        # test.py: class 1 = Real; không lấy confidence argmax của class fake.
        return float(self.probabilities(img_bgr, bbox)[1])
