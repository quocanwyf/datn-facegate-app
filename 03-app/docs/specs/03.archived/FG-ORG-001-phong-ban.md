# FG-ORG-001 — Quản lý phòng ban

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **ARCHIVED — triển khai và nghiệm thu xong ngày 15/11/2026**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: T03/T05/T06 và T07 `eb13891`; [báo cáo T07](../../../ket-qua-kiem-thu/2026-11-15_T07/bao-cao.md).
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §6; admin.md W-05; DB §4.1. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-05 tab Phòng ban.
- Task liên quan: T03, T06, T07 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-001](FG-AUTH-001-xac-thuc-phien.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Quản lý phòng ban trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR ghi; đọc theo từng operation. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: company, department, employee, user_role.
- Đầu vào nghiệp vụ: Tên phòng ban; id khi sửa.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tải danh sách phòng ban
2. Thêm tên phòng ban
3. Sửa tên, tải lại danh sách
4. Hiển thị nhân viên và quản lý tham chiếu

## 5. Quy tắc nghiệp vụ và bất biến

- Tên duy nhất trong công ty
- Quản lý phòng ban lấy từ user_role.scope_department_id
- Không thêm API xóa phòng ban vì nguồn chỉ có đọc/thêm/sửa

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /departments` | `getDepartments` | OWNER, HR, MANAGER, SECURITY | `Department` | 200, 400, 401, 403 |
| `POST /departments` | `postDepartments` | OWNER, HR | `DepartmentInput`, `Department` | 201, 400, 401, 403, 409 |
| `PATCH /departments/{id}` | `patchDepartmentsById` | OWNER, HR | `DepartmentInput`, `Department` | 200, 400, 401, 403, 404, 409 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Tên trùng/dữ liệu sai: lỗi hợp đồng
- Vai trò không quyền ghi bị từ chối

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ORG-001-AC01**: Thêm/sửa đúng tên.
- **FG-ORG-001-AC02**: Tên trùng bị chặn.
- **FG-ORG-001-AC03**: Không ghi phòng ban khi thiếu quyền.
- **FG-ORG-001-AC04**: Phạm vi MANAGER tham chiếu đúng phòng ban.

Các AC đã đối chiếu với log thật bên dưới. Không seed giả khuôn mặt, sự kiện nhận dạng hoặc ngày công.

## 9. Bằng chứng hoàn thành — 15/11/2026

| AC | Bằng chứng đã chạy |
|---|---|
| FG-ORG-001-AC01 | T06 admin_writes; T07 thêm/sửa tên thật |
| FG-ORG-001-AC02 | T07 test tên trùng trả 409, giữ form |
| FG-ORG-001-AC03 | T06 non_admin_write_routes_forbidden, 403 |
| FG-ORG-001-AC04 | T06 manager scope/role validation; T07 ảnh W05-departments và W05-users |

Nguồn log: [T03](../../../ket-qua-kiem-thu/2026-11-15_T03/bao-cao.md), [T05](../../../ket-qua-kiem-thu/2026-11-15_T05/bao-cao.md), [T06](../../../ket-qua-kiem-thu/2026-11-15_T06/bao-cao.md), [T07](../../../ket-qua-kiem-thu/2026-11-15_T07/bao-cao.md). T07: 33 fixture + 10 Hub thật đạt, giữ log các lượt lỗi trước đó.
