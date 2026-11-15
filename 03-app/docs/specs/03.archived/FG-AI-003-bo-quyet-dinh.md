# FG-AI-003 — Bộ quyết định đa khung và cooldown

- Phiên bản: 1.0 — 14/11/2026.
- Trạng thái: **ARCHIVED — triển khai và nghiệm thu xong ngày 15/11/2026**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: T04 `c110df6`, T05 `ed90ab6`; [báo cáo T04](../../../ket-qua-kiem-thu/2026-11-15_T04/bao-cao.md), [báo cáo T05](../../../ket-qua-kiem-thu/2026-11-15_T05/bao-cao.md).
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.5; WS §1.4. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: K-02, K-04; F-03.
- Task liên quan: T04, T05, T14 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-AI-002](../02.approved/FG-AI-002-pipeline-feature.md), [FG-AI-004](../02.approved/FG-AI-004-settings-nguong.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Bộ quyết định đa khung và cooldown trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Hub theo từng thiết bị. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: Cửa sổ bộ nhớ; recognition_event khi kết luận.
- Đầu vào nghiệp vụ: valid/live/id/score/bbox/t; tau cửa và settings.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Thêm khung hợp lệ vào cửa sổ tối đa5
2. Reset khi liên tục không hợp lệ>1s hoặc IoU<0.3
3. Xét SPOOF rồi MATCH rồi UNKNOWN
4. Kết luận xóa cửa sổ, hiển thị 3s
5. Kiểm cooldown nghiệp vụ trước ghi event

## 5. Quy tắc nghiệp vụ và bất biến

- live=p_live>=L và match=score>=tau
- SPOOF>=3 khung không live
- MATCH>=3 khung live cùng id, điểm TB các khung đó
- UNKNOWN đủ 5, >=4live không khớp và không id>=2live khớp
- INVALID không vào cửa sổ
- Cùng NV/cửa60s trả ALREADY không event, cảnh báo/cửa15s
- Các số đều cấu hình khởi đầu

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Chưa đủ luật tiếp tục gom
- Người mới reset trước thêm frame
- ALREADY không tạo MATCH mới

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-AI-003-AC01**: Điểm bằng tau và p_live bằng L được chấp nhận.
- **FG-AI-003-AC02**: 3 LA ra MATCH A,3 NL ra SPOOF.
- **FG-AI-003-AC03**: UNKNOWN đúng luật5 khung.
- **FG-AI-003-AC04**: Vét cạn chuỗi dài1–8 trên INVALID/NL/LA/LB/LN đối chiếu tham chiếu độc lập.
- **FG-AI-003-AC05**: Cooldown không tăng event.

Các AC đã nghiệm thu:

| AC | Bằng chứng thật |
|---|---|
| AC01–AC03 | Test đúng bằng tau/L, MATCH/SPOOF/UNKNOWN và ưu tiên, [log T04](../../../ket-qua-kiem-thu/2026-11-15_T04/pytest.log) |
| AC04 | 488.280 chuỗi × 3 biến thể = 1.464.840, tham chiếu độc lập, log T04 và [hồi quy T05](../../../ket-qua-kiem-thu/2026-11-15_T05/pytest-full.log) |
| AC05 | 1 OK + 2 ALREADY nhưng chỉ 1 MATCH; [summary thật](../../../ket-qua-kiem-thu/2026-11-15_T05/real-run-03/summary.json), [event DB](../../../ket-qua-kiem-thu/2026-11-15_T05/real-run-03/events.json) |

Đây là nghiệm thu chức năng bộ quyết định/cooldown. T14 vẫn kiểm demo tích hợp toàn hệ thống; các chức năng UI khác giữ trạng thái riêng. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
