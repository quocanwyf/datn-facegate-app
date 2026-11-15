# FG-FACE-002 — Thu mẫu và tạo hồ sơ chờ duyệt

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-006 của người dùng, giữ các quyết định đã chốt trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.2, §4.2; WS §1.2–1.6. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-08, K-09; F-02.
- Task liên quan: T04, T05, T08 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-FACE-001](FG-FACE-001-dong-y-sinh-trac.md), [FG-AI-001](FG-AI-001-cong-kiem-mo-hinh.md), [FG-AI-002](FG-AI-002-pipeline-feature.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Thu mẫu và tạo hồ sơ chờ duyệt trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR có phiên; NV ACTIVE đã đồng ý. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: face_profile/sample/embedding/template; ảnh ngoài repo ở HUB_DATA_DIR.
- Đầu vào nghiệp vụ: mode=enroll, phiên, employee_id, JPEG.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Thu5 mẫu thẳng/trái/phải/ngẩng/cúi
2. Kiểm chất lượng và live nếu bật
3. Trả enroll_progress accepted/5
4. Đủ 5 mẫu trích embedding, template và so trùng STRICT_TEST
5. Đủ 5 mẫu hợp lệ và lưu thành công: tạo PENDING_REVIEW nếu chưa có; nếu đăng ký lại đã xác nhận thì thay bản chờ cũ bằng bộ mới, rồi trả enroll_done.
6. K-09 báo chờ duyệt, về K-02 sau5s

## 5. Quy tắc nghiệp vụ và bất biến

- Mẫu căn chỉnh112× 112, vector512 chiều L2
- Template=L2(mean embedding)
- PENDING chưa vào gallery. Khi chụp lại, bản chờ cũ giữ nguyên tới khi đủ 5 mẫu hợp lệ và lưu bộ mới thành công; sau thay vẫn tối đa một PENDING_REVIEW/nhân viên.
- Trùng nhân viên khác chỉ cảnh báo để quản trị duyệt
- Đăng ký lại giữ ACTIVE cũ tới khi bản mới duyệt, với điều kiện quyền/consent/trạng thái nhân viên còn hợp lệ.
- TOO_SIMILAR cos>0.98 là khởi đầu

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- NO_FACE/MULTI_FACE/TOO_SMALL/POSE/SPOOF/TOO_SIMILAR theo WS
- Hủy/hết phiên/mất mạng không tiếp tục phiên cũ; giữ bản chờ cũ nếu bộ mới chưa được lưu và hoàn tất thay thế. Lưu thất bại trước hoàn tất cũng giữ bản chờ cũ.
- Theo Q-006, đăng ký lại lỗi không thay bản cũ; chỉ gửi enroll_done khi lưu đủ dữ liệu bắt buộc thành công. Không báo hoàn tất khi còn lỗi. Dọn mẫu tạm phải bảo toàn hồ sơ cũ theo Q-004.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-FACE-002-AC01**: 5 mẫu hợp lệ tạo1PENDING_REVIEW.
- **FG-FACE-002-AC02**: Mẫu lỗi không tăng accepted.
- **FG-FACE-002-AC03**: Cảnh báo trùng lưu và hiện W-08.
- **FG-FACE-002-AC04**: Bản chờ không dùng chấm công.
- **FG-FACE-002-AC05**: Đăng ký lại chưa duyệt không thay ACTIVE.

- **FG-FACE-002-AC06**: Chụp lại chưa đủ 5 mẫu thì bản chờ cũ không thay đổi.
- **FG-FACE-002-AC07**: Đủ 5 mẫu hợp lệ và lưu thành công mới thay bản chờ, không để hai PENDING_REVIEW.
- **FG-FACE-002-AC08**: Hủy/hết phiên/mất mạng hoặc lưu bộ mới thất bại trước hoàn tất không làm mất bản chờ cũ; hồ sơ ACTIVE hợp lệ cũ vẫn dùng tới khi bản mới được duyệt.

- **FG-FACE-002-AC09**: Đăng ký lại lỗi không báo enroll_done thành công và không mất bản cũ theo Q-004.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
