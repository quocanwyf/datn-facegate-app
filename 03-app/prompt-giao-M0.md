# PROMPT GIAO M0 — NỀN TẢNG & PARITY (session code)
> Soạn bởi session thiết kế app, 14/11/2026, theo `dac-ta-app.md` v1.1. **Đã cũ:** sẽ được thay bằng `plan-codex/T01`–`T02` cho Codex (xem `KE-HOACH-TONG.md`). Từ v1.4.2 app chỉ dùng **1 mô hình V1 s3** — bỏ mọi bước liên quan UniFace s3. Dán toàn bộ khối dưới dòng `---` cho **một session code mới** (Claude Code / Claude desktop) đã mở thư mục `datn-cv-facerecognition`.

---

Bạn là **session code** của phần App trong ĐATN "Mobile App tích hợp tối ưu AI cho hệ thống điểm danh và kiểm soát ra vào bằng nhận dạng khuôn mặt" (Nguyễn Quốc An, PTIT). Nhiệm vụ lần này: **chỉ mốc M0 — Nền tảng & parity** của `03-app/dac-ta-app.md`. Không làm M1 trở đi. Trao đổi bằng tiếng Việt, giữ thuật ngữ kỹ thuật tiếng Anh.

## 1. Đọc trước (bắt buộc, theo thứ tự)
1. `CLAUDE.md` — tuân thủ tuyệt đối.
2. `03-app/dac-ta-app.md` — đặc biệt §2.2, §2.3, §3, §4.1–4.4 và dòng **M0** ở §12. Khi prompt này và đặc tả lệch nhau: **dừng, hỏi An**.
3. Mã gốc sẽ vendor: `02-thuc-nghiem/code/fr/`, `02-thuc-nghiem/code/train.py`, `02-thuc-nghiem/eval-test/evaltest/{__init__.py,features.py,common.py,strip_backbone.py}`, `02-thuc-nghiem/eval-test/manifest/manifest_24.json`, `02-thuc-nghiem/eval-test/tools/windows/logs/strip_map_ban_sao.json`.
4. Log nguồn số liệu: `02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/{ket_qua_blufr_lfw.json, env.json}`, `02-thuc-nghiem/results/2026-11-05_eval-lfw/align_log.csv`, các `val.jsonl` của `V1-s3-Hy` và `UniFace-s3-Ngan`.

## 2. Quyền truy cập
- **Chỉ ghi** vào `03-app/hub/` và `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_M0/`.
- **Chỉ đọc**: toàn bộ `02-thuc-nghiem/` (đã khoá — KHÔNG ghi, KHÔNG tạo `__pycache__`; chạy Python với `-B` hoặc `PYTHONDONTWRITEBYTECODE=1` khi import từ đó), `C:\datn-backbones-24` (ngoài dự án — xin An cấp quyền đọc), thư mục LFW deep-funneled (An tải về, ngoài `02-thuc-nghiem/`, xem §3 đặc tả).
- Không sửa `dac-ta-app.md`, `de-cuong.md`, `nhat-ky.md`. Đề xuất thay đổi → ghi mục "Đề xuất cho session thiết kế" cuối báo cáo.
- Không xoá file (CLAUDE.md §4).

## 3. Lưu ý môi trường — đọc trước khi chạy gì
- M0 cần **GPU RTX 3050 trên Windows của An** (fp16/CUDA giống BLUFR). Nếu shell của bạn **không phải** máy Windows đó (vd. VM Linux không thấy GPU: `nvidia-smi` lỗi), thì: viết đầy đủ script + hướng dẫn chạy (lệnh PowerShell cụ thể), **để An chạy trên Windows**, rồi đọc log An trả về để lập báo cáo. Không được chạy bước GPU trên CPU rồi báo như kết quả GPU.
- Mọi lệnh nặng in log ra file trong `03-app/ket-qua-kiem-thu/<ngày>_M0/` (stdout + stderr), kèm thời điểm và phiên bản.

