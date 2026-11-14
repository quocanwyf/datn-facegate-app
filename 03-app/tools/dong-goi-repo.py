"""Đóng gói repo bàn giao (public) từ thư mục nghiên cứu.

    python 03-app/tools/dong-goi-repo.py <thư_mục_nghiên_cứu> <thư_mục_ra>

- Chép 03-app/ (trừ file nặng/không cần) + file gốc repo trong 03-app/ban-giao/repo-root/.
- Chép BẢN RÚT GỌN của 02-thuc-nghiem/ theo danh sách cố định (giữ nguyên đường dẫn tương đối).
- KHÔNG chép checkpoint (*.pt). Kiểm SHA-256 từng file sau khi chép; ghi 02-thuc-nghiem/BAN-RUT-GON.md.
- Cuối cùng chạy kiem-bi-mat.py trên thư mục ra.
Chạy lại được: xoá thư mục ra cũ trước khi chạy (script không tự xoá).
"""
import fnmatch
import hashlib
import os
import shutil
import subprocess
import sys

SRC, OUT = (os.path.abspath(a) for a in sys.argv[1:3])
if os.path.exists(OUT) and os.listdir(OUT):
    sys.exit(f"Thư mục ra không rỗng: {OUT}")

APP_EXCLUDE = ["03-app/ban-giao/*", "03-app/design-ui-kit/*.zip", "*/__pycache__/*", "*.pyc", "*/node_modules/*", "*/.venv/*"]
SLIM = [  # (đường dẫn trong 02-thuc-nghiem, là thư mục?)
    ("code/train.py", False), ("code/fr", True), ("code/tools/align_lfw.py", False), ("code/LICENSES", True),
    ("code-v1/fr/backbones", True), ("code-v1/fr/eval", True), ("code-v1/fr/align", True), ("code-v1/fr/utils", True),
    ("eval-test/evaltest/__init__.py", False), ("eval-test/evaltest/features.py", False), ("eval-test/evaltest/common.py", False),
    ("eval-test/evaltest/strip_backbone.py", False), ("eval-test/evaltest/blufr.py", False), ("eval-test/evaltest/lfw_data.py", False),
    ("eval-test/manifest/manifest_24.json", False), ("eval-test/tools/windows/logs/strip_map_ban_sao.json", False),
    ("results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json", False),
    ("results/2026-11-12_test-blufr-lfw/eval_test/env.json", False),
    ("results/2026-11-05_eval-lfw/align_log.csv", False),
    ("results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/val.jsonl", False),
    ("results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/summary.json", False),
    ("results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/config.yaml", False),
    ("data_splits/lfw_blufr", True),
]
SKIP = lambda rel: any(fnmatch.fnmatch(rel, p) for p in APP_EXCLUDE) or "/__pycache__/" in "/" + rel or rel.endswith(".pt")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def copy(src_rel_root, rel, log):
    s = os.path.join(SRC, rel); d = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(s, d)
    a, b = sha(s), sha(d)
    if a != b:
        sys.exit(f"Lỗi chép (hash lệch): {rel}")
    log.append((rel, a, os.path.getsize(d)))


def walk(rel_dir):
    for d, dirs, files in os.walk(os.path.join(SRC, rel_dir)):
        dirs[:] = [x for x in dirs if x not in {"__pycache__", "node_modules", ".venv"}]
        for f in files:
            yield os.path.relpath(os.path.join(d, f), SRC).replace("\\", "/")


os.makedirs(OUT)
app_log, slim_log = [], []
for rel in walk("03-app"):
    if not SKIP(rel):
        copy(SRC, rel, app_log)
# file gốc repo
rr = os.path.join(SRC, "03-app", "ban-giao", "repo-root")
for d, dirs, files in os.walk(rr):
    for f in files:
        s = os.path.join(d, f); rel = os.path.relpath(s, rr).replace("\\", "/")
        t = os.path.join(OUT, rel); os.makedirs(os.path.dirname(t), exist_ok=True); shutil.copy2(s, t)
        app_log.append((rel, sha(t), os.path.getsize(t)))
# bản rút gọn 02-thuc-nghiem
for p, is_dir in SLIM:
    rel = "02-thuc-nghiem/" + p
    if not os.path.exists(os.path.join(SRC, rel)):
        sys.exit(f"Thiếu nguồn: {rel}")
    for r in (walk(rel) if is_dir else [rel]):
        if not SKIP(r):
            copy(SRC, r, slim_log)
with open(os.path.join(OUT, "02-thuc-nghiem", "BAN-RUT-GON.md"), "w", encoding="utf-8") as f:
    f.write("# 02-thuc-nghiem — BẢN RÚT GỌN, CHỈ ĐỌC\n\n"
            "Chỉ gồm các file phần App cần (vendor, kiểm hash, ngưỡng, parity). Bản đầy đủ (~7,9 GB) nằm ở máy An.\n"
            "**Không có checkpoint** — xem `README-BAN-GIAO.md` mục Checkpoint. Không sửa bất kỳ file nào ở đây.\n\n"
            "| File | SHA-256 | Byte |\n|---|---|---|\n")
    for rel, h, n in sorted(slim_log):
        f.write(f"| `{rel}` | `{h}` | {n} |\n")
print(f"03-app + gốc repo: {len(app_log)} file; 02-thuc-nghiem rút gọn: {len(slim_log)} file "
      f"({sum(n for _, _, n in slim_log)/1e6:.1f} MB)")
r = subprocess.run([sys.executable, os.path.join(OUT, "03-app", "tools", "kiem-bi-mat.py"), OUT])
sys.exit(r.returncode)
