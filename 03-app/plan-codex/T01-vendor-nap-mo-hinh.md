# T01 — Vendor code thực nghiệm + cổng nạp mô hình
> Phụ thuộc: T00 · Máy: máy Hy (CPU) · Cần checkpoint: **có** — xin An file `best.pt`
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T01/bao-cao.md`.

## Mục tiêu
Hub nạp đúng mô hình UniFace + V1 s3 qua **cổng kiểm 4 bước**, dùng đúng code đã tạo số liệu BLUFR (bản sao chỉ-đọc có kiểm hash).

## Đọc trước
`03-app/dac-ta-app.md` §2.3, §4.1, §4.3 · skill `hub-rules` · `03-app/hub/AGENTS.md` · `02-thuc-nghiem/eval-test/evaltest/{features.py,common.py}` · `02-thuc-nghiem/code/fr/align/{detector.py,template.py}`.

## Được ghi vào
`03-app/hub/vendor/` (chỉ trong task này) · `03-app/hub/app/recog/model_loader.py` · `03-app/hub/tests/` · `03-app/hub/scripts/` · `03-app/hub/requirements.txt`, `pyproject.toml`.

## Các bước
1. Kiểm checkpoint: `python 03-app/tools/kiem-checkpoint.py` → phải OK (chưa có file → dừng).
2. Vendor (sao **nguyên văn**, kiểm sha256 sau khi sao) theo đặc tả §2.2:
   - `02-thuc-nghiem/code/train.py`, `02-thuc-nghiem/code/fr/` → `hub/vendor/code/`
   - `02-thuc-nghiem/eval-test/evaltest/{__init__,features,common}.py` → `hub/vendor/evaltest/`
   - `manifest_24.json`, `strip_map_ban_sao.json` → `hub/vendor/manifest/`
   - Ghi `hub/vendor/MANIFEST.sha256` (sha256 + đường dẫn gốc), viết bằng script `hub/scripts/vendor_sync.py` (chạy lại được).
3. `tests/test_vendor_hash.py`: (a) mọi file khớp `MANIFEST.sha256`; (b) khớp file gốc trong `02-thuc-nghiem/code/`; (c) `fr/backbones`, `fr/eval`, `fr/align`, `fr/utils` giống hệt bản trong `02-thuc-nghiem/code-v1/`.
4. `app/recog/model_loader.py`: đặt `DATN_CODE_DIR` rồi import `evaltest.features`; hàm `load_verified(model_row, device)` làm 4 bước (skill `hub-rules`), trả `(backbone, meta, verify_report)`; lỗi → exception có mã `MODEL_NOT_VERIFIED` + bước sai.
5. `tests/test_model_gate.py`: chạy 4 bước trên CPU (pass); + 3 ca phải lỗi: sha sai (file giả), strip_map thiếu bản ghi, `t_eq30` lệch.
6. Kiểm `import evaltest.features` chạy được trong môi trường **chỉ có `hub/vendor`** (không có `02-thuc-nghiem` trên sys.path): `tests/test_vendor_isolated.py` (chạy Python con với `sys.path` sạch).

## Tiêu chí nghiệm thu
| # | Tiêu chí | Cách kiểm |
|---|---|---|
| 1 | `test_vendor_hash.py` pass cả 3 phần | pytest log |
| 2 | 4 bước cổng pass trên CPU; `meta.epoch` = 18; `t_eq30` = 0,3736472… (|Δ| ≤ 1e-6 so JSON) | pytest log + in `verify_report` |
| 3 | 3 ca lỗi bị chặn đúng bước | pytest log |
| 4 | Import độc lập chạy được | pytest log |
| 5 | `git diff --stat` không có thay đổi nào trong `02-thuc-nghiem/` | output |

## Điều kiện dừng
Chưa có checkpoint · bất kỳ bước cổng nào sai với file thật · phải sửa file vendor hoặc `02-thuc-nghiem/` mới chạy được.
