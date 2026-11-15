# FG-KIOSK-002 — Phiên đăng ký bằng PIN HR

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-004 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.2, §10.1; kiosk.md K-05/K-06. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-05, K-06.
- Task liên quan: T05, T08 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AUTH-002](FG-AUTH-002-tai-khoan-vai-tro-pin.md), [FG-KIOSK-001](FG-KIOSK-001-camera-ket-noi.md), [FG-EMP-001](FG-EMP-001-nhan-vien.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Phiên đăng ký bằng PIN HR trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR có PIN; device đã ghép. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: user_account, device; phiên enroll theo hợp đồng.
- Đầu vào nghiệp vụ: user_id/PIN; từ khóa tìm employee ACTIVE.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Giữ góc phải K-02 trong3s
2. Tải enrollers chỉ tên/id, nhập PIN
3. Hub tạo phiên5 phút gắn người thực hiện
4. Chọn nhân viên ACTIVE, hiển thị hồ sơ hiện có

## 5. Quy tắc nghiệp vụ và bất biến

- PIN4 số, hash argon2id, khóa đơn giản sau5 lần sai trong15 phút
- K-05 không thao tác30s về K-02
- NV MANUAL vẫn cho chọn vì có thể đổi ý
- Có PENDING_REVIEW thì hỏi xác nhận trước khi đăng ký lại; từ chối xác nhận giữ nguyên bản chờ cũ.
- Theo Q-004, xác nhận chỉ cho bắt đầu chụp lại, không xóa/thay bản chờ ngay. Chỉ thay khi đủ 5 mẫu hợp lệ và lưu bản mới thành công.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /kiosk/enrollers` | `getKioskEnrollers` | device | `Enroller` | 200, 401 |
| `POST /kiosk/enroll/sessions` | `postKioskEnrollSessions` | device | `EnrollSessionCreate`, `EnrollSession` | 201, 400, 401, 403, 429 |
| `GET /kiosk/enroll/sessions/{id}/employees` | `getKioskEnrollSessionsEmployees` | device | `KioskEmployee` | 200, 401, 404, 422 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Sai PIN hiện lần còn lại/khóa
- SESSION_EXPIRED về K-02
- Không chọn NV ngoài ACTIVE

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-KIOSK-002-AC01**: PIN đúng mở phiên5 phút.
- **FG-KIOSK-002-AC02**: 5 lần sai khóa theo nguồn.
- **FG-KIOSK-002-AC03**: Danh sách enrollers không lộ PIN/hash.
- **FG-KIOSK-002-AC04**: Không thu mẫu với phiên hết hạn.
- **FG-KIOSK-002-AC05**: Không chọn được NV không ACTIVE.

- **FG-KIOSK-002-AC06**: Đã có PENDING_REVIEW thì hỏi trước khi đăng ký lại; không xác nhận không thay bản cũ.
- **FG-KIOSK-002-AC07**: Đã xác nhận nhưng hủy/hết phiên/mất mạng trước khi lưu bộ mới thành công thì bản chờ cũ còn nguyên.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
