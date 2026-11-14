"""Tiện ích chung: tìm thư mục code đóng băng (chỉ đọc), sha256, ghi JSON (có chế độ ghi-một-lần)."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from typing import Iterable, Optional

EVALTEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # .../02-thuc-nghiem/eval-test
THUC_NGHIEM_DIR = os.path.dirname(EVALTEST_DIR)                                   # .../02-thuc-nghiem


def find_code_dir(explicit: Optional[str] = None) -> str:
    """Thư mục ``code/`` đóng băng: --code_dir / biến môi trường DATN_CODE_DIR / ../code (bố cục trên máy An)."""
    cands = [explicit, os.environ.get("DATN_CODE_DIR"), os.path.join(THUC_NGHIEM_DIR, "code")]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "train.py")) and os.path.isdir(os.path.join(c, "fr")):
            return os.path.abspath(c)
    raise FileNotFoundError("không thấy thư mục code/ (cần train.py + fr/) — đặt DATN_CODE_DIR")


def import_code(explicit: Optional[str] = None) -> str:
    """Thêm code/ vào sys.path (chỉ để import; KHÔNG ghi gì vào đó)."""
    d = find_code_dir(explicit)
    if d not in sys.path:
        sys.path.insert(0, d)
    sys.dont_write_bytecode = True          # không tạo __pycache__ mới trong code/ đóng băng
    return d


def sha256_file(path: str, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_files(paths: Iterable[str], root: str) -> str:
    """Hash gộp nhiều file (tên tương đối + nội dung, CRLF→LF) — dùng ghi 'hash code eval-test'."""
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda x: os.path.relpath(x, root).replace(os.sep, "/")):
        h.update(os.path.relpath(p, root).replace(os.sep, "/").encode())
        with open(p, "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def evaltest_code_hash() -> str:
    files = []
    for d in ("evaltest",):
        for dp, dn, fs in os.walk(os.path.join(EVALTEST_DIR, d)):
            dn[:] = [x for x in dn if x != "__pycache__"]
            files += [os.path.join(dp, f) for f in fs if f.endswith(".py")]
    return sha256_files(files, EVALTEST_DIR)


def _clean(o):
    if isinstance(o, float):
        return None if math.isnan(o) else o
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return _clean(o.item())
        if isinstance(o, np.ndarray):
            return _clean(o.tolist())
    except ImportError:
        pass
    return o


def dump_json(obj, path: str, exclusive: bool = False) -> str:
    """Ghi JSON. ``exclusive=True``: mở bằng mode 'x' → lỗi nếu file đã tồn tại (ghi đúng MỘT lần).
    NaN ghi thành null. Trả về sha256 của nội dung đã ghi."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = json.dumps(_clean(obj), indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8")
    with open(path, "xb" if exclusive else "wb") as f:
        f.write(data)
    return sha256_bytes(data)


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: str):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
