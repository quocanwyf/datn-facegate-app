# Báo cáo T10 — Chấm công web quản trị

- Trạng thái: **XONG các tiêu chí T10**. W-11 lịch sử sự kiện là phần T11; trang cá nhân E-10 là T12.
- Commit: `9e28f9f` (web); archive ở commit kế tiếp.

| # | Tiêu chí | Kết quả / bằng chứng |
|---|---|---|
| 1 | W09 chữ tắt, màu token, tải Excel | WAITING_IN=C đúng nền #E3F2FD; lưới có chú giải, tổng ngày duy nhất; download từ Hub thật và mở lại đủ hai sheet — `playwright-fixtures.log`, `playwright-real.log`, `excel-download-check.json` |
| 2 | Không sửa/duyệt bản thân | Playwright kiểm Owner có employee; kể cả fixture can_review=true vẫn ẩn tự duyệt. Hub thật cũng kiểm Owner không sửa bản thân — hai log trên |
| 3 | ASSIGNMENT_OVERLAP tiếng Việt | 409 giữ form, hiện “Đã có phân ca trùng thời gian cho thứ này” — `W06-overlap-fixture.png` |
| 4 | Ảnh 3 màn; typecheck/lint sạch | Ảnh W06/W09/W12 trong `screens`; `typecheck.log`, `lint.log`, `build.log` |

Playwright: **4/4 fixture + 2/2 Hub thật**. Fixture chỉ trong browser, không ghi event/ngày công vào DB. Hub review dùng DB T10 riêng từ seed chính thức, ngày công do backend suy ra; giải trình tạo qua API đúng danh tính. Không có ảnh/event nhận dạng giả.

## Đã triển khai

- W06: thêm/sửa ca bằng TimePicker 24h, kiểm ca không qua ngày/quá 17h; chọn phòng ban/nhân viên, lưới 7 thứ, tạo/xóa phân ca; ngày lễ theo năm và thêm/xóa.
- W09: lọc tháng/phòng ban/tên/mã và employee_id từ chi tiết nhân viên; tải đủ các trang API, khử trùng ngày khi phân trang; cột mã/tên cố định, trạng thái tạm thời, Drawer giờ/phút/nguồn/cờ; sửa có lý do và đánh dấu nghỉ theo quyền; Excel từ API có scope server.
- W12: chờ/đã xử lý, giờ đề nghị/ghi nhận, vai trò duyệt từ can_review server, không tự duyệt, modal ghi chú và bắt buộc lý do từ chối. Nếu thiếu người đúng cấp, giữ pending và hướng dẫn bố trí người duyệt; không tự chuyển nhóm.
- Dùng component/token/font đã có; không sửa nguồn OpenAPI hoặc token UI. Lưu lỗi giữ form, chặn submit lặp, mutation chỉ báo thành công sau API thành công.

## Kiểm tra thực tế

- Hub thật: tạo ca; tạo/xóa phân ca cá nhân; thêm/xóa lễ; W09 tải tháng qua nhiều trang; Excel tải bằng browser; Owner tự bảo vệ; Manager duyệt NV006 trả 200 và tính lại công.
- Đã xem ảnh render W06, W09, W12. Dữ liệu fixture có nhãn riêng trong tên file, ảnh Hub thật có `real`.
- Lượt đầu test bị chờ inline style sau animation và đọc placeholder “Trống” làm tên ca; sửa điều kiện chờ theo trạng thái render và chọn tên ca seed rõ ràng. Không sửa app để làm giả phản hồi test.
- Build thành công; Vite còn cảnh báo kích thước chunk >500 kB, không có lỗi TypeScript hoặc lint.
- Chỉ archive spec đủ phạm vi: ca/phân ca/ngày lễ và Excel. Bảng công còn đường dẫn sự kiện W11; giải trình còn E10 nên giữ những spec đó tới T11/T12.

## Review

Theo `REVIEW-T10.md`. Báo cáo backend và Excel fixture kiểm công thức ở T09. Các phép đo camera/người thật không nằm trong kết quả T10 này.