## 4. Việc cần làm (đúng thứ tự; bước sau chỉ chạy khi bước trước đạt)
1. **`hub/scripts/check_env.py`**: in Python, torch (+ CUDA build), `torch.cuda.is_available()`, tên GPU, driver (`nvidia-smi`), OpenCV, numpy. Mục tiêu trùng môi trường BLUFR (`env.json`: Python 3.13, torch 2.11.0+cu130; OpenCV 4.14.0). Không được → chọn bản torch hợp driver, **ghi lý do**, chạy tiếp (đặc tả §3 cho phép), nhưng đánh dấu trong báo cáo.
2. **Vendor** theo §2.2–2.3: `hub/vendor/code/{train.py, fr/…}`, `hub/vendor/evaltest/{__init__.py, features.py, common.py}`, `hub/vendor/manifest/{manifest_24.json, strip_map_ban_sao.json}`, kèm `hub/vendor/MANIFEST.sha256`. Sao **nguyên văn** (so sha256 sau khi sao). `hub/tests/test_vendor_hash.py`: (a) hash khớp `MANIFEST.sha256`; (b) khớp file gốc trong `02-thuc-nghiem/code/`; (c) `fr/backbones`, `fr/eval`, `fr/align`, `fr/utils` giống hệt bản trong `02-thuc-nghiem/code-v1/`.
3. **Lớp bọc** `hub/app/recog/model_loader.py`: đặt `os.environ["DATN_CODE_DIR"]` = `hub/vendor/code` **trước** `import evaltest.features`; hàm `load_verified(model_id)` thực hiện **cổng khởi động 4 bước** §4.1 (sha gốc = manifest → strip_map nối tới `meta.sha256` trong `ket_qua_blufr_lfw.json` → `load_backbone(path, cuda, row=<dòng manifest>, expected_sha=…)` → `t_eq30` khớp ≤ 1e-6). Sai bước nào → raise, không trả mô hình.
4. **`hub/scripts/m0_tensor_equal.py`** (chạy một lần): với mỗi mô hình, nạp state dict backbone từ `best.pt` gốc và từ bản trích `C:\datn-backbones-24\<dest>` (đường dẫn `dest` trong strip_map) → `torch.equal` cho **mọi** khoá; ghi danh sách khoá + kết quả.
5. **Parity feature (lớp bọc)** `hub/scripts/parity_features.py` — chỉ chứng minh lớp bọc không làm hỏng gì (không phải phép tái lập số liệu test): chọn cố định 100 ảnh LFW (seed ghi trong log), căn chỉnh bằng `YuNetDetector` + `pick_center_face` + `norm_crop` → BGR→RGB → uint8 (N,3,112,112). So (a) đường đi qua lớp bọc Hub với (b) gọi trực tiếp `evaltest.features.extract_features` — cùng máy, cùng checkpoint, cùng chế độ: **max abs Δ ≤ 1e-5**. Nếu tìm thấy file feature của lần chạy Kaggle thì so thêm: **cos ≥ 0,9999** từng ảnh; không có file thì ghi "không có feature Kaggle để so; M0 không tái lập BLUFR (quyết định của An, xem nhật ký)".
5b. **[DỰ PHÒNG — KHÔNG CHẠY trong M0, theo quyết định của An 14/11/2026]** Tái lập đầu-cuối 1 trial BLUFR `hub/scripts/m0_blufr_t01.py`. Chỉ được viết/chạy khi An yêu cầu (vd. vận hành thử thấy từ chối nhầm hoặc người lạ lọt qua bất thường, cần phân biệt lỗi pipeline với điều kiện thực tế). Nội dung giữ lại để dùng khi đó:
   - Căn chỉnh **toàn bộ** LFW ở chế độ `pick_center_face` bằng đúng đường đi của lần test (`evaltest.lfw_data.ensure_aligned` → `align_lfw.py`), ghi ra thư mục tạm **ngoài** `02-thuc-nghiem/`.
   - Trích feature bằng `evaltest.features.extract_features` (mô hình nạp qua cổng khởi động bước 3).
   - Chạy `evaltest.blufr.evaluate_trial` trên `02-thuc-nghiem/data_splits/lfw_blufr/split_t01.csv` (import `evaltest` từ `02-thuc-nghiem/eval-test/` ở chế độ chỉ-đọc, `-B`).
   - So với `ket_qua["r18_uniface_v1_lam0.6_m0.45_s3_e28:best"].blufr.per_trial["split_t01.csv"]`: `thr_DIR@0.01` = 0,46859; `DIR_rank1@FAR=0.01` = 0,83278; `VR@FAR=0.001` = 0,97844. **Dung sai [khởi đầu]: |Δthr| ≤ 1e-3; |ΔDIR| ≤ 0,5 điểm %; |ΔVR| ≤ 0,5 điểm %.**
   - Thông tin thêm (không tính đạt/không đạt): so `aligned_sha256` với `38d3fc75501b65e3…c6a3` (`toan_ven_du_lieu.lfw.aligned_sha256`); chỉ kỳ vọng khớp nếu cùng OpenCV 4.14.0 — lệch thì ghi lại, không dừng.
   - Báo cáo phải ghi rõ: **đây là chạy lại trên tập test đã mở để kiểm tái lập, không phải kết quả mới**; không đưa số này vào bảng kết quả của quyển.
