# FG-ATT-005 — Xuất Excel bảng công tháng

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-010 của người dùng, giữ các quyết định trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.8, §6; skill cham-cong-vn. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-09.
- Task liên quan: T06, T09, T10 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-ATT-003](FG-ATT-003-bang-cong-sua-nghi.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Xuất Excel bảng công tháng trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR xuất theo phạm vi được phép; MANAGER được xuất Excel bảng công team theo Q-001, server giới hạn phòng ban thuộc scope quản lý. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: attendance_day, employee, department; file binary.
- Đầu vào nghiệp vụ: month=YYYY-MM; department_id theo contract.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Chọn tháng/phòng ban
2. Kiểm quyền
3. Tổng hợp ngày công hiệu lực
4. Trả bang-cong-YYYY-MM.xlsx
5. Kiểm2 sheet khi nghiệm thu

## 5. Quy tắc nghiệp vụ và bất biến

- Tổng hợp: mã/tên/phòng, ngày công, lần muộn, phút muộn/sớm, vắng/thiếu ra/nghỉ
- Chi tiết: NV/ngày/ca/in/out/trạng thái/nguồn/phút/ghi chú
- Ngày giờ kiểu Excel, dd/MM/yyyy và HH:mm
- Trạng thái tiếng Việt từ status.json
- Theo Q-010, tổng ngày công đếm cặp NV/ngày duy nhất thuộc NORMAL/LATE/EARLY/LATE_EARLY; mỗi ngày 1, không cộng thêm ngày cho giải trình APPROVED. Các trạng thái khác thống kê riêng, không quy đổi nửa ngày.
- Không khóa kỳ

Công thức chi tiết và ví dụ theo Q-010 tại [FG-ATT-002](../03.archived/FG-ATT-002-tinh-chot-cong.md#công-thức-theo-q-010); không cộng ngày riêng chỉ vì có giải trình.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /attendance/export` | `getAttendanceExport` | OWNER, HR, MANAGER |  | 200, 400, 401, 403 |


Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Sai tháng/quyền theo contract; MANAGER không được xuất dữ liệu ngoài team, kể cả tự sửa department_id.
- Không suy ra quyền EMPLOYEE tải Excel tổ chức từ quyền xem cá nhân

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ATT-005-AC01**: File đúng tên và 2 sheet.
- **FG-ATT-005-AC02**: Ngày giờ kiểu Excel và nhãn Việt.
- **FG-ATT-005-AC03**: Lọc phòng ban đúng.
- **FG-ATT-005-AC04**: Không lộ ngoài quyền.
- **FG-ATT-005-AC05**: Tổng hợp khớp chi tiết không đếm trùng.

- **FG-ATT-005-AC06**: MANAGER xuất được team sau đồng bộ nguồn; không có bộ lọc hoặc sửa bộ lọc cũng không lộ người ngoài scope.

- **FG-ATT-005-AC07**: Ngày có giải trình APPROVED được tính theo trạng thái hiệu lực, tối đa 1 ngày công, không cộng theo số request/event.
- **FG-ATT-005-AC08**: Sheet tổng hợp đối chiếu chi tiết theo công thức Q-010, phút muộn/sớm theo grace và worked_min chỉ trong ca trừ phần giao nghỉ.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
