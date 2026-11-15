# FG-FACE-001 — Đồng ý hoặc từ chối dùng khuôn mặt

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-005 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §0a, §5.2; kiosk.md K-07; DB employee. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-07; W-04/E-08 đọc trạng thái.
- Task liên quan: T05, T08, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-KIOSK-002](FG-KIOSK-002-phien-dang-ky-pin.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Đồng ý hoặc từ chối dùng khuôn mặt trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

NV quyết định; OWNER/HR thực hiện qua phiên. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: employee.face_consent_at, face_consent_by, attendance_method.
- Đầu vào nghiệp vụ: employee_id, agree, enroll_session_id.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Hiện mục đích/loại dữ liệu/nơi lưu/cách xóa và chấm hộ
2. Đồng ý ghi thời điểm/người thực hiện lần đồng ý mới rồi chụp; đăng ký lại vẫn giữ hồ sơ ACTIVE hợp lệ đến khi bản mới được duyệt.
3. Từ chối xóa sinh trắc hiện có theo FG-FACE-004, đặt face_consent_at/by cùng NULL và MANUAL; thông báo 4 giây rồi về K-02.

## 5. Quy tắc nghiệp vụ và bất biến

- Điều khoản cố định ngắn, không bảng/phiên bản consent
- Hai cột consent cùng NULL hoặc cùng có giá trị
- Không đồng ý không tạo hồ sơ; nếu đã có ACTIVE/PENDING thì xóa dữ liệu sinh trắc đó, loại khỏi gallery và chuyển MANUAL theo Q-005.
- Chỉ phiên có quyền và còn hạn ghi được consent

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `POST /kiosk/enroll/sessions/{id}/consent` | `postKioskEnrollSessionsConsent` | device | `ConsentInput`, `KioskEmployee` | 200, 400, 401, 404, 422, 503 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Hết phiên không ghi consent
- Theo Q-005, từ chối sau từng có hồ sơ cũng xóa sinh trắc/consent hiện hành và chuyển MANUAL; khác với chỉ hủy chụp giữ bản cũ theo Q-004.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-FACE-001-AC01**: Đồng ý ghi đúng thời điểm/người.
- **FG-FACE-001-AC02**: Từ chối chuyển MANUAL không ép chụp.
- **FG-FACE-001-AC03**: Có thông báo phương án lễ tân.
- **FG-FACE-001-AC04**: Không thêm quản trị điều khoản.

- **FG-FACE-001-AC05**: agree=false khi đã có hồ sơ xóa ACTIVE/PENDING và sinh trắc liên quan, đặt hai cột consent NULL và chuyển MANUAL.
- **FG-FACE-001-AC06**: Đồng ý đăng ký lại ghi thời điểm/người thực hiện mới, giữ hồ sơ ACTIVE hợp lệ đến khi bản mới được duyệt.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
