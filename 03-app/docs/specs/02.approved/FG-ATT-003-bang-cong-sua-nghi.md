# FG-ATT-003 — Bảng công, sửa ngày công và đánh dấu nghỉ

- Phiên bản: 1.1 — 14/11/2026; bổ sung quyết định Q-009 của người dùng, giữ các quyết định trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.5/5.7, §6; admin.md W-09; skill cham-cong-vn. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-09, W-04 tab Công.
- Task liên quan: T06, T09, T10 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-ATT-002](FG-ATT-002-tinh-chot-cong.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Bảng công, sửa ngày công và đánh dấu nghỉ trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR ghi; MANAGER đọc team. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: attendance_day, employee, attendance_request, audit_log.
- Đầu vào nghiệp vụ: Tháng/phòng ban/NV; day_id/giờ sửa/reason; LeaveInput.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Xem lưới NV×ngày/tổng và chú giải
2. Mở drawer ca/giờ/event/nguồn
3. OWNER/HR sửa người khác có lý do
4. Đánh dấu nghỉ LEAVE
5. Tính lại/hiển thị kết quả

## 5. Quy tắc nghiệp vụ và bất biến

- Không ai sửa công mình kể cả OWNER
- Sửa source MANUAL và audit
- Ẩn nút sửa bản thân, server vẫn chặn
- Không khóa kỳ công MVP
- Theo Q-009, tự tính lại phải giữ giờ đã sửa thủ công hợp lệ và trạng thái LEAVE đã đánh dấu; không ghi đè bằng event mới hoặc job tự động.
- Trên ngày có ca thông thường chưa quét, UI phân biệt Chưa bắt đầu trước giờ ca, Chưa đến — tạm thời từ giờ ca tới trước chốt; không hiện Vắng trước khi chốt.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /attendance/days` | `getAttendanceDays` | OWNER, HR, MANAGER | `AttendanceStatus`, `PageAttendanceDay` | 200, 400, 401, 403 |
| `PATCH /attendance/days/{id}` | `patchAttendanceDaysById` | OWNER, HR | `AttendanceDayEdit`, `AttendanceDay` | 200, 400, 401, 403, 404, 422 |
| `POST /attendance/leave` | `postAttendanceLeave` | OWNER, HR | `LeaveInput`, `AttendanceDay` | 200, 400, 401, 403, 404 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- 403 SELF_EDIT_FORBIDDEN
- Giờ trái DB bị chặn
- Thiếu reason không lưu

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ATT-003-AC01**: MANAGER chỉ đọc team.
- **FG-ATT-003-AC02**: OWNER tự sửa bị 403.
- **FG-ATT-003-AC03**: Sửa người khác lưu MANUAL/audit.
- **FG-ATT-003-AC04**: Đánh dấu nghỉ thành LEAVE.
- **FG-ATT-003-AC05**: Drawer hiện nguồn và cờ quên ra.

- **FG-ATT-003-AC06**: Giờ sửa MANUAL/lý do/audit không bị mất hoặc bị event tự động ghi đè khi recompute.
- **FG-ATT-003-AC07**: LEAVE đã đánh dấu còn giữ khi có event mới hoặc chạy job tự tính lại.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
