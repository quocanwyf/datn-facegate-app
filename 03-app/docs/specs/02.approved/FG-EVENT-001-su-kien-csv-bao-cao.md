# FG-EVENT-001 — Tra cứu sự kiện, CSV và báo cáo chấm hộ

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.6, §6; admin.md W-11; DB event. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-11; W-04 tab Sự kiện.
- Task liên quan: T06, T07, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-001](../03.archived/FG-AUTH-001-xac-thuc-phien.md), [FG-ATT-004](FG-ATT-004-cham-cong-ho.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Tra cứu sự kiện, CSV và báo cáo chấm hộ trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR/SECURITY; MANAGER event team; /me của mình. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_event, event_handling, user_account, employee.
- Đầu vào nghiệp vụ: Thời gian/cửa/kết quả/NV/người thực hiện; page/size.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Lọc danh sách
2. Xem thời gian/cửa/device/kết quả/NV/điểm/ngưỡng/khung/người/lý do
3. Xuất CSV cùng bộ lọc
4. Báo cáo chấm hộ theo người và số NV khác nhau

## 5. Quy tắc nghiệp vụ và bất biến

- Event chỉ thêm, không sửa điểm/xóa
- Ngoại lệ snapshot_path→NULL
- CSV chỉ cột/bộ lọc hợp đồng
- Không crop MATCH
- Báo cáo nhận biết lạm dụng, không tự kết luận vi phạm
- Quyền export/manual-report tra operation riêng

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /events` | `getEvents` | OWNER, HR, SECURITY, MANAGER | `EventResult`, `PageEvent` | 200, 400, 401, 403 |
| `GET /events/{id}/snapshot` | `getEventsSnapshot` | OWNER, HR, SECURITY |  | 200, 401, 403, 404 |
| `GET /events/manual-report` | `getEventsManualReport` | OWNER, HR, SECURITY | `ManualReportRow` | 200, 400, 401, 403 |
| `GET /events/export` | `getEventsExport` | OWNER, HR, SECURITY | `EventResult` | 200, 400, 401, 403 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Không trả ngoài phạm vi
- Crop chỉ OWNER/HR/SECURITY
- Ngày/bộ lọc sai theo contract

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-EVENT-001-AC01**: Tra cứu đúng lọc/phân trang/quyền.
- **FG-EVENT-001-AC02**: CSV không lộ ngoài quyền.
- **FG-EVENT-001-AC03**: Báo cáo lượt/NV khác nhau đối chiếu event.
- **FG-EVENT-001-AC04**: DB chặn UPDATE điểm/DELETE.
- **FG-EVENT-001-AC05**: Xóa sinh trắc giữ event và NULL crop.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
