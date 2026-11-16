# FG-ACCESS-002 — Mở cửa thủ công mô phỏng

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **ARCHIVED — triển khai và nghiệm thu xong ngày 16/11/2026**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: T09/T10 và T11 `5b8b7af`; [báo cáo T11](../../../ket-qua-kiem-thu/2026-11-16_T11/bao-cao.md).
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §6; admin.md W-10; API gates/manual-open. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-10 Thao tác nhanh.
- Task liên quan: T06, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-GATE-001](../02.approved/FG-GATE-001-cua-chinh-sach.md), [FG-MON-001](FG-MON-001-giam-sat-canh-bao.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Mở cửa thủ công mô phỏng trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/SECURITY; HR chỉ xem giám sát. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_event MANUAL_OPEN, gate, user_account.
- Đầu vào nghiệp vụ: gate_id và reason theo schema.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Chọn cửa/nhập lý do
2. Server kiểm quyền
3. Ghi MANUAL_OPEN với người thực hiện và thời điểm
4. Hiện mở mô phỏng và đẩy event

## 5. Quy tắc nghiệp vụ và bất biến

- Lý do bắt buộc
- MANUAL_OPEN không chấm công
- Không relay vật lý
- Không thêm xác thực bằng ảnh

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `POST /gates/{id}/manual-open` | `postGatesManualOpen` | OWNER, SECURITY | `ManualOpenInput`, `Event` | 201, 400, 401, 403, 404 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Thiếu lý do/quyền/cửa không tồn tại theo contract

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ACCESS-002-AC01**: OWNER/SECURITY mở được và có event/lý do.
- **FG-ACCESS-002-AC02**: HR gọi mở bị từ chối.
- **FG-ACCESS-002-AC03**: Không tạo công từ MANUAL_OPEN.
- **FG-ACCESS-002-AC04**: Lịch sử giữ người/thời điểm.

Các AC đã đạt qua kiểm thử T09/T10/T11; xem báo cáo T11 và log liên quan. Fixture chỉ kiểm logic trong DB riêng; phép quét/đo realtime dùng ảnh thật đã đồng ý ngoài repo.
