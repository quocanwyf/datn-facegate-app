# Lịch sử review và approved specs

## APPROVED 2026-11-14

- Người review: người dùng giao việc trong chat này.
- Người approved: người dùng giao việc trong chat này.
- Ngày ghi nhận xác nhận: 14/11/2026, múi giờ Asia/Bangkok. Ngày thực hiện review trước đó không được cung cấp riêng.
- Căn cứ: tin nhắn trực tiếp của người dùng: “tôi đã review và duyệt tất cả các specs trong file draft”.
- Phạm vi: toàn bộ 32 file `FG-*.md` có trong `01.draft` tại thời điểm xác nhận, phiên bản tài liệu 1.0.
- Thực hiện: giữ mã/tên và nội dung nghiệp vụ, cập nhật metadata thành `APPROVED`, chuyển sang `02.approved`, cập nhật liên kết trong specs/mục lục/ma trận.
- Chưa xác nhận triển khai hoặc nghiệm thu; không chuyển file vào `03.archived`.
- Các Q trong `CAN-CHOT.md` giữ nguyên: tin nhắn duyệt không cung cấp phương án cụ thể để tự sửa các điểm khác biệt của nguồn chuẩn.

### Các mã được duyệt

| Nhóm | Mã tính năng |
|---|---|
| Xác thực | FG-AUTH-001, FG-AUTH-002 |
| Tổ chức và nhân viên | FG-ORG-001, FG-EMP-001 |
| Cửa và thiết bị | FG-GATE-001, FG-DEV-001 |
| Kiosk | FG-KIOSK-001, FG-KIOSK-002 |
| Khuôn mặt | FG-FACE-001, FG-FACE-002, FG-FACE-003, FG-FACE-004 |
| AI | FG-AI-001, FG-AI-002, FG-AI-003, FG-AI-004, FG-AI-005 |
| Ra vào | FG-ACCESS-001, FG-ACCESS-002 |
| Chấm công | FG-ATT-001, FG-ATT-002, FG-ATT-003, FG-ATT-004, FG-ATT-005 |
| Giải trình | FG-REQ-001, FG-REQ-002 |
| Cá nhân và tổng quan | FG-ME-001, FG-DASH-001 |
| Giám sát và sự kiện | FG-MON-001, FG-EVENT-001 |
| Nhật ký và vận hành | FG-AUDIT-001, FG-SYS-001 |

Vị trí hiện tại của từng spec tra tại [mục lục](README.md). Khi chuyển trạng thái tiếp theo, thêm lịch sử mới và giữ bản ghi xác nhận này.

## Quyết định Q-001 — 14/11/2026

