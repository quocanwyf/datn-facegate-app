# FG-ME-001 — Hôm nay, công tháng và chi tiết cá nhân

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §9.2, §5.5; me.md. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: E-02, E-03, E-04; shell /me.
- Task liên quan: T06, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-ATT-002](../03.archived/FG-ATT-002-tinh-chot-cong.md), [FG-REQ-001](../03.archived/FG-REQ-001-tao-huy-giai-trinh.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Hôm nay, công tháng và chi tiết cá nhân trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

EMPLOYEE; MANAGER dùng trang cá nhân bên cạnh quyền team. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: employee, attendance_day, shift, recognition_event.
- Đầu vào nghiệp vụ: Danh tính token; month; date.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Hôm nay xem ca/in/out/trạng thái tạm
2. Xem lượt qua cửa
3. Chọn tháng xem lịch/4 KPI
4. Chạm ngày xem phút/nguồn/cờ quên ra
5. Gửi giải trình qua FG-REQ-001

## 5. Quy tắc nghiệp vụ và bất biến

- Chỉ dữ liệu bản thân
- ACCESS_ONLY ghi không tính công
- Không ca/lễ/MANUAL có thông điệp riêng
- Giờ trống dấu —, chưa chốt nhãn tạm thời
- Web360–430px, desktop max480
- Menu4mục, MANAGER thêm Duyệt
- Không push/PWA bắt buộc

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /me/today` | `getMeToday` | EMPLOYEE | `MeToday` | 200, 401, 403 |
| `GET /me/attendance` | `getMeAttendance` | EMPLOYEE | `MeMonth` | 200, 401, 403 |
| `GET /me/days/{date}` | `getMeDaysById` | EMPLOYEE | `MeDay` | 200, 401, 403 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Không gắn employee chuyển /admin
- Ngày có PENDING ẩn gửi/hiện trạng thái
- Lỗi theo hợp đồng

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ME-001-AC01**: Không đọc được ngày người khác.
- **FG-ME-001-AC02**: Chưa chốt có nhãn tạm.
- **FG-ME-001-AC03**: ACCESS_ONLY ghi không tính công.
- **FG-ME-001-AC04**: Lịch mở đúng ngày.
- **FG-ME-001-AC05**: Lễ/không ca/MANUAL đúng thông điệp.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
