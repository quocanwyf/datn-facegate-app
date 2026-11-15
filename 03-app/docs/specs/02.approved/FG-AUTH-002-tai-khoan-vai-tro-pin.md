# FG-AUTH-002 — Tài khoản, vai trò, mật khẩu tạm và PIN

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-011 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §6, §10.1; admin.md W-05; DB §4.1. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-05 tab Tài khoản; W-03 tạo kèm.
- Task liên quan: T03, T06, T07 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-001](FG-AUTH-001-xac-thuc-phien.md), [FG-ORG-001](FG-ORG-001-phong-ban.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Tài khoản, vai trò, mật khẩu tạm và PIN trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR quản trị; HR không sửa OWNER. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: user_account, user_role, auth_refresh_token.
- Đầu vào nghiệp vụ: Email, employee_id, trạng thái; danh sách vai trò/phòng ban; PIN4 số.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Xem/tạo tài khoản, hiển thị mật khẩu tạm một lần
2. Sửa trạng thái và đặt toàn bộ vai trò
3. MANAGER chọn phạm vi phòng ban
4. Đặt lại mật khẩu hoặc PIN cho OWNER/HR

## 5. Quy tắc nghiệp vụ và bất biến

- Email duy nhất không phân biệt hoa thường
- Một employee liên kết tối đa một tài khoản theo DB
- MANAGER bắt buộc scope_department_id, các vai trò khác không có scope
- PIN cá nhân OWNER/HR băm argon2id
- Server chặn HR sửa tài khoản OWNER

### Chuyển cấp khi nhiều vai trò — Q-011

Xét theo thứ tự vai trò của người gửi, chọn nhánh đầu tiên phù hợp:

1. Có OWNER (kể cả kiêm HR): HR khác người gửi duyệt.
2. Có HR nhưng không OWNER: OWNER khác người gửi duyệt.
3. MANAGER của chính phòng ban mình, không OWNER/HR: HR khác người gửi duyệt.
4. Còn lại: MANAGER đúng phòng ban người gửi, khác người gửi. MANAGER chỉ quản lý phòng khác nằm trong nhánh này khi tự gửi giải trình.

Luôn chặn tự duyệt ở server dù có nhiều vai trò. Không có người duyệt hợp lệ thì giữ PENDING, hiển thị cần bố trí người duyệt; không tự đổi nhóm hoặc tự duyệt. Quy tắc này chỉ dùng chọn nhóm người duyệt giải trình, không thay quyền tổng thể, không thêm push/endpoint/trường phân công vào contract trong bước ghi nhận quyết định.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /users` | `getUsers` | OWNER, HR | `PageUser` | 200, 400, 401, 403 |
| `POST /users` | `postUsers` | OWNER, HR | `UserCreate`, `User` | 201, 400, 401, 403, 409 |
| `PATCH /users/{id}` | `patchUsersById` | OWNER, HR | `UserUpdate`, `User` | 200, 400, 401, 403, 404 |
| `PUT /users/{id}/roles` | `putUsersRoles` | OWNER, HR | `RolesInput`, `User` | 200, 400, 401, 403, 404, 422 |
| `PUT /users/{id}/kiosk-pin` | `putUsersKioskPin` | OWNER, HR | `PinInput` | 204, 400, 401, 403, 404, 422 |
| `POST /users/{id}/reset-password` | `postUsersResetPassword` | OWNER, HR | `TempPassword` | 200, 401, 403, 404 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Email trùng hoặc phạm vi trái DB bị chặn
- Không trả PIN/hash khi đọc tài khoản
- Không hiển thị lại mật khẩu tạm sau lần trả ban đầu

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AUTH-002-AC01**: Tạo/reset trả mật khẩu tạm một lần.
- **FG-AUTH-002-AC02**: MANAGER thiếu phòng ban bị chặn.
- **FG-AUTH-002-AC03**: HR gọi trực tiếp sửa OWNER bị từ chối.
- **FG-AUTH-002-AC04**: Tài khoản nhiều phạm vi lưu đúng các dòng role.
- **FG-AUTH-002-AC05**: PIN không được trả dạng rõ sau lưu.

- **FG-AUTH-002-AC06**: Tài khoản nhiều vai trò giữ đủ các quyền đã cấp; chỉ áp thứ tự Q-011 khi chọn nhóm duyệt giải trình.
- **FG-AUTH-002-AC07**: OWNER kiêm HR không thể dùng vai trò HR để tự duyệt giải trình của mình.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
