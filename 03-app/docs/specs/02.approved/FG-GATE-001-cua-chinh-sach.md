# FG-GATE-001 — Cửa, chính sách ra vào và ngưỡng từng cửa

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-001 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.4, §5.4, §6; admin.md W-07. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-07.
- Task liên quan: T06, T07, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-ORG-001](../03.archived/FG-ORG-001-phong-ban.md), [FG-AI-004](../03.archived/FG-AI-004-settings-nguong.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Cửa, chính sách ra vào và ngưỡng từng cửa trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER quản lý cửa; HR được sửa chính sách ra vào và danh sách phòng ban theo Q-001. Chưa cấp thêm quyền tạo cửa, đổi mode/ngưỡng hoặc quản trị thiết bị cho HR. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: gate, gate_allowed_department, threshold_profile.
- Đầu vào nghiệp vụ: Tên/mode/default_policy/threshold_level/custom_threshold; phòng ban được phép.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Xem/chọn/thêm cửa
2. Sửa chế độ và chính sách
3. Chọn phòng ban nếu DEPARTMENTS_ONLY
4. Chọn ngưỡng rồi lưu, hiển thị nguồn và danh sách thiết bị

## 5. Quy tắc nghiệp vụ và bất biến

- ATTENDANCE_ACCESS tính công, ACCESS_ONLY chỉ ra vào
- ALLOW_ALL_ACTIVE hoặc DEPARTMENTS_ONLY
- Mặc định ngưỡng DEFAULT_VAL cho cửa chấm công và STRICT_TEST cho cửa chỉ ra vào
- CUSTOM bắt buộc gate.custom_threshold trong [-1,1]
- Không khung giờ ra vào/relay thật/đa chi nhánh

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /gates` | `getGates` | OWNER, HR, SECURITY | `Gate` | 200, 400, 401, 403 |
| `POST /gates` | `postGates` | OWNER | `GateInput`, `Gate` | 201, 400, 401, 403, 409 |
| `PATCH /gates/{id}` | `patchGatesById` | OWNER, HR | `GateInput`, `Gate` | 200, 400, 401, 403, 404, 409, 422 |
| `PUT /gates/{id}/allowed-departments` | `putGatesAllowedDepartments` | OWNER, HR | `IdList`, `Gate` | 200, 400, 401, 403, 404 |


Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- CUSTOM thiếu/sai phạm vi bị chặn
- Không đủ quyền:403
- Theo Q-001, API/UI cần cho HR sửa chính sách và danh sách phòng ban, đồng thời giới hạn trường ngoài quyền.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-GATE-001-AC01**: Mode điều khiển đúng có/không tính công.
- **FG-GATE-001-AC02**: CUSTOM thiếu giá trị không lưu.
- **FG-GATE-001-AC03**: Phòng ban ngoài danh sách bị DENIED_RULE.
- **FG-GATE-001-AC04**: UI hiện giá trị và nhãn nguồn ngưỡng.

- **FG-GATE-001-AC05**: HR sửa được chính sách/danh sách phòng ban sau đồng bộ nguồn; không sửa mode/ngưỡng hoặc tạo cửa bằng quyền này.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