6. **Parity landmark** `hub/scripts/parity_landmarks.py`: chạy YuNet (score 0,6, retry 0,3 như `align_lfw.py`, chọn `pick_center_face`) trên **toàn bộ** ảnh có trong `align_log.csv`; so 10 toạ độ với log: **≥ 99% ảnh có lệch tối đa ≤ 0,5 px**. Báo thêm: phân phối lệch, số ảnh khác `method` (detect/retry/fallback) so với log, và **số ảnh đổi mặt** khi chuyển sang quy tắc "mặt lớn nhất" (chỉ để báo cáo, không phải tiêu chí).
7. **Test kênh màu** `hub/tests/test_color_order.py`: cùng ảnh, đưa BGR thay RGB → kỳ vọng cos(feature_BGR, feature_RGB) **< 0,99**. Nếu cos ≥ 0,99: đó là mô hình **ít nhạy** với thứ tự kênh (test này không bắt được lỗi quên chuyển màu), **không phải hệ thống sai** — ghi số đo thật và đề xuất cách test khác (vd. so số khớp/không khớp trên một tập cặp nhỏ khi đảo kênh), không dừng.
8. **`hub/scripts/gen_thresholds.py`**: đọc trực tiếp log (không gõ tay) → ghi `ket-qua-kiem-thu/<ngày>_M0/thresholds.json` cho cả hai mô hình: DEFAULT_VAL (`thr@far=1e-05` tại epoch best trong `val.jsonl`), STRICT_TEST (TB 10 trial `thr_DIR@0.01`), `t_eq30`; mỗi số kèm `source_ref` (file + trường). Kiểm khớp bảng §4.4 (V1: 0,4233 / 0,4657 / 0,3736; UniFace: 0,3692 / 0,4148 / 0,2908, làm tròn 4 chữ số).

## 5. Điều kiện DỪNG và báo An (không tự xử lý cho qua)
- Driver/GPU không chạy được **bất kỳ** bản torch CUDA nào.
- Bất kỳ bước nào của cổng khởi động sai (sha, strip_map, `verify_checkpoint`, `t_eq30`).
- `torch.equal` = False ở bất kỳ khoá nào.
- Parity feature (bước 5) hoặc landmark (bước 6) **không đạt dung sai**. (Bước 5b không chạy trong M0.)
- Ngưỡng sinh ra lệch bảng §4.4.
- Cần sửa file trong `vendor/` hoặc `02-thuc-nghiem/` để chạy được.

**Tuyệt đối không:** nới ngưỡng, sửa file vendor, đổi tiền xử lý, bỏ qua bước kiểm, hoặc ghi "pass" khi không có log chứng minh.

## 6. Báo cáo M0
File `03-app/ket-qua-kiem-thu/<ngày>_M0/bao-cao-M0.md`:
1. **Môi trường thật**: OS, GPU, driver, Python, torch (+CUDA), OpenCV, numpy — dán nguyên output `check_env.py`.
2. **Bảng tiêu chí**: tiêu chí (M0-1…M0-7) | ngưỡng trong đặc tả | **số đo thật** | file log | Đạt / Không đạt.
3. Chi tiết từng bước + đường dẫn log.
4. Những điểm lệch so với môi trường BLUFR và ảnh hưởng dự kiến.
5. **Đề xuất cho session thiết kế** (nếu có).
6. Danh sách file đã tạo.

Kết thúc bằng 3–5 dòng tóm tắt cho An: đạt hay chưa, có gì cần An quyết.
