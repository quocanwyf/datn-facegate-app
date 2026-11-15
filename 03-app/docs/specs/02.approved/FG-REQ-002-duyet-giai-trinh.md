# FG-REQ-002 — Duyệt hoặc từ chối giải trình

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-011 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.7, §6; admin.md W-12; me.md E-10. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-12, E-10.
- Task liên quan: T06, T09, T10, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-REQ-001](FG-REQ-001-tao-huy-giai-trinh.md), [FG-ATT-002](FG-ATT-002-tinh-chot-cong.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Duyệt hoặc từ chối giải trình trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

MANAGER đúng team, HR/OWNER theo chuyển cấp; không tự duyệt. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: attendance_request, attendance_day, user_role, audit_log.
- Đầu vào nghiệp vụ: request_id và ghi chú theo schema.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Xem chờ theo phạm vi
2. Đối chiếu giờ thực tế/đề nghị
3. Duyệt hoặc từ chối
4. Duyệt recompute dùng giờ đề nghị
5. Hiển thị kết quả/người/thời điểm

## 5. Quy tắc nghiệp vụ và bất biến

- Chỉ PENDING→APPROVED/REJECTED, CANCELLED do người gửi
- Người duyệt khác người gửi
- Theo Q-011, xét người gửi theo thứ tự OWNER → HR → MANAGER chính phòng mình → còn lại; chọn nhóm duyệt theo bảng chuyển cấp dưới đây.
- Từ chối bắt buộc ghi chú
- Duyệt source ADJUSTED giữ event gốc
- Ẩn nút tự duyệt và server chặn

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
| `GET /attendance/requests` | `getAttendanceRequests` | OWNER, HR, MANAGER | `RequestStatus`, `PageAttendanceRequest` | 200, 400, 401, 403 |
| `POST /attendance/requests/{id}/approve` | `postAttendanceRequestsApprove` | OWNER, HR, MANAGER | `ReviewInput`, `AttendanceRequest` | 200, 400, 401, 403, 404, 422 |
| `POST /attendance/requests/{id}/reject` | `postAttendanceRequestsReject` | OWNER, HR, MANAGER | `ReviewInput`, `AttendanceRequest` | 200, 400, 401, 403, 404, 422 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- 403 SELF_REVIEW_FORBIDDEN
- 422 NOT_PENDING theo approve contract
- Thiếu ghi chú reject bị chặn
- Không có người duyệt hợp lệ theo Q-011 thì giữ PENDING và báo cần bố trí người duyệt; không tự duyệt/không tự chuyển nhóm ngoài quy tắc.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-REQ-002-AC01**: MANAGER duyệt đúng NV team.
- **FG-REQ-002-AC02**: Tự duyệt API bị 403.
- **FG-REQ-002-AC03**: Approve áp giờ và ADJUSTED.
- **FG-REQ-002-AC04**: Reject không áp giờ.
- **FG-REQ-002-AC05**: Không duyệt lại bản đã xử lý.

- **FG-REQ-002-AC06**: Người gửi OWNER kiêm HR chỉ có HR khác duyệt; HR kiêm MANAGER không OWNER được OWNER khác duyệt.
- **FG-REQ-002-AC07**: MANAGER chính phòng mình gửi thì HR duyệt; MANAGER chỉ quản lý phòng khác gửi thì MANAGER đúng phòng người gửi duyệt.
- **FG-REQ-002-AC08**: Không có người duyệt hợp lệ giữ PENDING và hiển thị yêu cầu bố trí người duyệt; luôn chặn tự duyệt kể cả nhiều vai trò.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
