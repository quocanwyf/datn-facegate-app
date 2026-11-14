# T02 — Kiểm môi trường GPU, so tensor, parity, sinh bảng ngưỡng
> Phụ thuộc: T01 · Máy: **laptop An (RTX 3050, Windows)** — Hy viết script, An chạy · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T02/bao-cao.md`.

## Mục tiêu
Chứng minh Hub trên laptop An dùng đúng mô hình và đúng tiền xử lý như lúc tạo số liệu; sinh bảng ngưỡng từ log.
(Thay cho `03-app/prompt-giao-M0.md` — file đó đã cũ.)

## Đọc trước
`03-app/dac-ta-app.md` §3, §4.1–4.4, dòng **M0** ở §12 · skill `hub-rules`.

## Được ghi vào
`03-app/hub/scripts/` · `03-app/hub/tests/` · `03-app/ket-qua-kiem-thu/<ngày>_T02/`.

## Chuẩn bị (An)
- LFW deep-funneled (Kaggle `jessicali9530/lfw-dataset`) tải về **ngoài repo**, vd. `D:\datn-data\lfw`; truyền đường dẫn qua tham số `--lfw`.
- Thư mục bản trích sẵn `C:\datn-backbones-24` (có trên laptop An).
- Môi trường Python của Hub + torch **bản CUDA** hợp driver RTX 3050.

## Script (Hy viết, chạy thử phần CPU trên máy mình với `--device cpu --limit 20` nếu có vài ảnh LFW)
1. `scripts/check_env.py` → in Python, torch (+CUDA build), `torch.cuda.is_available()`, tên GPU, driver (`nvidia-smi`), OpenCV, numpy. Mục tiêu trùng môi trường BLUFR (`02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/env.json`: Python 3.13, torch 2.11.0+cu130; OpenCV 4.14.0). Driver không hỗ trợ CUDA 13 → dùng bản torch CUDA hợp driver, ghi rõ.
2. `scripts/m0_tensor_equal.py --stripped C:\datn-backbones-24` → `torch.equal` mọi khoá giữa backbone từ `best.pt` và bản trích (đường dẫn đích lấy từ `strip_map`).
3. `scripts/parity_features.py --lfw … --n 100 --seed 2026` → 100 ảnh LFW, căn chỉnh `YuNetDetector` + `pick_center_face` + `norm_crop` → BGR→RGB → uint8; so (a) qua lớp bọc Hub với (b) gọi thẳng `extract_features`: **max |Δ| ≤ 1e-5** (cùng máy, cùng chế độ fp16).
4. `scripts/parity_landmarks.py --lfw …` → YuNet (0,6, thử lại 0,3 như `align_lfw.py`, `pick_center_face`) trên **mọi** ảnh trong `02-thuc-nghiem/results/2026-11-05_eval-lfw/align_log.csv`; so 10 toạ độ: **≥ 99% ảnh lệch tối đa ≤ 0,5 px**. Báo thêm: phân phối lệch, số ảnh khác `method`, số ảnh đổi mặt khi dùng "mặt lớn nhất" (chỉ báo cáo).
5. `tests/test_color_order.py` → cùng ảnh, đưa BGR thay RGB: kỳ vọng cos < 0,99. Nếu ≥ 0,99: ghi số đo + đề xuất test khác (không dừng).
6. `scripts/gen_thresholds.py` → đọc log, ghi `ket-qua-kiem-thu/<ngày>_T02/thresholds.json`: DEFAULT_VAL (`thr@far=1e-05` tại epoch 18 trong `val.jsonl` V1 s3), STRICT_TEST (TB 10 trial `thr_DIR@0.01`), `t_eq30`, mỗi số kèm `source_ref`; so với `03-app/db/seed.sql` (0,4232754409313202 · 0,4657080352306366 · 0,3736472427845001).

## Tiêu chí nghiệm thu (đặc tả §12 M0)
| # | Tiêu chí |
|---|---|
| 1 | Output `check_env.py` thật trong báo cáo |
| 2 | `torch.equal` = True cho mọi khoá |
| 3 | Parity feature max |Δ| ≤ 1e-5 |
| 4 | Parity landmark ≥ 99% ảnh ≤ 0,5 px |
| 5 | Test màu: số đo thật (đạt hoặc ghi đề xuất) |
| 6 | Ngưỡng sinh ra = giá trị trong `seed.sql` (sai số ≤ 1e-9) |
| 7 | Ghi rõ: **không tái lập BLUFR trên laptop** (quyết định An 14/11) |

## Điều kiện dừng
Không chạy được bất kỳ bản torch CUDA nào · `torch.equal` False · parity không đạt · ngưỡng lệch seed. **Không nới ngưỡng, không sửa vendor.**

## Dự phòng (KHÔNG chạy trừ khi An yêu cầu)
Tái lập BLUFR trial 01 (`evaltest.blufr.evaluate_trial` trên `02-thuc-nghiem/data_splits/lfw_blufr/split_t01.csv`, so `per_trial["split_t01.csv"]`) — xem đặc tả §12 M0 (4b).
