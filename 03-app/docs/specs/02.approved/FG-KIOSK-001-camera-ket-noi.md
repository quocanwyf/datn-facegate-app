# FG-KIOSK-001 — Camera, WebSocket và phục hồi kết nối

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-006 của người dùng, giữ các quyết định đã chốt trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) WS §1; kiosk.md K-02/K-04/K-11. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-02, K-04, K-11.
- Task liên quan: T05, T08, T14 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-DEV-001](FG-DEV-001-thiet-bi-ghep-thu-hoi.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Camera, WebSocket và phục hồi kết nối trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Kiosk đã ghép; mọi người qua cửa. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: device.last_seen_at; frame trong bộ nhớ, không lưu DB.
- Đầu vào nghiệp vụ: auth/device_token/app_version; JSON frame + binary JPEG; ping.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Auth message đầu trong5 giây, nhận config
2. Chụp camera trước, gửi JSON frame rồi binary JPEG ngay sau
3. Chờ phản hồi cùng seq rồi mới gửi tiếp
4. Hiện K-04 rồi quay về quét
5. Khi phát hiện ngắt kết nối, thử nối lại; sau 3 giây vẫn ngắt thì hiện K-11. Khi kết nối còn mở nhưng Hub im lặng 15 giây thì coi là mất kết nối và hiện K-11 ngay tại mốc đó.

## 5. Quy tắc nghiệp vụ và bất biến

- Không token trong URL
- seq tăng dần, Hub bỏ seq đã xử lý
- Khởi đầu max_fps4, cạnh dài640, JPEG80 từ config
- BUSY khi hàng đợi>2 khung/thiết bị, chờ 200ms
- Sau result không gửi frame trong result_display_sec mặc định3s
- Ping mỗi 10 giây khi không gửi frame.
- Theo Q-003: disconnect đã phát hiện mà sau 3 giây chưa nối lại thì hiện K-11. Không coi đây là timeout chờ phản hồi của một frame.
- Khi kết nối còn mở nhưng không nhận message/phản hồi Hub trong 15 giây kể từ lần nhận cuối: coi là mất kết nối, hiện K-11; không đợi thêm 3 giây.
- Preview trực tiếp được phép, không ảnh mẫu/crop trả về
- Khoảng chờ nối lại: 1 → 2 → 4 → 8 → 15 giây, duy trì tối đa 15 giây giữa các lần sau; hủy enrollment dở theo luồng nguồn.

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Q-006 đã đồng bộ WS/UI: gallery rỗng trả state NO_GALLERY, hiện “Chưa có dữ liệu khuôn mặt”; gallery cập nhật lỗi trả RECOGNITION_UNAVAILABLE và tạm ngưng nhận dạng, khôi phục theo config. Lỗi phản hồi frame có seq.
- Chưa có quyền camera: hướng dẫn mở cài đặt
- FRAME_DECODE_FAILED bỏ frame
- AUTH_TIMEOUT/BAD_MESSAGE theo WS
- MODEL_NOT_VERIFIED hiện máy chủ chưa sẵn sàng
- Disconnect phục hồi trước 3 giây không cần hiện K-11 vì lần ngắt đó; nếu kéo dài thì hiện K-11. Timeout im lặng 15 giây áp dụng độc lập như Q-003.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-KIOSK-001-AC01**: Không hai frame đồng thời chờ phản hồi.
- **FG-KIOSK-001-AC02**: Auth quá hạn/thu hồi bị đóng.
- **FG-KIOSK-001-AC03**: BUSY chờ trước gửi tiếp.
- **FG-KIOSK-001-AC04**: K-04 không ảnh và không gửi frame.
- **FG-KIOSK-001-AC05**: Nối lại không tiếp tục enroll dở.

- **FG-KIOSK-001-AC06**: Disconnect vẫn chưa phục hồi sau 3 giây hiện K-11; phục hồi trước mốc này không hiện K-11 vì lần ngắt đó.
- **FG-KIOSK-001-AC07**: Kết nối mở nhưng không nhận message từ Hub đủ 15 giây thì coi là mất kết nối và hiện K-11, không cộng thêm 3 giây.
- **FG-KIOSK-001-AC08**: Các khoảng chờ nối lại lần lượt 1, 2, 4, 8, 15 giây và không vượt 15 giây giữa các lần tiếp theo.

- **FG-KIOSK-001-AC09**: Gallery rỗng hiển thị “Chưa có dữ liệu khuôn mặt”, không hiển thị kết quả người lạ chỉ vì thiếu dữ liệu.
- **FG-KIOSK-001-AC10**: Gallery cập nhật lỗi được hiển thị tình trạng tạm ngưng nhận dạng theo hợp đồng đồng bộ; không hiển thị nhận dạng thành công từ dữ liệu chưa cập nhật.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
