"""Kiểm file checkpoint mô hình (không có trong repo, An gửi riêng).

    python 03-app/tools/kiem-checkpoint.py

So SHA-256 của best.pt với dòng tương ứng trong manifest_24.json. In OK / THIẾU / SAI và thoát mã 0/1/2.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ID = "r18_uniface_v1_lam0.6_m0.45_s3_e28:best"
CKPT = os.path.join(ROOT, "02-thuc-nghiem", "results", "V1-s3-Hy", "phien-1",
                    "r18_uniface_v1_lam0.6_m0.45_s3_e28", "checkpoints", "best.pt")
MANIFEST = os.path.join(ROOT, "02-thuc-nghiem", "eval-test", "manifest", "manifest_24.json")


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = json.load(open(MANIFEST, encoding="utf-8"))["checkpoints"]
    row = next(r for r in rows if r["id"] == ID)
    if not os.path.exists(CKPT):
        print(f"THIẾU: chưa có checkpoint.\n  Cần đặt file vào: {CKPT}\n  Xin An gửi (Google Drive / Zalo).")
        sys.exit(1)
    got = sha256(CKPT)
    if got != row["sha256"]:
        print(f"SAI: SHA-256 không khớp manifest.\n  mong đợi {row['sha256']}\n  nhận được {got}\n  Tải lại file, không dùng file này.")
        sys.exit(2)
    print(f"OK: {ID}\n  {CKPT}\n  sha256 {got} (khớp manifest_24.json), epoch mong đợi {row['expected_epoch']}")


if __name__ == "__main__":
    main()
