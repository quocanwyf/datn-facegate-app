# FaceGate — App chấm công & kiểm soát ra vào bằng nhận dạng khuôn mặt (bản demo ĐATN)

Phần ứng dụng của ĐATN *"Mobile App tích hợp tối ưu AI cho hệ thống điểm danh và kiểm soát ra vào bằng nhận dạng khuôn mặt"* — Nguyễn Quốc An, PTIT.
Mô hình nhận dạng: **UniFace + V1** (ResNet-18, train trên CASIA-WebFace) — chỉ dùng cho nghiên cứu/giáo dục, **không dùng thương mại**.

Mở [FaceGate.code-workspace](FaceGate.code-workspace) trong VS Code để thấy riêng Web, Kiosk, Hub và toàn bộ dự án.

| Cần tìm | Mở tại |
|---|---|
| Giao diện web quản trị và nhân viên | [web/src](03-app/web/src), bắt đầu từ [App.tsx](03-app/web/src/App.tsx) |
| App kiosk Android | [kiosk/src](03-app/kiosk/src), màn quét [k02-scan.tsx](03-app/kiosk/src/screens/k02-scan.tsx) |
| Backend FastAPI và AI | [hub/app](03-app/hub/app), bắt đầu từ [main.py](03-app/hub/app/main.py), nhận diện trong [recog](03-app/hub/app/recog) |
| Database và hợp đồng API | [db](03-app/db), [OpenAPI](03-app/openapi/openapi.yaml), [WebSocket](03-app/openapi/ws-protocol.md) |
| Yêu cầu và giao diện | [Đặc tả chính](03-app/dac-ta-app.md), [specs](03-app/docs/specs/README.md), [thiết kế UI](03-app/ui) |
| Tiến độ và bằng chứng | [Kế hoạch](03-app/plan-codex/README.md), [báo cáo kiểm thử](03-app/ket-qua-kiem-thu) |
| Chạy và review | [Test web](03-app/KICH-BAN-TEST-WEB.md), [demo chung](03-app/kich-ban-demo.md), [chạy demo và đo](03-app/ket-qua-kiem-thu/2026-11-16_T14/RUN-T14.md) |
| Tài liệu tham khảo | [Bàn giao](README-BAN-GIAO.md), [lịch sử thiết kế](03-app/docs/lich-su-thiet-ke/README.md), [mã và số liệu nghiên cứu](02-thuc-nghiem) |

Hub phục vụ cả web và kiosk. Dữ liệu PostgreSQL, ảnh/video cá nhân và bản lưu checkpoint trên máy nằm trong kho riêng `D:\WorkSpace\DATN\facegate-private`. Điểm nạp checkpoint khi chạy được mô tả trong [bàn giao](README-BAN-GIAO.md#2-checkpoint-file-mô-hình).
