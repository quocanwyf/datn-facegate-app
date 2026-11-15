# FG-AI-002 — Pipeline khung và trích đặc trưng

- Phiên bản: 1.1 — 14/11/2026; bổ sung quyết định Q-006 của người dùng, giữ các quyết định đã chốt trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.2–4.3; WS §1.3/1.5. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-02, K-08.
- Task liên quan: T01, T02, T04 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AI-001](FG-AI-001-cong-kiem-mo-hinh.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Pipeline khung và trích đặc trưng trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Worker Hub; device gửi khung. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: Khung trong bộ nhớ; model/template gallery.
- Đầu vào nghiệp vụ: JPEG, bbox/landmark, model/settings/gallery.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Giải mã BGR
2. YuNet score>=0.6 chọn bbox lớn nhất khi recognize
3. Kiểm bbox cạnh ngắn>=80 và abs(yaw_ratio)<=0.35
4. Liveness trên BGR gốc/bbox nếu bật
5. norm_crop rồi BGR2RGB/CHW uint8(1,3,112,112)
6. extract_features float32 L2(1,512)
7. Nhân template để top1 và chuyển quyết định

## 5. Quy tắc nghiệp vụ và bất biến

- Một worker suy luận, không PyTorch trên event loop
- 80px/yaw0.35 là cấu hình khởi đầu
- Phân biệt BGR liveness với RGB nhận dạng
- App chọn mặt lớn nhất, không pick_center_face kiểu LFW
- Enroll nhiều mặt bị loại theo WS
- Không lưu frame camera

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- NO_FACE/TOO_FAR/LOOK_STRAIGHT theo state
- Decode lỗi bỏ frame
- Theo Q-006, gallery không có hồ sơ đủ điều kiện thì Kiosk hiện “Chưa có dữ liệu khuôn mặt”; không kết luận UNKNOWN hay ghi cảnh báo người lạ chỉ vì gallery rỗng.
- Cập nhật gallery lỗi thì tạm ngưng nhận dạng đến khi phục hồi; không ra quyết định dựa trên gallery chưa cập nhật. Enrollment vẫn dùng luồng riêng.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AI-002-AC01**: Kiểm kênh màu BGR/RGB đúng.
- **FG-AI-002-AC02**: Feature shape/dtype/L2 đúng.
- **FG-AI-002-AC03**: Khung kém chất lượng không vào cửa sổ.
- **FG-AI-002-AC04**: Recognize chọn bbox lớn nhất còn enroll loại nhiều mặt.
- **FG-AI-002-AC05**: Worker không chặn event loop.

- **FG-AI-002-AC06**: Gallery rỗng hiển thị chưa có dữ liệu và không sinh sự kiện UNKNOWN/người lạ.
- **FG-AI-002-AC07**: Khi gallery cập nhật lỗi, không tiếp tục kết luận nhận dạng đến khi phục hồi.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
