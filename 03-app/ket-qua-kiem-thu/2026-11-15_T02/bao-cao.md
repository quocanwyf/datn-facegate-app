# Báo cáo T02 — Script parity và bảng ngưỡng

- Trạng thái: XONG MỘT PHẦN — hoàn tất script/hướng dẫn; chờ log GPU laptop An. Theo chỉ đạo của người dùng, push phần này và tiếp tục T03–T12, không chờ chạy T02.
- Commit nền: 232f95e (T01 đã push); mã commit script xem lịch sử `T02: prepare asynchronous GPU parity handoff`.
- Máy chạy: Windows 11, Python 3.13.13, torch 2.11.0+cpu, OpenCV 4.14.0, numpy 2.5.4 (`cpu-env.json`). Không có CUDA.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Môi trường thật | Đã ghi CPU; GPU chưa chạy | cpu-env.json | Một phần |
| 2 | torch.equal mọi khóa | Chưa chạy; thiếu bản trích trên máy Hy | RUN-T02.md | Chờ An |
| 3 | Feature delta ≤1e-5 | Chưa chạy; không có LFW | RUN-T02.md | Chờ An |
| 4 | Landmark ≥99% trong 0,5px | Chưa chạy; không có LFW | RUN-T02.md | Chờ An |
| 5 | Số đo test màu | SKIP đúng lý do thiếu LFW | pytest.log | Chờ An |
| 6 | Ngưỡng khớp seed ≤1e-9 | Cả ba ngưỡng delta=0, đọc từ log gốc | thresholds.json | Đạt |
| 7 | Không tái lập BLUFR | Không chạy BLUFR, script chỉ đọc kết quả có sẵn | thresholds.json | Đạt |

## Đã làm

Viết check_env, m0_tensor_equal, parity_features, parity_landmarks, gen_thresholds và tiện ích dùng chung. So feature dùng biên RGB của Hub đã kiểm ở T01; detector chọn tâm chỉ trong parity. Landmark đọc toàn bộ align_log, thử lại 0,3 và median fallback như nguồn; ảnh lỗi vẫn ở mẫu số. Không lưu ảnh hay embedding. CUDA không khả dụng thì dừng, không tự chuyển CPU để nghiệm thu.

Kiểm thử thực tế: **15 passed, 1 skipped** trong 18,24 giây, gồm hồi quy T01 và đọc ngưỡng thật/seed bị thay đổi. Các CLI `--help` chạy thành công; kiểm bí mật SẠCH. Lần chạy checker đầu gặp lỗi mã hóa stdout cp1252; chạy lại với PYTHONUTF8=1 thành công, hướng dẫn laptop đã đặt biến này.

## File đã tạo / sửa

`hub/scripts/{m0_common,check_env,m0_tensor_equal,parity_features,parity_landmarks,gen_thresholds}.py`, `hub/tests/{test_threshold_sources,test_color_order}.py`, `ket-qua-kiem-thu/RUN-T02.md` và log cùng thư mục báo cáo.

## Vấn đề và đề xuất

Chưa đủ bằng chứng đánh dấu toàn bộ T02 đạt hoặc archive FG-AI-001. Không sửa vendor, research, đặc tả, DB, UI, hợp đồng hay plan. Không có dữ liệu LFW/bản trích trên máy Hy nên không tạo ảnh hoặc số đo giả thay thế.

## Cần An làm — tin nhắn soạn sẵn

An pull main rồi mở `03-app/ket-qua-kiem-thu/RUN-T02.md`, chỉnh đường dẫn LFW ngoài repo và chạy khối PowerShell trên laptop RTX 3050. Cần checkpoint gốc đúng manifest và `C:\datn-backbones-24`. Chạy môi trường CUDA → tensor → feature 100 ảnh → landmark toàn bộ → màu → ngưỡng; không chạy lại BLUFR. Push riêng thư mục log JSON/stdout theo hướng dẫn, gửi hash commit và tên thư mục. Nếu lỗi, giữ log và gửi lại, không sửa ngưỡng/vendor. Hy/Codex tiếp tục T03–T12 trong lúc chờ.
