# FG-ATT-001 — Ca, phân ca và ngày lễ

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.5, §6; DB shift/shift_assignment/holiday. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-06; W-04 tab Ca; E-02.
- Task liên quan: T06, T07, T09 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-EMP-001](FG-EMP-001-nhan-vien.md), [FG-ORG-001](FG-ORG-001-phong-ban.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Ca, phân ca và ngày lễ trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR ghi; đọc theo operation/phạm vi. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: shift, shift_assignment, holiday.
- Đầu vào nghiệp vụ: Tên/giờ ca/nghỉ/grace; employee hoặc department; weekday/từ–đến; ngày/tên lễ.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tạo/sửa ca
2. Phân ca từng thứ cho phòng ban/cá nhân với khoảng hiệu lực
3. Xem/xóa phân ca
4. Thêm/xóa ngày lễ theo năm

## 5. Quy tắc nghiệp vụ và bất biến

- Ca cùng ngày end>start, tối đa17h
- Nghỉ đủ 2giờ hoặc cùng NULL, nằm trong ca
- Phân ca đúng1employee/department, weekday1–7
- EXCLUDE chặn giao hiệu lực cùng đối tượng/thứ
- Cá nhân ưu tiên phòng ban
- Lễ toàn công ty

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /shifts` | `getShifts` | OWNER, HR, MANAGER | `Shift` | 200, 400, 401, 403 |
| `POST /shifts` | `postShifts` | OWNER, HR | `ShiftInput`, `Shift` | 201, 400, 401, 403, 409, 422 |
| `PATCH /shifts/{id}` | `patchShiftsById` | OWNER, HR | `ShiftInput`, `Shift` | 200, 400, 401, 403, 404, 422 |
| `GET /shift-assignments` | `getShiftAssignments` | OWNER, HR, MANAGER | `ShiftAssignment` | 200, 400, 401, 403 |
| `POST /shift-assignments` | `postShiftAssignments` | OWNER, HR | `ShiftAssignmentInput`, `ShiftAssignment` | 201, 400, 401, 403, 409 |
| `DELETE /shift-assignments/{id}` | `deleteShiftAssignmentsById` | OWNER, HR |  | 204, 401, 403, 404 |
| `GET /holidays` | `getHolidays` | any | `Holiday` | 200, 400, 401, 403 |
| `POST /holidays` | `postHolidays` | OWNER, HR | `Holiday` | 201, 400, 401, 403, 409 |
| `DELETE /holidays/{date}` | `deleteHolidaysById` | OWNER, HR |  | 204, 401, 403, 404 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- 409 ASSIGNMENT_OVERLAP
- Qua đêm/quá 17h/nghỉ không hợp lệ bị chặn
- Không thêm API sửa phân ca khi contract chỉ tạo/xóa

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ATT-001-AC01**: Ca qua đêm bị từ chối.
- **FG-ATT-001-AC02**: Giao phân ca bị 409.
- **FG-ATT-001-AC03**: Ca cá nhân thắng phòng ban.
- **FG-ATT-001-AC04**: Ngày lễ ra HOLIDAY.
- **FG-ATT-001-AC05**: Đọc ca đúng quyền/phạm vi.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
