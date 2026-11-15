# FG-MON-001 — Giám sát realtime và xử lý cảnh báo

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.3, §6; WS §2; admin.md W-10. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-10; W-02/W-07 nhận WS.
- Task liên quan: T05, T07, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-001](FG-AUTH-001-xac-thuc-phien.md), [FG-EVENT-001](FG-EVENT-001-su-kien-csv-bao-cao.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Giám sát realtime và xử lý cảnh báo trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/SECURITY thao tác; HR xem; MANAGER WS event team. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_event, event_handling, device, counters.
- Đầu vào nghiệp vụ: Auth access_token; event_id/status/linked_employee_id/note.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Auth message đầu WS
2. Nhận event/alert/device_status/counters/alert_handled
3. Hiện luồng và crop UNKNOWN/SPOOF
4. Chọn RESOLVED/FALSE_ALARM/IS_EMPLOYEE và lưu
5. Cập nhật các màn đang mở

## 5. Quy tắc nghiệp vụ và bất biến

- Server lọc phạm vi, không lọc client sau nhận
- IS_EMPLOYEE cần linked_employee_id
- Không thêm crop cảnh báo vào gallery
- MATCH không ảnh
- HR không handle/manual-open nhưng được chấm hộ theo feature riêng
- TOKEN_EXPIRED đóng4401, refresh rồi nối lại

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `POST /events/{id}/handle` | `postEventsHandle` | OWNER, SECURITY | `EventHandleInput`, `Event` | 200, 400, 401, 403, 404, 422 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Mất WS hiện dải đỏ
- Snapshot không còn theo404
- MANAGER không đọc crop qua REST

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-MON-001-AC01**: Không nhận event ngoài team/phạm vi.
- **FG-MON-001-AC02**: Event/alert cùng id không nhân đôi lịch sử.
- **FG-MON-001-AC03**: IS_EMPLOYEE thiếu NV bị chặn.
- **FG-MON-001-AC04**: HR handle bị 403.
- **FG-MON-001-AC05**: Handle không đổi gallery.
- **FG-MON-001-AC06**: Hết token refresh/nối lại.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
