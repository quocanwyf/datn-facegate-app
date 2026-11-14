# Báo cáo T01 — Vendor và cổng nạp mô hình

- Trạng thái: **XONG** trên CPU theo tiêu chí T01. Chưa xác nhận parity GPU T02.
- Commit triển khai: `fcd09f7e9f3e8fd310acd0a85e747c950b2a070b`. Hoàn tất bàn giao ngày 15/11/2026.
- Máy chạy: Windows; Python 3.13.13, torch 2.11.0+cpu, OpenCV 4.14.0, numpy 2.5.4, scikit-image 0.26.0; CUDA false. Output `env.log`, `packages.log`.
- Đọc task/đặc tả §2.3/§4.1–4.4, Hub AGENTS và hub-rules; chỉ ghi trong phạm vi T01. T00 đã hoàn tất, push ở 2dca389 (triển khai 10be9e0).

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | test_vendor_hash.py cả 3 phần | 33 file khớp MANIFEST.sha256 và nguồn; bốn nhóm backbones/eval/align/utils code/code-v1 byte-equal; không có payload ngoài manifest (trừ metadata Git/manifest của task) | pytest.log, vendor-sync.log | Đạt |
| 2 | Cổng 4 bước CPU; epoch=18; t_eq30 khớp JSON <=1e-6 | 4/4 bước ok; epoch=18, missing/unexpected_keys rỗng, amp=false; t_eq30=0.3736472427845001 bằng log tham chiếu | pytest.log (verify_report + meta) | Đạt |
| 3 | 3 ca lỗi bị chặn đúng bước | Sai SHA bước1, thiếu strip link bước2, lệch t_eq30 bước4. Thêm ca fingerprint sai chuyển SystemExit của vendor thành MODEL_NOT_VERIFIED bước3 | pytest.log | Đạt |
| 4 | Import độc lập | Python con -I -B, CWD thư mục tạm, không có 02-thuc-nghiem trên sys.path; evaltest.features và fr.backbones đến từ vendor | pytest.log | Đạt |
| 5 | Không thay đổi 02-thuc-nghiem | git diff --stat/numstat rỗng; checkpoint local được người dùng cấp và đã kiểm SHA, không tracked | research-diff.log, checkpoint.log | Đạt |

Tổng **13 passed** trong 14.24s ở lần cuối, gồm các ca bổ sung hợp đồng màu/shape đầu vào. Đây là kiểm nguồn/nạp mô hình CPU, không phải benchmark/parity hoặc nhận dạng người thật. Checker SẠCH (`kiem-bi-mat.log`).

## Đã làm

- `scripts/vendor_sync.py` sao nguyên byte train.py (chỉ để tìm code, không chạy), fr/, ba module evaltest và hai JSON manifest/strip-map. Kiểm nguồn và đích trước khi sao; từ chối ghi đè khác hash. Chạy lặp kết quả không đổi (`vendor-sync-repeat.log`).
- `vendor/MANIFEST.sha256` có dạng JSON với path/source/sha256 cho từng file. `.gitattributes` của vendor dùng -text để Git không đổi LF/CRLF sau kiểm hash. Đây là metadata đóng băng do T01 tạo, không sửa nội dung nghiên cứu.
- `load_verified(model_row, device)` kiểm file SHA, strip-map nối tới meta.sha256 BLUFR, load_backbone(row=manifest, expected_sha=...), strict load/verify_checkpoint, rồi đối chiếu t_eq30. Mọi Exception/SystemExit thành ModelNotVerified với code MODEL_NOT_VERIFIED và bước cụ thể để tầng Hub sau này giữ health chẩn đoán.
- Biên `extract_aligned_bgr` dùng chung cho script T02 và worker T04: nhận BGR uint8 112x112, đổi RGB/transpose/contiguous, gọi duy nhất extract_features của vendor. Không tự chuẩn hóa, flip hay L2. Ma trận màu trong test chỉ kiểm thứ tự kênh, không sinh ảnh khuôn mặt, embedding giả hoặc số đo chất lượng AI.
- Cài môi trường CPU riêng .venv Python 3.13; không cài CUDA trên máy dev, không train lại hoặc torch.save lại backbone.

## File tạo/sửa

`hub/app/recog/model_loader.py`, các __init__.py, `hub/scripts/vendor_sync.py`, `hub/vendor/` (tạo một lần ở T01), `hub/tests/` và conftest, requirements.txt, pyproject.toml; log trong thư mục này. Không stage Hub AGENTS hoặc nguồn thiết kế có thay đổi sẵn của người dùng.

## Vấn đề và xử lý

- Lần gọi pytest trước khi cài xong dependencies báo chưa có pytest (`pytest-before-install.log`); sau cài đầy đủ đã chạy các kiểm cổng thật thành công. Không có bước cổng nào thất bại với file checkpoint thật.
- T01 dùng CPU fp32, không suy diễn tương đương CUDA fp16. Python patch 3.13.13 khác môi trường BLUFR 3.13.16; runtime ghi thực tế, không sửa log nguồn.
- Vendor từ đây chỉ đọc. Muốn thay đổi nội dung vendor/nguồn nghiên cứu để vượt kiểm thì phải dừng theo task.

## Specs và đề xuất thiết kế

Chưa chuyển FG-AI-001 sang archived: AC04 còn cần parity T02 và AC06 cần tích hợp health/worker ở các task sau. Kết quả T01 hoàn thành không đồng nghĩa toàn bộ feature đã nghiệm thu. Không sửa đặc tả/DB/UI/OpenAPI/plan.

## Cần An làm

> An ơi, T01 đã kiểm cổng CPU trên checkpoint thật. Bước GPU T02 sẽ bàn giao script + 03-app/ket-qua-kiem-thu/RUN-T02.md theo cách làm bất đồng bộ đã chốt; lúc rảnh pull rồi chạy trên laptop có CUDA, LFW ngoài repo và C:/datn-backbones-24. Gửi lại log thật, không gửi/commit best.pt, LFW hay ảnh khuôn mặt. Codex tiếp tục các task sau khi bàn giao script, không chờ kết quả GPU và không ghi parity đã đạt trước log.
