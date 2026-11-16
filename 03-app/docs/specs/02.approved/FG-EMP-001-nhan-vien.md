# FG-EMP-001 — Hồ sơ và vòng đời nhân viên

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-002 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.1, §5.9, §6; admin.md W-03/W-04. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-03, W-04.
- Task liên quan: T03, T06, T07 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-001](../03.archived/FG-AUTH-001-xac-thuc-phien.md), [FG-ORG-001](../03.archived/FG-ORG-001-phong-ban.md), [FG-FACE-004](FG-FACE-004-xoa-rut-dong-y.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Hồ sơ và vòng đời nhân viên trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR ghi; MANAGER đọc team; các quyền đọc khác theo API. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: employee, department, user_account; hồ sơ mặt và công liên quan.
- Đầu vào nghiệp vụ: Mã/họ tên/email/SĐT/phòng ban/ngày vào làm; tùy chọn tạo tài khoản.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tìm/lọc tên mã, phòng ban, trạng thái, phương thức, hồ sơ
2. Thêm/sửa hồ sơ và tùy chọn tài khoản
3. Mở các tab thông tin/khuôn mặt/ca/công/sự kiện
4. Tạm khóa, mở khóa hoặc xác nhận nghỉ việc

## 5. Quy tắc nghiệp vụ và bất biến

- Mã duy nhất trong công ty
- ACTIVE/SUSPENDED/TERMINATED và FACE/MANUAL theo DB
- SUSPENDED giữ dữ liệu khuôn mặt hợp lệ và vẫn được định danh để trả DENY/INACTIVE theo Q-002; không được mở cửa hoặc tính công.
- TERMINATED có terminated_at, xóa sinh trắc và giữ công
- Đổi trạng thái cập nhật gallery trước khi API thành công
- Xác nhận nghỉ việc theo UI, không quy trình2 bước

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /employees` | `getEmployees` | OWNER, HR, MANAGER, SECURITY (Q-014, chỉ ACTIVE/MANUAL tối thiểu) | `EmployeeStatus`, `AttendanceMethod`, `PageEmployee` | 200, 400, 401, 403 |
| `POST /employees` | `postEmployees` | OWNER, HR | `EmployeeCreate`, `EmployeeCreated` | 201, 400, 401, 403, 409 |
| `GET /employees/{id}` | `getEmployeesById` | OWNER, HR, MANAGER | `Employee` | 200, 401, 403, 404 |
| `PATCH /employees/{id}` | `patchEmployeesById` | OWNER, HR | `EmployeeUpdate`, `Employee` | 200, 400, 401, 403, 404, 409 |
| `POST /employees/{id}/suspend` | `postEmployeesSuspend` | OWNER, HR | `Employee` | 200, 401, 403, 404, 422 |
| `POST /employees/{id}/reactivate` | `postEmployeesReactivate` | OWNER, HR | `Employee` | 200, 401, 403, 404, 422 |
| `POST /employees/{id}/terminate` | `postEmployeesTerminate` | OWNER, HR | `Employee` | 200, 401, 403, 404, 422, 503 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Trùng mã/phòng ban sai bị chặn
- Server lọc team
- Q-002 đã chốt hành vi định danh SUSPENDED để từ chối; quy tắc gallery đã đồng bộ trong nguồn chuẩn.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-EMP-001-AC01**: Danh sách đúng bộ lọc/phân trang/phạm vi.
- **FG-EMP-001-AC02**: Tạm khóa không xóa hồ sơ.
- **FG-EMP-001-AC03**: Nghỉ việc xóa sinh trắc giữ công.
- **FG-EMP-001-AC04**: MANAGER không đọc NV ngoài team.
- **FG-EMP-001-AC05**: Thay trạng thái có hiệu lực gallery theo nguồn đã chốt.

- **FG-EMP-001-AC06**: Tạm khóa nhân viên có hồ sơ hợp lệ vẫn nhận ra danh tính, ghi DENIED_INACTIVE, không mở cửa và không tính công.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.

## Q-014 — 16/11/2026

Người dùng chốt SECURITY chỉ tra cứu ACTIVE/MANUAL, trả id/mã/tên/phòng ban/trạng thái/phương thức để chấm hộ. GET chi tiết và các quyền ghi giữ nguyên; nhiều vai trò giữ quyền riêng. Căn cứ: chat và báo cáo T11.
