"""Checkpoint đầy đủ để resume sau khi phiên Kaggle/Colab bị ngắt.

Lưu: backbone, head (gồm W, b của UniFace, weight_mom nếu r<1), optimizer, GradScaler, epoch,
số bước đã chạy trong epoch, global_step, trạng thái RNG, generator lấy mẫu lớp, config.
(Lịch LR là hàm thuần của global_step nên không cần state riêng — xem train.py: lr_at().)
Ghi kiểu nguyên tử: ghi file tạm rồi os.replace → không hỏng file nếu bị ngắt giữa lúc ghi.
"""
import os

import torch


def save_checkpoint(path: str, state: dict):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    torch.save(state, tmp)
    os.replace(tmp, path)


def load_checkpoint(path: str, map_location="cpu") -> dict:
    return torch.load(path, map_location=map_location, weights_only=False)
