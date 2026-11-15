# FG-SYS-001 — Sức khỏe Hub, phiên bản và giới hạn vận hành

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-013, giữ quyết định Q-008 trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §0a, §11–§14; API health/version; DB company. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: Header /admin, W-14, K-11.
- Task liên quan: T03, T14 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AI-001](FG-AI-001-cong-kiem-mo-hinh.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Sức khỏe Hub, phiên bản và giới hạn vận hành trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Public health/version theo API; người vận hành. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: Health/version response; company/timezone/settings; runtime log.
- Đầu vào nghiệp vụ: Cấu hình DB/model/data-dir; GET health/version.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Khởi động kiểm model và nạp gallery
2. Công bố health/version không nhạy cảm
3. Web/Kiosk hiện tình trạng
4. Đo kịch bản hiệu năng theo T14

## 5. Quy tắc nghiệp vụ và bất biến

- 1 công ty/1 cơ sở/1–3 cửa/10–200 NV
- HTTP/ws LAN không tên miền/TLS
- Theo Q-013, demo dùng một công ty từ seed và timezone cố định Asia/Ho_Chi_Minh; timestamp DB vẫn timestamptz.
- Web/Kiosk hiện tên công ty và ngày giờ theo timezone công ty, không dùng timezone máy người xem để đổi ngày công.
- HUB_DATA_DIR ngoài repo
- Mục tiêu p95 khung<150ms RTX3050, kết quả<2s,3 Kiosk+5web chưa phải số đo
- Không thêm màn hình/API sửa company/timezone trong demo. Dòng “Công ty” trong ma trận quyền không cấp phạm vi tạo thêm CRUD công ty.
- Không seed giả mặt/event/công

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /health` | `getHealth` | public | `Health` | 200 |
| `GET /version` | `getVersion` | public |  | 200 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Theo Q-008, model chưa xác minh không tuyên bố ready, tạm ngừng nhận dạng/mở cửa/ghi công bằng mặt; giữ API kiểm tra trạng thái để báo lỗi.
- API kiểm tra còn chạy không đồng nghĩa nhận dạng sẵn sàng; khi model chưa xác minh, Health phản ánh model_verified=false và trạng thái không sẵn sàng theo hợp đồng đã đồng bộ.
- Kiosk hiển thị “Máy chủ chưa sẵn sàng”. Không cam kết các chức năng quản trị khác hoạt động khi DB/Hub lỗi.
- Mất DB/Hub hiện lỗi thật
- Không mở rộng TLS/BitLocker/push/multi-company

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-SYS-001-AC01**: Health/version đúng schema không lộ secret.
- **FG-SYS-001-AC02**: Khởi động lại kiểm hash/nạp gallery tự động.
- **FG-SYS-001-AC03**: Đo có config/log thật p50/p95.
- **FG-SYS-001-AC04**: Sinh trắc không trong repo.

- **FG-SYS-001-AC05**: Lỗi xác minh model vẫn có thể kiểm tra tình trạng qua API và Kiosk hiện máy chủ chưa sẵn sàng; không nhận dạng/mở cửa/ghi công bằng mặt.

- **FG-SYS-001-AC06**: Demo lấy công ty từ seed; Web/Kiosk dùng tên công ty và ngày giờ Asia/Ho_Chi_Minh kể cả khi máy người xem dùng timezone khác.
- **FG-SYS-001-AC07**: Không có màn hình/API sửa công ty/timezone được bổ sung ngoài phạm vi demo đã chốt.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
