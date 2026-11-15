# Chuyển thư mục dự án — 15/11/2026

- Thư mục chính: `D:\WorkSpace\DATN\datn-facegate-app`.
- Nguồn: `C:\Users\NMinH\OneDrive\Desktop\code\datn-facegate-app`.
- Đối chiếu trước khi chuyển nguồn: 55.924 tệp, 1.353.469.470 byte; SHA-256 khớp toàn bộ. Xem `verification.json`.
- Giữ nguyên HEAD `12d8581dd201fd4f5a5b8d8b194f2eab17bd2a5c`, trạng thái Git và nội dung chưa commit, bao gồm phần T07 đang làm.
- Giữ `.env` và checkpoint ngoài Git; checkpoint khớp manifest tại đường dẫn mới.
- Khôi phục liên kết phụ thuộc; cài lại Node bằng lockfile và Python bằng đúng 71 phiên bản đã có. Vite, uvicorn, Alembic chạy được. Web/Kiosk typecheck exit 0.
- PostgreSQL vẫn dùng dữ liệu cũ tại AppData, port 5433; đã khởi động lại và chuyển log ra ngoài repo. `pg_isready`: accepting connections.
- Giữ nguyên U03, U04 và `datn-cv-facerecognition` bên cạnh dự án.
- Bản sao lưu phục vụ chuyển thư mục nằm ở `D:\WorkSpace\DATN\.facegate-migration-backup-20261115`; gồm các phần nguồn đã chuyển và cache cũ. Không dùng các bản sao lưu làm thư mục phát triển.
- Nhật ký đầy đủ và manifest SHA từng tệp: `%LOCALAPPDATA%\FaceGate\migration-20261115` (ngoài Git).
- Nguồn OneDrive không còn tệp hoặc liên kết; chỉ còn thư mục gốc rỗng do tiến trình đang giữ working directory. Xem `source-cleanup.json`.

Việc chuyển thư mục không đánh dấu T07 hoàn thành. Hai lần E2E trước đó còn lỗi kiểm thử; giữ nguyên log thật, tiếp tục sửa/kiểm trên thư mục chính ở ổ D.
