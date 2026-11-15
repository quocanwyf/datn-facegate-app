# FG-AI-001 — Nạp mô hình đã xác minh

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-008 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.1, §4.3, §12 M0. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-14; K-11 khi chưa sẵn sàng.
- Task liên quan: T01, T02, T04 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-FACE-003](FG-FACE-003-duyet-ho-so-gallery.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Nạp mô hình đã xác minh trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Hub nội bộ; OWNER/HR xem model active. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_model; manifest/strip map/log BLUFR chỉ đọc.
- Đầu vào nghiệp vụ: best.pt V1s3; manifest row; strip map; nguồn log; DATN_CODE_DIR.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Kiểm sha256 bằng manifest
2. Nối source hash tới stripped/meta.sha256 qua strip map
3. Load strict qua load_backbone/verify_checkpoint
4. So meta.t_eq30 sai số<=1e-6
5. Nạp gallery/ghi runtime thực tế

## 5. Quy tắc nghiệp vụ và bất biến

- Chỉ UniFace+V1 R18 seed3 epoch18, không model COMPARISON
- Hash gốc120489621accefd7e78da9bd83fe3c6360ad94877e8ac4b9cdfa1038ec8eef88
- Không torch.save rồi so byte backbone
- CUDA fp16 autocast, CPU fallback ghi rõ chỉ kiểm thử
- Checkpoint không commit, không train lại
- Code nghiên cứu/vendor không sửa

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Theo Q-008, sai bất kỳ bước kiểm model thì dừng phần nhận dạng; không nhận dạng/mở cửa/ghi công bằng mặt. Giữ API kiểm tra trạng thái để báo lỗi, không coi API còn chạy là model đã sẵn sàng.
- Kiosk hiện “Máy chủ chưa sẵn sàng”; đặc tả §4.1 đã quy định dừng phần nhận dạng và giữ health chẩn đoán, không nới điều kiện kiểm.
- Thiếu checkpoint theo task triển khai phải xin An
- Không tự nới parity

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AI-001-AC01**: Có log4 bước cổng kiểm.
- **FG-AI-001-AC02**: Hash/manifest sai khiến model không sẵn sàng.
- **FG-AI-001-AC03**: Strict không thiếu/thừa khóa.
- **FG-AI-001-AC04**: Parity lớp bọc delta<=1e-5 theo M0.
- **FG-AI-001-AC05**: Runtime là phiên bản thật.

- **FG-AI-001-AC06**: Model chưa xác minh không xử lý nhận dạng hoặc mở cửa/ghi công bằng mặt; API kiểm tra trạng thái vẫn báo tình trạng lỗi theo Q-008.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
