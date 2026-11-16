# T12 — Trang cá nhân `/me`

Ngày 16/11/2026: **đã triển khai E02/E03/E04/E05/E06/E08/E10; đạt AC1–AC4. AC5 ảnh Chrome Android còn chờ người dùng kiểm tra sau.** Không đánh dấu toàn bộ T12 đã nghiệm thu.

## Đã triển khai

- Khung tối đa 480 px, thanh trên 56 px, điều hướng dưới 64 px cố định, safe-area; MANAGER có tab Duyệt và số chờ. Quản trị không gắn NV chuyển về admin.
- Hôm nay: ca/lễ/không ca, giờ vào/ra, trạng thái tạm thời từ server, lượt qua cửa và ACCESS_ONLY “Không tính công”; làm mới khi mở lại/focus, nút làm mới và kéo xuống. GSAP lật giờ khi giá trị đổi, tắt theo reduced-motion.
- Lịch tháng, chấm màu từ status.json, chi tiết ngày/cờ quên ra/nguồn công; tổng tháng dùng summary từ API. Ngày có PENDING ẩn gửi giải trình.
- Gửi/hủy giải trình: lý do/giờ bắt buộc theo loại, định dạng dd/MM/yyyy và HH:mm, đổi sang ISO có offset theo giờ công ty; 409 giữ form, chặn gửi lặp.
- Dữ liệu khuôn mặt không hiện ảnh. Rút consent có xác nhận; lỗi xóa giữ hộp thoại/thử lại, nạp lại trạng thái MANUAL kể cả khi server trả 503, chỉ báo xong khi API thành công.
- Duyệt team theo quyền server và loại chính người duyệt, kể cả fixture trả can_review sai; từ chối bắt buộc ghi chú, bottom sheet trên điện thoại.
- Sửa thêm cache W02/W10 dùng chung key nhưng khác size: tách size trong query key để tổng quan luôn lấy đúng 10 sự kiện.

## Nghiệm thu

| AC | Kết quả |
|---|---|
| 1. 390×844 không tràn/thanh dưới chạm được | 5 browser tests pass, có ảnh E02/E03/E04/E05/E06/E08/E10 trong [screens](screens); đo scrollWidth và vị trí footer ở đáy viewport. |
| 2. E02 khớp DB 0/1/2 event | 3 PostgreSQL integration tests pass: đối chiếu id/status/finalized/giờ/phút và lượt qua cửa. Fixture rollback, không phải phép đo/quét người thật. [pytest-db.log](pytest-db.log). |
| 3. E10 không hiện chính người duyệt | Fixture can_review=true vẫn bị loại; ghi chú reject bắt buộc, đúng scope=team. Quy tắc Q011 và server tự duyệt tiếp tục có test T09. |
| 4. Rút consent → MANUAL/xóa sinh trắc | Browser + CPU Hub + DB/file thật trên **clone riêng T08**: 5 mẫu, 5 embedding, 1 template, 1 profile → 0; consent_at/by NULL. Giữ 5 event và 16 ngày công; file mẫu đã xóa. Nguồn T08 vẫn FACE/5 mẫu/1 template. [revoke-before.json](revoke-before.json), [revoke-after.json](revoke-after.json), [browser-real.log](browser-real.log). |
| 5. Chrome Android qua 10.0.2.2:5173/me | **CHƯA XÁC NHẬN**. AVD đã khởi động, web/Hub chạy sẵn; lệnh tự mở Chrome bị automatic approval review chặn “blocked by policy”. Người dùng chọn “Để tôi kiểm tra sau”. Không dùng ảnh Playwright desktop làm bằng chứng Android. |

Các kiểm khác: auth/session regression 19/19; monitor regression 3/3; typecheck, ESLint, production build đạt. Luồng gửi → PENDING → hủy → CANCELLED chạy qua giao diện và Hub thật trên clone T12, [browser-requests-real.log](browser-requests-real.log), ảnh E06-real-pending/cancelled. Lần chạy đầu test dùng nhãn “Khác” thay vì “Lý do khác” trong status.json nên timeout; đã sửa test và giữ log đầu để đối chiếu. Vite còn cảnh báo chunk >500 kB; chưa đo hiệu năng điện thoại. Không thay OpenAPI, DB schema hoặc mô hình tại T12.

Tạo clone bằng PostgreSQL TEMPLATE từ DB T08 đã đăng ký/duyệt ảnh thật, copy kho riêng vào LOCALAPPDATA/FaceGate/T12-*; không xuất ảnh hoặc vector vào Git. Dữ liệu chấm công ba trạng thái chỉ là fixture rollback trong DB test T11, được tách khỏi clone sinh trắc/browser thật.

## Review và phần còn lại

Kịch bản mở thủ công, tài khoản, checklist từng màn và cách chạy lại: [RUN-T12.md](RUN-T12.md).

T13 hiệu chỉnh chống giả mạo và T14 demo cần người dùng cùng thực hiện theo thỏa thuận; chưa bật chống giả mạo, chưa chọn ngưỡng L. T02 chờ chạy riêng trên laptop; T08 vẫn còn video toàn luồng và đo CPU thiết bị. Không tuyên bố toàn dự án đã nghiệm thu.
