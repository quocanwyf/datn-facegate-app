"""Kiểm repo không chứa file cấm trước khi commit/push (repo PUBLIC).

    python 03-app/tools/kiem-bi-mat.py [thư_mục_gốc]

Chặn: checkpoint/trọng số lớn, .env thật, ảnh khuôn mặt/dữ liệu Hub, LFW, file > 50 MB, chuỗi giống khoá bí mật.
Bỏ qua thư mục bị .gitignore loại (node_modules, .venv, .git).
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".expo", "android", "ios", "dist", "build"}
BAN_EXT = {".pt", ".pth", ".ckpt", ".safetensors", ".bin", ".npy", ".npz"}
ALLOW = {os.path.normpath(x) for x in [
    "02-thuc-nghiem/code/fr/align/models/face_detection_yunet_2023mar.onnx",   # YuNet, MIT, ~0,2 MB
    "02-thuc-nghiem/code-v1/fr/align/models/face_detection_yunet_2023mar.onnx",
    "03-app/hub/vendor/code/fr/align/models/face_detection_yunet_2023mar.onnx",
]}
ALLOW_PREFIX = (os.path.normpath("03-app/hub/vendor/silentface") + os.sep,)   # MiniFASNet, Apache-2.0 (T13)
BAN_NAME = re.compile(r"^\.env(\..+)?$")
BAN_DIRS = re.compile(r"(^|/)(hub_data|HUB_DATA_DIR|lfw|lfw-deepfunneled|faces|snapshots)(/|$)", re.I)
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC )?PRIVATE KEY-----|ghp_[0-9A-Za-z]{36}|sk-[0-9A-Za-z]{32,})")
MAX = 50 * 1024 * 1024

bad = []
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    rel_d = os.path.relpath(d, ROOT).replace("\\", "/")
    if rel_d != "." and BAN_DIRS.search(rel_d):
        bad.append((rel_d + "/", "thư mục dữ liệu khuôn mặt / LFW")); dirs[:] = []; continue
    for f in files:
        p = os.path.join(d, f); rel = os.path.normpath(os.path.relpath(p, ROOT))
        ext = os.path.splitext(f)[1].lower()
        if rel in ALLOW or rel.startswith(ALLOW_PREFIX):
            continue
        if BAN_NAME.match(f) and f != ".env.example":
            bad.append((rel, "file .env thật"))
        elif ext in BAN_EXT or ext == ".onnx":
            bad.append((rel, "trọng số / mảng dữ liệu"))
        elif os.path.getsize(p) > MAX:
            bad.append((rel, "file > 50 MB"))
        elif ext in {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".md", ".txt", ".toml", ".cfg", ".ini", ".sql"}:
            try:
                if SECRET.search(open(p, encoding="utf-8", errors="ignore").read()):
                    bad.append((rel, "chuỗi giống khoá bí mật"))
            except OSError:
                pass
if bad:
    print("KHÔNG SẠCH — gỡ các file sau trước khi commit/push:")
    for r, why in bad:
        print(f"  {r}  ({why})")
    sys.exit(1)
print(f"SẠCH: {ROOT}")
