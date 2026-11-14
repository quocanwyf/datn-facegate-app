"""Kiểm hợp đồng màu bằng ma trận màu đơn, không tạo ảnh/khuôn mặt hoặc số đo AI."""
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from app.recog import model_loader


def test_boundary_sends_rgb_uint8_to_the_single_vendor_extractor(monkeypatch):
    sentinel = object()
    backbone = object()
    device = torch.device('cpu')
    def extract(model, tensor, selected_device):
        assert model is backbone and selected_device is device
        assert tensor.dtype == torch.uint8 and tensor.shape == (1, 3, 112, 112)
        assert tensor.is_contiguous()
        assert tensor[0, :, 0, 0].tolist() == [37, 23, 11]
        return sentinel
    monkeypatch.setattr(model_loader, 'frozen_features', lambda: SimpleNamespace(extract_features=extract))
    color_patch = np.empty((112, 112, 3), dtype=np.uint8)
    color_patch[:] = [11, 23, 37]
    assert model_loader.extract_aligned_bgr(backbone, color_patch, device) is sentinel


@pytest.mark.parametrize('invalid', [None, np.zeros((16, 16, 3), dtype=np.uint8), np.zeros((112, 112, 3), dtype=np.float32)])
def test_invalid_alignment_input_rejected(invalid):
    with pytest.raises(ValueError, match='BGR uint8'):
        model_loader.extract_aligned_bgr(object(), invalid, torch.device('cpu'))
