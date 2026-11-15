# FG-AI-004 — Cấu hình nhận dạng và nguồn ngưỡng

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-007 của người dùng, giữ các quyết định trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.4–4.5; DB §6; admin.md W-14. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-14, W-07.
- Task liên quan: T02, T04, T06, T07 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AI-001](FG-AI-001-cong-kiem-mo-hinh.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Cấu hình nhận dạng và nguồn ngưỡng trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER sửa settings; OWNER/HR được xem cấu hình nhận dạng và model active theo quyết định Q-001. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: company.settings, threshold_profile, gate.custom_threshold, recognition_model, audit_log.
- Đầu vào nghiệp vụ: RecognitionSettings; ngưỡng cửa ở FG-GATE-001.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Đọc model/ngưỡng/source_ref
2. Hiện nhãn nguồn và đánh đổi BLUFR
3. OWNER sửa/xác nhận lưu
4. Ghi audit và gửi config khi đổi theo WS

## 5. Quy tắc nghiệp vụ và bất biến

- DEFAULT_VAL≈0.4233 chọn validation FAR1e-5
- STRICT_TEST≈0.4657 hiệu chỉnh tập test BLUFR sau báo cáo
- t_bs≈0.3736 chỉ tham khảo
- Ngưỡng nguồn sinh từ script đọc log, không gõ tay
- BLUFR gallery1000 không phải số đo văn phòng
- FPIR/FNIR DEFAULT5%/10.6%, STRICT1%/~16.4% dẫn từ nguồn
- Anti-spoof false/L null tới hiệu chỉnh T13. Theo Q-007, chỉ bật sau T13 và chốt L trong [0,1]; thiếu/sai L không được bật.
- window_size=W là số nguyên dương; match_min/unknown_min/spoof_min nguyên từ 1 đến W. Giữ mặc định W=5, MATCH=3, UNKNOWN=4, SPOOF=3.
- Cấu hình không hợp lệ bị từ chối và giữ toàn bộ cấu hình cũ, không lưu/áp dụng một phần. Server kiểm ràng buộc, UI kiểm sớm.
- Không màn so sánh mô hình

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /settings/recognition` | `getSettingsRecognition` | OWNER, HR | `RecognitionSettings` | 200, 400, 401, 403 |
| `PUT /settings/recognition` | `putSettingsRecognition` | OWNER | `RecognitionSettings` | 200, 400, 401, 403, 422 |
| `GET /models/active` | `getModelsActive` | OWNER, HR | `ModelActive` | 200, 400, 401, 403 |


Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Trái bounds/quan hệ cấu hình Q-007 trả lỗi, không đổi cấu hình cũ. OpenAPI đã ghi 422 khi bật anti-spoof với L NULL; các điều kiện bổ sung xem nguồn đã đồng bộ.
- Chưa hiệu chỉnh UI khóa L theo nguồn
- Q-001 đã đồng bộ: HR GET settings được phép; PUT vẫn chỉ OWNER.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AI-004-AC01**: UI hiện đủ nhãn nguồn.
- **FG-AI-004-AC02**: Không dùng t_bs vận hành.
- **FG-AI-004-AC03**: OWNER lưu và Kiosk nhận config.
- **FG-AI-004-AC04**: Vai trò khác không PUT settings.
- **FG-AI-004-AC05**: Không gán số BLUFR thành đo văn phòng.

- **FG-AI-004-AC06**: HR đọc cấu hình nhận dạng được sau đồng bộ nguồn; HR PUT cấu hình vẫn bị từ chối.

- **FG-AI-004-AC07**: Sau đồng bộ nguồn, chưa hiệu chỉnh T13 hoặc L thiếu/ngoài [0,1] thì không cho bật anti-spoof.
- **FG-AI-004-AC08**: W hoặc các số khung không nguyên/dương, hoặc ngưỡng khung lớn hơn W bị từ chối.
- **FG-AI-004-AC09**: Cấu hình không hợp lệ không thay bất kỳ giá trị nào của cấu hình cũ; mặc định vẫn 5/3/4/3.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
