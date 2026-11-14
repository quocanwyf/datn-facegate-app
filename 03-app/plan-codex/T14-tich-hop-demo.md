# T14 — Tích hợp đầu-cuối, đo hiệu năng, kịch bản demo
> Phụ thuộc: T00–T13 · Máy: **laptop An** (Hub, GPU) + máy Hy (máy ảo Kiosk, trình duyệt) · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T14/bao-cao.md`.

## Mục tiêu
Hệ thống chạy liền mạch trên cấu hình demo; số đo hiệu năng thật; kịch bản demo 5–7 phút.

## Cấu hình demo đề xuất
Hub + PostgreSQL + web build tĩnh trên **laptop An** (GPU) · Kiosk = máy ảo trên laptop Hy (hoặc laptop An nếu đủ RAM) trỏ tới IP LAN của laptop An · trình duyệt quản trị trên laptop bất kỳ cùng Wi-Fi. Mở cổng 8000 trên tường lửa Windows của laptop An.

## Các bước
1. Cài Hub trên laptop An theo `hub/AGENTS.md`; cổng khởi động pass với **CUDA**.
2. Đo (đặc tả §11): thời gian từng bước/khung (giải mã, YuNet, liveness, embed, top1, quyết định) p50/p95 với 1 và 3 Kiosk giả lập (`kiosk_sim.py` song song) — tối thiểu 300 khung mỗi cấu hình; thời gian đứng-vào → kết quả trên Kiosk thật (máy ảo) 20 lượt; VRAM/RAM.
3. Chạy các kịch bản: đăng ký → duyệt → chấm công vào/ra → đi muộn → quên quét ra → giải trình → duyệt → bảng công + Excel → người lạ → cảnh báo → chấm hộ NV MANUAL → cửa phòng máy chủ (NV không thuộc Kỹ thuật bị từ chối) → nghỉ việc (dữ liệu khuôn mặt bị xoá) → ảnh in (khi đã bật T13).
4. Viết `03-app/kich-ban-demo.md` (thứ tự, ai làm gì, câu nói, dữ liệu chuẩn bị, phương án khi lỗi).
5. Chạy skill `security review` lần cuối.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | Bảng số đo thật (p50/p95 từng bước, 1 và 3 Kiosk) + máy/phiên bản |
| 2 | Mọi kịch bản bước 3 chạy được — mỗi kịch bản có ảnh/video |
| 3 | `kich-ban-demo.md` đủ |
| 4 | Danh sách lỗi còn lại (nếu có) + mức ảnh hưởng tới demo |
