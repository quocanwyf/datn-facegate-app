# FG-ATT-002 — Tính lại và chốt ngày công

- Phiên bản: 1.3 — 14/11/2026; bổ sung quyết định Q-010 của người dùng, giữ các quyết định trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §5.5; skill cham-cong-vn; DB §5–6. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-09; E-02/E-03/E-04; K-04.
- Task liên quan: T09, T10, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-ATT-001](FG-ATT-001-ca-phan-ca-ngay-le.md), [FG-ACCESS-001](FG-ACCESS-001-quyet-dinh-ra-vao.md), [FG-ATT-004](FG-ATT-004-cham-cong-ho.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Tính lại và chốt ngày công trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

Hub/Scheduler; người dùng đọc qua màn công. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: recognition_event, attendance_day, attendance_request, shift_assignment, holiday.
- Đầu vào nghiệp vụ: employee/work_date, event hợp lệ, APPROVED request, leave/holiday/timezone.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tìm ca hiệu lực
2. Lọc event theo cửa sổ ca[start−3h,end+4h]
3. check_in sớm nhất, check_out muộn nhất>=in+30 phút
4. Tính trạng thái/phút theo thứ tự
5. recompute khi event/duyệt/sửa/chốt
6. Scheduler finalize lúc end+4h

## 5. Quy tắc nghiệp vụ và bất biến

- Chỉ MATCH được phép tại ATTENDANCE_ACCESS và MANUAL_ATTENDANCE
- Tính theo múi giờ công ty/cửa sổ ca, không ngày lịch
- Ưu tiên HOLIDAY>LEAVE>OFF>NOT_STARTED>IN_PROGRESS>ABSENT>MISSING_OUT>nhóm đủ giờ
- Theo Q-008, ngày làm việc thông thường đã vào nhưng chưa chốt là IN_PROGRESS, hiển thị “Đang làm việc — tạm thời”; giữ ưu tiên HOLIDAY/LEAVE/OFF.
- NORMAL/LATE/EARLY/LATE_EARLY kết luận khi chốt theo quy tắc ngày công; không dùng ví dụ WS cũ ghi NORMAL ngay lúc vào để thay đổi luật.
- MISSING_OUT thiếu ra hoặc ra<end−2h, trường hợp sau suspect_forgot_out=true
- late=in>start+grace_in, early=end−2h<=out<end−grace_out
- Theo Q-010, worked_min chỉ tính trong ca và trừ phần giao với giờ nghỉ; lấy phần nguyên kết quả phút, không làm tròn timestamp trước khi so grace.
- recompute idempotent, giữ event. Theo Q-009, tự tính lại phải giữ giờ sửa thủ công hợp lệ và LEAVE đã đánh dấu.
- Ngày đã chốt nhận event muộn có occurred_at thuộc cửa sổ ca thì tính lại trên thời điểm xảy ra và giữ finalized=true; không dùng thời điểm nhận để đổi ngày công.
- Không kết luận thiếu công trước chốt

### Công thức theo Q-010

Các công thức dưới áp dụng sau khi chọn giờ hiệu lực (event/giải trình/sửa hợp lệ) và giữ quy tắc trạng thái, ưu tiên, MISSING_OUT đã chốt. Đây là yêu cầu thiết kế, chưa có kết quả chạy app.

- `late_min = floor((check_in - start)/60 giây)` nếu `check_in > start + grace_in`; ngược lại 0. Không trừ grace khỏi số phút sau khi đã vượt mức cho phép.
- Với ngày được phân loại về sớm theo luật hiện có, `early_min = floor((end - check_out)/60 giây)`; trong khoảng cho phép thì 0. Không dùng công thức này để biến MISSING_OUT thành EARLY.
- Với cặp giờ vào–ra hợp lệ: `a=max(check_in,start)`, `b=min(check_out,end)`; `gross=max(0,b-a)`; `rest` là thời lượng giao của `[a,b]` với khoảng nghỉ trong ca, bằng 0 nếu không có phần giao hoặc không có giờ nghỉ.
- `worked_min = floor(max(0,gross-rest)/60 giây)`. Chỉ lấy phần nguyên sau phép tính, không trừ toàn bộ giờ nghỉ nếu người đó chỉ làm một phần không giao với giờ nghỉ.
- So sánh grace bằng timestamp đầy đủ, không cắt giây trước phép so. Đến sớm/về muộn ngoài ca không tăng worked_min.
- `ngay_cong` là số cặp `(employee_id,work_date)` duy nhất có trạng thái hiệu lực thuộc NORMAL/LATE/EARLY/LATE_EARLY. Mỗi ngày tối đa 1; trạng thái khác theo dõi riêng, không quy đổi nửa ngày.
- Giải trình APPROVED cập nhật ngày công đó trước tổng hợp, không cộng thêm ngày theo số request hoặc event.

Ví dụ thiết kế: ca 08:30–17:30, nghỉ 12:00–13:00, grace vào/ra 10 phút. Vào 08:40 không muộn; vào 08:41 muộn 11 phút. Vào 08:00, ra 18:00 chỉ có 480 phút trong ca sau nghỉ; không cộng giờ ngoài ca. Các ví dụ không phải log nhận dạng/chấm công thực tế.

## 6. REST / tích hợp

Không có REST riêng cho xử lý nội bộ/WS này. Không tự tạo endpoint.

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Ngoài cửa sổ chỉ là ra vào
- Không ca OFF, lễ ưu tiên HOLIDAY
- Theo Q-009, ngày có ca thông thường chưa tới giờ/chưa quét hiển thị “Chưa bắt đầu”; đã tới giờ/chưa quét/chưa chốt hiển thị “Chưa đến — tạm thời”, không kết luận vắng sớm.
- Đến mốc chốt không có giờ vào thì ABSENT, giữ ưu tiên HOLIDAY/LEAVE/OFF. “Chưa đến — tạm thời” dùng WAITING_IN trong schema.sql/OpenAPI/status.json đã đồng bộ; check_in_at NULL và finalized=false.
- Event xảy ra ngoài cửa sổ chỉ ra vào; giữ timestamp gốc. Q-009 không bổ sung Kiosk gửi bù offline.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-ATT-002-AC01**: recompute cùng đầu vào không đổi kết quả.
- **FG-ATT-002-AC02**: ACCESS_ONLY không công.
- **FG-ATT-002-AC03**: out đúng in+30 phút được chọn.
- **FG-ATT-002-AC04**: Đúng grace không LATE/EARLY.
- **FG-ATT-002-AC05**: Ra<end−2h sau chốt ra MISSING_OUT/cờ.
- **FG-ATT-002-AC06**: Ngày lễ/không ca/giải trình kiểm riêng.

- **FG-ATT-002-AC07**: Ngày làm việc thông thường đã quét vào, trước chốt trả IN_PROGRESS/tạm thời; khi chốt mới kết luận nhóm NORMAL/LATE/EARLY/LATE_EARLY nếu đủ điều kiện.
- **FG-ATT-002-AC08**: HOLIDAY/LEAVE/OFF vẫn giữ ưu tiên; việc hiển thị tạm thời không biến các ngày đó thành IN_PROGRESS.

- **FG-ATT-002-AC09**: Ngày có ca chưa tới giờ/chưa quét hiện Chưa bắt đầu; đã tới giờ/chưa quét/chưa chốt hiện Chưa đến — tạm thời; tới chốt không có vào mới ABSENT, giữ các ưu tiên lễ/nghỉ/không ca.
- **FG-ATT-002-AC10**: recompute tự động không ghi đè giờ sửa thủ công hợp lệ hoặc LEAVE đã đánh dấu.
- **FG-ATT-002-AC11**: Event nhận muộn nhưng occurred_at trong cửa sổ ca được tính lại sau chốt, finalized vẫn true; ngoài cửa sổ không tham gia công.

- **FG-ATT-002-AC12**: Ca bắt đầu 08:30, grace 10 phút: vào 08:40 có late_min=0; vào 08:41 có late_min=11.
- **FG-ATT-002-AC13**: Phút làm việc không cộng phần ngoài ca và chỉ trừ phần giao thực tế với giờ nghỉ; lấy phần nguyên sau khi tính.
- **FG-ATT-002-AC14**: Một ngày đủ điều kiện có giải trình được duyệt chỉ tính 1 ngày công; trạng thái khác không tự quy đổi thành nửa ngày.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
