"""Kiểm repo không chứa file cấm trước khi commit/push (repo PUBLIC).

    python 03-app/tools/kiem-bi-mat.py [thư_mục_gốc]

Chặn file bí mật/trọng số bị đưa vào Git và dữ liệu không được phép trong repo.
Chỉ cho phép .env gốc và checkpoint chuẩn ở local nếu Git xác nhận ignored, untracked.
File tracked vẫn được kiểm tra kể cả nằm trong thư mục thường được bỏ qua.
"""
import os
import re
import sys
import subprocess

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".expo", "android", "ios", "dist", "build"}
BAN_EXT = {".pt", ".pth", ".ckpt", ".safetensors", ".bin", ".npy", ".npz"}
ALLOW = {os.path.normpath(x) for x in [
    "02-thuc-nghiem/code/fr/align/models/face_detection_yunet_2023mar.onnx",   # YuNet, MIT, ~0,2 MB
    "02-thuc-nghiem/code-v1/fr/align/models/face_detection_yunet_2023mar.onnx",
    "03-app/hub/vendor/code/fr/align/models/face_detection_yunet_2023mar.onnx",
]}
ALLOW_PREFIX = (os.path.normpath("03-app/hub/vendor/silentface") + os.sep,)   # MiniFASNet, Apache-2.0 (T13)
BAN_NAME = re.compile(r"^\.env(\..+)?$", re.I)
BAN_DIRS = re.compile(r"(^|/)(hub_data|HUB_DATA_DIR|lfw|lfw-deepfunneled|faces|snapshots)(/|$)", re.I)
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC )?PRIVATE KEY-----|ghp_[0-9A-Za-z]{36}|sk-[0-9A-Za-z]{32,})")
MAX = 50 * 1024 * 1024
LOCAL_ONLY = {os.path.normcase(os.path.normpath(path)) for path in (
    '.env',
    '02-thuc-nghiem/results/V1-s3-Hy/phien-1/'
    'r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt',
)}


def tracked_paths():
    try:
        result = subprocess.run(['git', '-C', ROOT, 'ls-files', '-z', '--cached'],
                                capture_output=True, check=True)
        return {os.path.normpath(os.fsdecode(path)) for path in result.stdout.split(b'\0') if path}
    except (OSError, subprocess.CalledProcessError):
        return None


TRACKED = tracked_paths()
TRACKED_KEYS = {os.path.normcase(path) for path in TRACKED or ()}


def allowed_local(rel):
    key = os.path.normcase(rel)
    if TRACKED is None or key not in LOCAL_ONLY or key in TRACKED_KEYS:
        return False
    try:
        result = subprocess.run(['git', '-C', ROOT, 'check-ignore', '--quiet', '--',
                                 rel.replace('\\', '/')], capture_output=True)
        return result.returncode == 0
    except OSError:
        return False


def inspect_file(rel):
    p = os.path.join(ROOT, rel)
    f = os.path.basename(rel)
    ext = os.path.splitext(f)[1].lower()
    if rel in ALLOW or rel.startswith(ALLOW_PREFIX):
        return None
    if allowed_local(rel):
        return None
    if BAN_DIRS.search(rel.replace('\\', '/')):
        return 'thư mục dữ liệu khuôn mặt / LFW'
    if BAN_NAME.match(f) and f.casefold() != '.env.example':
        return 'file .env thật'
    if ext in BAN_EXT or ext == '.onnx':
        return 'trọng số / mảng dữ liệu'
    if not os.path.isfile(p):
        return None
    if os.path.getsize(p) > MAX:
        return 'file > 50 MB'
    if ext in {'.py', '.ts', '.tsx', '.js', '.json', '.yaml', '.yml', '.md', '.txt', '.toml', '.cfg', '.ini', '.sql'}:
        try:
            with open(p, encoding='utf-8', errors='ignore') as stream:
                if SECRET.search(stream.read()):
                    return 'chuỗi giống khoá bí mật'
        except OSError:
            return 'không đọc được file để kiểm tra'
    return None

bad = []
checked = set()
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    rel_d = os.path.relpath(d, ROOT).replace("\\", "/")
    if rel_d != "." and BAN_DIRS.search(rel_d):
        bad.append((rel_d + "/", "thư mục dữ liệu khuôn mặt / LFW")); dirs[:] = []; continue
    for f in files:
        rel = os.path.normpath(os.path.relpath(os.path.join(d, f), ROOT))
        checked.add(os.path.normcase(rel))
        reason = inspect_file(rel)
        if reason:
            bad.append((rel, reason))
for rel in sorted(TRACKED or ()):
    if os.path.normcase(rel) not in checked:
        reason = inspect_file(rel)
        if reason:
            bad.append((rel, reason))
if bad:
    print("KHÔNG SẠCH — gỡ các file sau trước khi commit/push:")
    for r, why in bad:
        print(f"  {r}  ({why})")
    sys.exit(1)
print(f"SẠCH: {ROOT}")
