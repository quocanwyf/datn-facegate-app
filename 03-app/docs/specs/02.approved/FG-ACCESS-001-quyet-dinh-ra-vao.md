# FG-ACCESS-001 — Cho phép hoặc từ chối ra vào

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-002 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.3–5.4; WS §1.4. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-04; F-03.
- Task liên quan: T04, T05, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-GATE-001](FG-GATE-001-cua-chinh-sach.md), [FG-AI-003](../03.archived/FG-AI-003-bo-quyet-dinh.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Cho phép hoặc từ chối ra vào trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Nhân viên; Hub kiểm chính sách cửa. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_event, employee, gate, gate_allowed_department.
- Đầu vào nghiệp vụ: MATCH id/score từ AI; cửa/trạng thái NV.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Kiểm trạng thái NV
2. Kiểm chính sách phòng ban
3. Kiểm cooldown
4. Ghi MATCH hoặc DENIED_RULE/DENIED_INACTIVE
5. Mô phỏng mở cửa, tính công nếu đúng mode
6. Đẩy monitor và kết quả Kiosk

## 5. Quy tắc nghiệp vụ và bất biến

- Theo Q-002, SUSPENDED có dữ liệu khuôn mặt hợp lệ vẫn được nhận ra, ghi DENIED_INACTIVE và trả DENY/INACTIVE; không mở cửa và không tính công.
- TERMINATED không gallery
- MATCH có door_action OPEN, không ảnh
- ACCESS_ONLY không tạo công
- Không relay/khóa điện thật

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Ngoài phòng ban trả DENY/RULE
- Tạm khóa trả DENY/INACTIVE, hiện “Tài khoản đang tạm khoá”; không áp chính sách ALLOW_ALL_ACTIVE để cho qua.
- UNKNOWN/SPOOF không employee

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ACCESS-001-AC01**: NV đúng quyền được MATCH.
- **FG-ACCESS-001-AC02**: Ngoài quyền bị DENIED_RULE.
- **FG-ACCESS-001-AC03**: ACCESS_ONLY chỉ ra vào.
- **FG-ACCESS-001-AC04**: MATCH không snapshot.
- **FG-ACCESS-001-AC05**: Cooldown không event trùng.

- **FG-ACCESS-001-AC06**: SUSPENDED được nhận ra có DENIED_INACTIVE, door=DENY, không có công từ lượt quét này; Kiosk hiện thông báo tài khoản tạm khóa.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
