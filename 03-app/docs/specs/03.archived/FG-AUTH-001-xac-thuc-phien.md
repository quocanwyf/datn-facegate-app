# FG-AUTH-001 — Đăng nhập, đổi mật khẩu và quản lý phiên

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **ARCHIVED — triển khai và nghiệm thu xong ngày 15/11/2026**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: T03/T05/T06 và T07 `eb13891`; [báo cáo T07](../../../ket-qua-kiem-thu/2026-11-15_T07/bao-cao.md).
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §6, §10.1; me.md E-01. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-01, E-01; menu tài khoản.
- Task liên quan: T03, T07, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: Không liệt kê phụ thuộc riêng.
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Đăng nhập, đổi mật khẩu và quản lý phiên trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Mọi tài khoản ACTIVE; login/refresh theo x-roles public. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: user_account, auth_refresh_token, user_role.
- Đầu vào nghiệp vụ: Email/mật khẩu; refresh token; mật khẩu cũ/mới theo schema.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Nhập email/mật khẩu và gửi login
2. Hub kiểm tài khoản và trả token/thông tin vai trò
3. Nếu must_change_password thì mở đổi mật khẩu lần đầu
4. Chọn /admin hoặc /me theo vai trò và liên kết employee
5. Refresh khi hết access token, logout thu hồi refresh token

## 5. Quy tắc nghiệp vụ và bất biến

- Hash mật khẩu bằng argon2id
- Access 15 phút, refresh 7 ngày và xoay vòng
- Đổi mật khẩu thu hồi refresh token
- Tài khoản nhiều vai trò, chỉ EMPLOYEE vào /me, quản trị không gắn employee vào /admin
- CORS chỉ origin Web, demo HTTP LAN

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `POST /auth/login` | `postAuthLogin` | public | `LoginRequest`, `TokenPair` | 200, 400, 401, 429 |
| `POST /auth/refresh` | `postAuthRefresh` | public | `RefreshRequest`, `TokenPair` | 200, 401 |
| `POST /auth/logout` | `postAuthLogout` | any | `RefreshRequest` | 204, 401 |
| `POST /auth/change-password` | `postAuthChangePassword` | any | `ChangePassword` | 204, 400, 401, 422 |
| `GET /me` | `getMe` | any | `UserMe` | 200, 401 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Sai thông tin hiển thị Email hoặc mật khẩu không đúng
- 429 hiển thị thử lại sau, không tự đặt chính sách khóa ngoài nguồn
- 403 khi không đủ quyền dù biết URL

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AUTH-001-AC01**: Đăng nhập hợp lệ trả đúng danh tính và vai trò.
- **FG-AUTH-001-AC02**: must_change_password mở luồng đổi lần đầu.
- **FG-AUTH-001-AC03**: Refresh đã xoay/thu hồi không dùng lại.
- **FG-AUTH-001-AC04**: Đăng xuất/đổi mật khẩu thu hồi refresh theo nguồn.
- **FG-AUTH-001-AC05**: API tài nguyên từ chối người thiếu quyền.

Các AC đã đối chiếu với log thật bên dưới. Không seed giả khuôn mặt, sự kiện nhận dạng hoặc ngày công.

## 9. Bằng chứng hoàn thành — 15/11/2026

| AC | Bằng chứng đã chạy |
|---|---|
| FG-AUTH-001-AC01 | T03 test_login_identity_and_contract; T07 5 role thật |
| FG-AUTH-001-AC02 | T03 test_must_change_password_reflects_database; T07 auth đổi lần đầu |
| FG-AUTH-001-AC03 | T03 concurrent_refresh/rotation/revocation; T07 session hai test |
| FG-AUTH-001-AC04 | T03 logout/change-password thu hồi; T07 auth logout/đổi mật khẩu |
| FG-AUTH-001-AC05 | T03/T06 ma trận quyền; T07 route/menu 5 vai trò |

Nguồn log: [T03](../../../ket-qua-kiem-thu/2026-11-15_T03/bao-cao.md), [T05](../../../ket-qua-kiem-thu/2026-11-15_T05/bao-cao.md), [T06](../../../ket-qua-kiem-thu/2026-11-15_T06/bao-cao.md), [T07](../../../ket-qua-kiem-thu/2026-11-15_T07/bao-cao.md). T07: 33 fixture + 10 Hub thật đạt, giữ log các lượt lỗi trước đó.
