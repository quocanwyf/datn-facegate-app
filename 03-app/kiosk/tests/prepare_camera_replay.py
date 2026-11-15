"""Đổi ảnh được đồng ý thử thành video camera AVD; luôn lưu ngoài repo.

Đây là phát lại ảnh thật để kiểm tra tích hợp, không phải phép đo người đứng
trước webcam hay kiểm thử chống giả mạo T13. Không tạo khuôn mặt/sự kiện giả.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
from PIL import Image, ImageOps

parser = argparse.ArgumentParser()
parser.add_argument('photos', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--cycles', type=int, default=30, help='Lặp bộ ảnh để camera không hết video giữa luồng review.')
args = parser.parse_args()
if not 1 <= args.cycles <= 300:
    raise SystemExit('Số vòng phải trong khoảng 1–300.')
root = Path(__file__).resolve().parents[3]
output = args.output.resolve()
if output.is_relative_to(root):
    raise SystemExit('Video chứa ảnh thật phải nằm ngoài repo.')
photos = sorted(p for p in args.photos.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.heif', '.heic'})
if not photos:
    raise SystemExit('Không có ảnh đầu vào.')
pillow_heif.register_heif_opener()
output.parent.mkdir(parents=True, exist_ok=True)
writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*'mp4v'), 10, (640, 480))
if not writer.isOpened():
    raise SystemExit('Không mở được bộ mã hóa video.')
try:
    # Mỗi ảnh giữ 2 s; toàn bộ ảnh thật được giữ tỷ lệ, thêm viền trống hai bên.
    frames = []
    for path in photos:
        with Image.open(path) as source:
            fitted = ImageOps.contain(ImageOps.exif_transpose(source).convert('RGB'), (640, 480))
            canvas = Image.new('RGB', (640, 480))
            canvas.paste(fitted, ((640 - fitted.width) // 2, (480 - fitted.height) // 2))
            frame = cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR)
        frames.append(frame)
    for _ in range(args.cycles):
        for frame in frames:
            for _ in range(20):
                writer.write(frame)
finally:
    writer.release()
print(json.dumps({'kind': 'authorized-photo-replay', 'photos': len(photos), 'cycles': args.cycles, 'fps': 10, 'seconds': len(photos) * 2 * args.cycles, 'video': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False))