- Người dùng xác nhận “1. có; 2. có; 3. có” tương ứng: MANAGER xuất Excel team; HR xem cấu hình nhận dạng; HR sửa chính sách ra vào của cửa.
- Cập nhật được duyệt trực tiếp trong chat: FG-GATE-001, FG-AI-004, FG-ATT-005 lên phiên bản 1.1, giữ `APPROVED`.
- Phạm vi chi tiết và phần API/UI cần đồng bộ ghi tại [Q-001](CAN-CHOT.md#q-001--quyền-api-khác-ma-trận-nghiệp-vụ). Chưa sửa nguồn chuẩn hoặc triển khai code, chưa có nghiệm thu app cho quyết định này.

## Quyết định Q-002 — 14/11/2026

- Người dùng trả lời “chọn 1”: vẫn nhận ra nhân viên tạm khóa, thông báo tài khoản đang tạm khóa và từ chối mở cửa/chấm công.
- FG-EMP-001, FG-FACE-003, FG-ACCESS-001 cập nhật lên phiên bản 1.1 theo xác nhận trực tiếp, giữ `APPROVED`.
- Ghi `DENIED_INACTIVE` khi nhận ra nhân viên SUSPENDED; không biến sự kiện bị từ chối thành công chấm công hoặc mở cửa.
- Cần đồng bộ quy tắc gallery trong nguồn chuẩn. Quyết định này xác định hành vi; chưa lựa chọn kiến trúc gallery chung/phụ, chưa triển khai hoặc nghiệm thu.

## Quyết định Q-003 — 14/11/2026

- Người dùng trả lời “đồng ý” với đề xuất: disconnect chưa phục hồi sau 3 giây thì hiện màn mất kết nối; kết nối mở nhưng Hub im lặng 15 giây thì coi là mất kết nối; nối lại với khoảng chờ 1/2/4/8 giây, tối đa 15 giây giữa các lần thử.
- FG-KIOSK-001 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ `APPROVED`.
- Ghi rõ hai mốc độc lập: timeout im lặng 15 giây không cộng thêm khoảng chờ disconnect 3 giây. Ping 10 giây khi không có frame theo giao thức hiện có.
- Chưa sửa nguồn UI/WS hoặc code; các AC kết nối mới là dự kiến, chưa chạy nghiệm thu app.

## Quyết định Q-004 — 14/11/2026

- Người dùng trả lời “đồng í” với phương án: hỏi xác nhận đăng ký lại, giữ bản chờ cũ khi chụp, chỉ thay khi đủ 5 mẫu hợp lệ và lưu bản mới thành công; hủy/hết phiên/mất mạng giữ bản cũ; ACTIVE cũ giữ đến khi duyệt mới.
- FG-KIOSK-002 và FG-FACE-002 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ `APPROVED`.
- Quyết định xác định vòng đời quan sát được, không bổ sung API hoặc tự chọn cơ chế phục hồi file/DB đang thuộc Q-006. Chưa triển khai/nghiệm thu.

## Quyết định Q-005 — 14/11/2026

- Người dùng trả lời “đồng ý” với bảng xử lý: từ chối/rút đồng ý hoặc xóa hành chính đều xóa sinh trắc, xóa thông tin consent hiện hành và chuyển MANUAL; dùng mặt lại cần đồng ý/đăng ký lại. Đồng ý đăng ký lại ghi consent mới, giữ hồ sơ đang hoạt động đến khi duyệt bản mới. Xóa giữ công và event gốc.
- FG-FACE-001 và FG-FACE-004 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ `APPROVED`.
- Ghi rõ hai cột consent cùng NULL khi từ chối/rút/xóa, crop liên kết bị xóa và snapshot_path NULL; audit nghiệp vụ vẫn theo nguồn.
- Chưa sửa nguồn chuẩn/code hoặc nghiệm thu app; phục hồi lỗi còn Q-006.

## Quyết định Q-006 — 14/11/2026

- Người dùng trả lời “đồng ý” với sáu ý: chỉ thành công khi hoàn tất; đăng ký lại lỗi giữ bản cũ; rút/xóa ngừng nhận dạng ngay cả khi xóa file lỗi và cho thử lại; gallery lỗi tạm ngưng nhận dạng; duyệt đồng thời chỉ một lần; gallery rỗng báo chưa có dữ liệu, không tạo cảnh báo người lạ.
- FG-FACE-002/003/004 và FG-KIOSK-001 lên phiên bản 1.2; FG-AI-002 lên phiên bản 1.1; giữ APPROVED theo xác nhận trực tiếp.
- Đây là hành vi phục hồi đã duyệt, không tự lựa chọn giao dịch file/DB hoặc bổ sung mã lỗi/endpoint. Cần đồng bộ hợp đồng và UI trước triển khai phần thay đổi; chưa chạy nghiệm thu app.

## Quyết định Q-007 — 14/11/2026

- Người dùng trả lời “đồng ý”: chỉ bật anti-spoof sau T13/chốt L; L thuộc [0,1], không bật nếu thiếu/sai; số khung MATCH/UNKNOWN/SPOOF nguyên trong [1,W]; giữ mặc định 5/3/4/3; cấu hình sai bị từ chối và giữ cấu hình cũ.
- FG-AI-004 lên phiên bản 1.2, FG-AI-005 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ `APPROVED`.
- Chưa chọn giá trị L cụ thể, chưa thay yêu cầu hiệu chỉnh T13; chưa sửa nguồn chuẩn hoặc code, chưa nghiệm thu app.

## Quyết định Q-008 — 14/11/2026

- Người dùng trả lời “đồng ý”: model chưa xác minh không nhận dạng/mở cửa/ghi công bằng mặt; giữ API kiểm tra để báo lỗi và Kiosk báo máy chủ chưa sẵn sàng; ngày làm việc thông thường đã vào nhưng chưa chốt hiển thị IN_PROGRESS/tạm thời; nhóm NORMAL/LATE/EARLY/LATE_EARLY kết luận khi chốt và sửa ví dụ WS cũ.
- FG-AI-001, FG-SYS-001, FG-ATT-002 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ APPROVED.
- Cần đồng bộ nguồn về cổng khởi động/health/WS/UI; không nới kiểm model, không xác nhận code đã chạy hoặc nghiệm thu.

## Quyết định Q-009 — 14/11/2026

- Người dùng trả lời “đồng ý”: chưa tới ca/chưa quét hiển thị Chưa bắt đầu; đã tới giờ/chưa quét/chưa chốt hiển thị Chưa đến — tạm thời; chốt không có vào thành ABSENT; giữ sửa tay/LEAVE khi tự tính lại; event nhận muộn nhưng xảy ra trong cửa sổ ca được tính lại và giữ finalized; ngoài cửa sổ chỉ ra vào.
- FG-ATT-002 lên phiên bản 1.2, FG-ATT-003 lên phiên bản 1.1, giữ APPROVED theo xác nhận trực tiếp.
- Cần đồng bộ nguồn về biểu diễn dữ liệu và quy tắc tính lại; không tự thêm enum/endpoint, chưa triển khai hoặc nghiệm thu.

## Quyết định Q-010 — 14/11/2026

- Người dùng trả lời “đồng ý”: vượt grace tính phút từ giờ ca, trong grace là 0; công chỉ trong ca và trừ phần giao giờ nghỉ; lấy phần nguyên kết quả phút; 4 trạng thái đủ điều kiện tính 1 ngày, trạng thái khác thống kê riêng; giải trình không cộng ngày lần hai.
- Ví dụ đã được duyệt: ca 08:30, grace 10 phút; vào 08:40 không muộn, vào 08:41 tính 11 phút muộn. Đây là ví dụ yêu cầu, không kết quả đo app.
- FG-ATT-002 lên phiên bản 1.3, FG-ATT-005 lên phiên bản 1.2 theo xác nhận trực tiếp, giữ APPROVED. Chưa đồng bộ nguồn chuẩn/code hoặc nghiệm thu app.

## Quyết định Q-011 — 14/11/2026

- Người dùng trả lời “đồng ý” với thứ tự xét người gửi: OWNER→HR khác; HR không OWNER→OWNER khác; MANAGER chính phòng mình không OWNER/HR→HR; còn lại→MANAGER đúng phòng ban. Luôn không tự duyệt.
- Không có người duyệt hợp lệ thì giữ PENDING, thông báo cần bố trí người duyệt. Thứ tự chỉ dùng cho luồng giải trình.
- FG-REQ-002 và FG-AUTH-002 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ APPROVED; chưa đồng bộ nguồn chuẩn hoặc triển khai/nghiệm thu.

## Quyết định Q-012 — 14/11/2026

- Người dùng trả lời “đồng ý”: Có mặt=đã có giờ vào; Đi muộn=trong Có mặt và vượt start+grace; Chưa đến=đã tới ca/chưa vào; Lượt người lạ=event UNKNOWN không SPOOF. Ba chỉ số nhân viên chỉ ACTIVE có ca, loại lễ/LEAVE/không ca và đếm người duy nhất; số trong ngày tạm thời; lấy 10 event mới nhất bằng page=1/size=10.
- FG-DASH-001 lên phiên bản 1.1 theo xác nhận trực tiếp, giữ APPROVED. Chưa đồng bộ nguồn chuẩn/code hoặc nghiệm thu app.

## Quyết định Q-013 — 14/11/2026

- Người dùng trả lời “đồng ý”: demo một công ty từ seed, timezone cố định Asia/Ho_Chi_Minh, Web/Kiosk hiển thị tên/ngày giờ theo cấu hình đó, không thêm màn/API sửa công ty/timezone.
- FG-SYS-001 lên phiên bản 1.2 theo xác nhận trực tiếp, giữ APPROVED. Chưa sửa seed/cấu hình triển khai/code hoặc nghiệm thu app.
- Kết thúc review: 32 specs APPROVED và 13/13 Q đã có quyết định. Các phần nguồn chuẩn chưa đồng bộ vẫn được ghi rõ; chưa có feature được đánh dấu triển khai xong hoặc archived.

## Đồng bộ nguồn chuẩn — 14/11/2026

Người dùng trực tiếp yêu cầu đồng bộ nguồn chuẩn theo các quyết định trước triển khai. Đã cập nhật đặc tả v1.4.4, DB, OpenAPI v1.1.0/WS, UI/token, skill và plan liên quan; làm mới bảng API trong specs. Các ghi nhận “chưa đồng bộ” ở các mục trước là lịch sử tại thời điểm duyệt. Giữ APPROVED, chưa triển khai app/archived. Báo cáo tại `03-app/ket-qua-kiem-thu/2026-11-14_dong-bo-nguon/bao-cao.md`.

## Chốt khóa lượt thử ghép thiết bị — 15/11/2026

Người dùng chọn trực tiếp trong chat: “Khóa IP nhập sai trong 10 phút; giữ cách nhập mã hiện tại, đổi thông báo thành khóa lượt thử từ máy này.” FG-DEV-001 cập nhật v1.1 và giữ APPROVED theo xác nhận này. Đồng bộ đúng mô tả PairRequest/OpenAPI, K-01, thiết kế DB và T05; không thêm pairing_id hoặc thay cấu trúc schema DB. Bộ đếm device.pairing_attempts không dùng để gán lỗi cho mã đích không biết. Nghiệm thu backend T05 ghi riêng tại ket-qua-kiem-thu/2026-11-15_T05; chưa đánh dấu hoàn tất SecureStore/UI.


## Hoàn thành FG-AI-003 — 15/11/2026

Chuyển archived sau T04 c110df6/T05 ed90ab6: 1.464.840 chuỗi và cooldown thật 1 OK + 2 ALREADY chỉ 1 MATCH. Metadata/AC/báo cáo và các liên kết đã cập nhật. Các spec khác giữ approved khi chưa đủ AC.
