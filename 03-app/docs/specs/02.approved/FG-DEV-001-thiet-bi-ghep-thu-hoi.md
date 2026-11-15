# FG-DEV-001 — Tạo, ghép và thu hồi thiết bị Kiosk

- Phiên bản: 1.1 — 15/11/2026 (chốt khóa lượt thử theo IP).
- Review/approved thay đổi 1.1: người dùng xác nhận trực tiếp trong chat ngày 15/11/2026: “Khóa IP nhập sai trong 10 phút; giữ cách nhập mã hiện tại, đổi thông báo thành khóa lượt thử từ máy này.” Giữ APPROVED sau xác nhận này; chưa nghiệm thu toàn bộ UI/SecureStore.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §6; admin.md W-07; kiosk.md K-01; WS §1.1. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-07, K-01.
- Task liên quan: T05, T06, T07, T08 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-GATE-001](FG-GATE-001-cua-chinh-sach.md), [FG-KIOSK-001](FG-KIOSK-001-camera-ket-noi.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Tạo, ghép và thu hồi thiết bị Kiosk trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER quản lý; thiết bị ghép bằng mã. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: device, gate.
- Đầu vào nghiệp vụ: Tên/gate_id; hub URL/mã 6 số; app_version.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. OWNER tạo thiết bị, nhận QR và mã 6 số có hạn10 phút
2. Kiosk quét QR chứa hub/code hoặc nhập tay
3. POST pair rồi lưu device_token/hub_url/gate vào SecureStore
4. Thu hồi thiết bị khi cần

## 5. Quy tắc nghiệp vụ và bất biến

- Device token chỉ thao tác cửa được gắn
- ACTIVE phải có token theo DB
- Demo không refresh device token
- Thu hồi khiến Kiosk xóa token/về K-01
- Máy ảo gọi Hub cùng máy qua http://10.0.2.2:8000

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /devices` | `getDevices` | OWNER | `Device` | 200, 400, 401, 403 |
| `POST /devices` | `postDevices` | OWNER | `DeviceCreate`, `DevicePairing` | 201, 400, 401, 403, 404 |
| `POST /devices/{id}/revoke` | `postDevicesRevoke` | OWNER | `Device` | 200, 401, 403, 404 |
| `POST /kiosk/pair` | `postKioskPair` | public | `PairRequest`, `PairResponse` | 200, 400, 404, 422, 429 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- PAIRING_EXPIRED422, PAIRING_INVALID404, PAIRING_LOCKED429 sau 5 lần sai: khóa lượt thử từ IP đó trong 10 phút, không khóa mã ghép; giữ request mã 6 số (người dùng chốt 15/11/2026)
- Lỗi mạng nhắc kiểm Hub/Wi-Fi
- DEVICE_REVOKED/TOKEN_INVALID xóa token

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-DEV-001-AC01**: Mã hợp lệ ghép đúng cửa và lưu SecureStore.
- **FG-DEV-001-AC02**: Mã hết hạn/sai/khóa trả đúng lỗi.
- **FG-DEV-001-AC03**: Thiết bị thu hồi không dùng WS hợp lệ.
- **FG-DEV-001-AC04**: Không thêm API refresh token thiết bị.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
