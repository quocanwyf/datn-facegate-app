# LAYOUT MÀN HÌNH — WEB ADMIN `/admin` (desktop ≥ 1280 px)
> Theo `ui/design-system.md` (Ant Design 5 + `web-antd-theme.json`, Canopy) và `dac-ta-app.md` §9.3, §6 (quyền).
> Màn: W-01 … W-12, W-14, W-16 (W-13 gộp vào W-05; W-15 So sánh mô hình, W-17 Điều khoản: **đã bỏ**).
> Dưới 1024 px: Sider thành Drawer; bảng cuộn ngang. Không cần tối ưu điện thoại cho `/admin`.

## Khung chung (App shell)
- **Sider** 64 px (thu gọn, icon 24 + tooltip), gradient teal; mục đang chọn = ô trắng bo 12, icon teal. Nhóm mục theo vai trò (ẩn mục không có quyền):
  Tổng quan (W-02) · Giám sát (W-10) · Nhân viên (W-03) · Xác nhận khuôn mặt (W-08, badge số chờ) · Bảng công (W-09) · Giải trình (W-12, badge) · Sự kiện (W-11) · Ca & lịch (W-06) · Phòng ban & tài khoản (W-05) · Cửa & thiết bị (W-07) · Cấu hình nhận dạng (W-14) · Nhật ký (W-16).
- **Header** 64 px trắng: tên công ty · khoảng trống · chấm trạng thái Hub (`GET /health`: xanh/đỏ) · chuông (số cảnh báo chưa xử lý, mở W-10) · avatar + tên + vai trò (menu: Trang cá nhân `/me`, Đổi mật khẩu, Đăng xuất).
- **Nội dung:** nền `bg`, lề 24; mỗi trang mở đầu bằng `PageHero` (breadcrumb + tiêu đề + số đếm xám), sau đó là panel trắng bo 16.
- Dải nhỏ cuối trang: "Bản trình diễn nghiên cứu – không dùng thương mại".
- **Mặc định khi vào `/admin`:** OWNER/HR → W-02; SECURITY → W-10; MANAGER → W-09 (lọc team).
- **Không có quyền** (403) → `Result` 403 "Bạn không có quyền xem trang này".

---
## W-01 · Đăng nhập
Dùng chung E-01 (`ui/man-hinh/me.md`), bản desktop: thẻ đăng nhập rộng 400 đặt giữa nền `hero-mist`.

## W-02 · Tổng quan hôm nay (OWNER, HR)

- **Định nghĩa Q-012:** Ba chỉ số nhân viên chỉ tính ACTIVE có ca hôm nay, loại HOLIDAY/LEAVE/OFF; dùng giờ công hiệu lực, đếm mỗi người một lần. Có mặt = đã có check_in; Đi muộn là tập con Có mặt có check_in > start+grace_in; Chưa đến = đã tới start mà chưa check_in. Trong ngày là số tạm thời, không đổi IN_PROGRESS thành LATE để tính KPI. Lượt người lạ = số event UNKNOWN xảy ra trong ngày theo timezone công ty, không gồm SPOOF và không phải số danh tính riêng biệt. 10 event mới nhất dùng page=1&size=10, mới nhất trước, không query limit.
- **Bố cục:** `PageHero` "Tổng quan · {ngày}" → hàng 4 `KpiTile`: Có mặt · Đi muộn · Chưa đến · Lượt người lạ hôm nay → 2 cột 8/4: trái = bảng "10 sự kiện mới nhất" (giờ, cửa, người/“Người lạ”, pill kết quả) với link "Xem tất cả" → W-11; phải = thẻ "Cần xử lý": số khuôn mặt chờ xác nhận (→ W-08), số giải trình chờ (→ W-12), số cảnh báo chưa xử lý (→ W-10), thiết bị mất kết nối.
- **Dữ liệu:** `GET /api/v1/dashboard/today`, `GET /api/v1/events?page=1&size=10`; cập nhật trực tiếp qua WS `/ws/monitor` (sự kiện mới chèn đầu bảng).
- **Chuyển động:** KPI đếm từ 0 (600 ms); hàng mới trượt vào.

## W-03 · Nhân viên (OWNER, HR; MANAGER chỉ đọc team)
- **Bố cục:** `PageHero` "Nhân viên {tổng}" → thanh công cụ: tìm (tên/mã) · lọc phòng ban · lọc trạng thái · lọc phương thức (Khuôn mặt/Chấm hộ) · lọc hồ sơ khuôn mặt | nút chính "Thêm nhân viên" → `Table`: Mã · Họ tên · Phòng ban · Trạng thái (pill) · Phương thức (pill) · Hồ sơ khuôn mặt (pill) · Ngày vào làm · menu ⋯ (Sửa, Tạm khoá/Mở khoá, Nghỉ việc).
- **Thêm/Sửa:** `Drawer` 480: mã, họ tên, email, SĐT, phòng ban, ngày vào làm, tuỳ chọn "Tạo tài khoản đăng nhập" (email = email NV, mật khẩu tạm hiện một lần).
- **Nghỉ việc:** `Modal.confirm` nguy hiểm: "Chuyển {tên} sang Đã nghỉ việc? Toàn bộ ảnh mẫu và đặc trưng khuôn mặt sẽ bị xoá ngay. Dữ liệu chấm công được giữ lại." → `POST /api/v1/employees/{id}/terminate`.
- **Dữ liệu:** `GET /api/v1/employees?...` (phân trang 20), `POST`, `PATCH /employees/{id}`, `POST /employees/{id}/suspend|reactivate|terminate`.
- **Bấm dòng** → W-04.

## W-04 · Chi tiết nhân viên (OWNER, HR)

- **Q-005/Q-006:** Xóa dữ liệu khuôn mặt xóa cả ACTIVE/PENDING và crop liên kết, NULL consent_at/by, MANUAL; giữ lịch sử công/event. Xóa file lỗi báo chưa hoàn tất/cho thử lại, không cho nhận dạng trở lại; không báo thành công khi gallery chưa cập nhật.
- **Bố cục:** `PageHero` (breadcrumb "Nhân viên / {tên}") + thẻ thông tin chồng lên banner: tên (h3), mã, phòng ban, pill trạng thái, 3 ô: phương thức · hồ sơ khuôn mặt · ca hiện tại → `Tabs`:
  - **Thông tin:** form chỉ đọc + nút Sửa.
  - **Khuôn mặt:** trạng thái hồ sơ, thời điểm đồng ý + người thực hiện, lưới 5 ảnh mẫu 112×112 (phóng 2×, bo 12) kèm điểm phát hiện; nút danger "Xoá dữ liệu khuôn mặt" (`DELETE /api/v1/employees/{id}/face`, xác nhận) ; nếu chưa có: hướng dẫn "Đăng ký tại Kiosk bằng PIN HR".
  - **Ca:** phân ca hiệu lực (cá nhân / theo phòng ban), nút "Gán ca riêng" → W-06.
  - **Chấm công:** bảng tháng hiện tại (ngày, vào, ra, pill, nguồn) + chọn tháng.
  - **Sự kiện:** bảng event của NV (lọc thời gian).
- **Dữ liệu:** `GET /api/v1/employees/{id}`, `GET /api/v1/face-profiles?employee_id=`, `GET /api/v1/face-samples/{id}/image`, `GET /api/v1/attendance/days?employee_id=`, `GET /api/v1/events?employee_id=`.

## W-05 · Phòng ban & tài khoản (OWNER, HR)
- **Bố cục:** `Tabs` 2 tab:
  - **Phòng ban:** bảng (tên, số NV, quản lý = các user có vai trò MANAGER phạm vi phòng này) + thêm/sửa tên.
  - **Tài khoản:** bảng (email, NV liên kết, vai trò dạng pill neutral, trạng thái, lần đăng nhập cuối) ; `Drawer` sửa: trạng thái, vai trò (checkbox OWNER/HR/SECURITY/EMPLOYEE; MANAGER kèm chọn phòng ban, có thể nhiều dòng), **PIN Kiosk** (đặt/đổi 4 số, chỉ cho OWNER/HR), nút "Đặt lại mật khẩu".
- **Ràng buộc hiển thị:** HR không sửa được tài khoản OWNER (ẩn nút).
- **Dữ liệu:** `GET/POST/PATCH /api/v1/departments`, `GET/POST/PATCH /api/v1/users`, `PUT /users/{id}/roles`, `PUT /users/{id}/kiosk-pin`, `POST /users/{id}/reset-password`.

## W-06 · Ca, phân ca, ngày lễ (OWNER, HR)
- **Bố cục:** `Tabs`:
  - **Ca:** bảng ca (tên, giờ, nghỉ trưa, cho phép muộn/sớm) + `Drawer` thêm/sửa (`TimePicker` 24 giờ; kiểm "giờ kết thúc > giờ bắt đầu, tối đa 17 giờ").
  - **Phân ca:** chọn đối tượng (Phòng ban / Nhân viên) → lưới 7 cột Thứ 2…CN, mỗi ô là ca đang áp dụng (chip) + hiệu lực từ–đến; thêm/xoá phân ca. Lỗi `409 ASSIGNMENT_OVERLAP` → "Đã có phân ca trùng thời gian cho thứ này".
  - **Ngày lễ:** danh sách theo năm + thêm (ngày, tên) / xoá.
- **Dữ liệu:** `/api/v1/shifts`, `/api/v1/shift-assignments`, `/api/v1/holidays`.

## W-07 · Cửa & thiết bị (OWNER; HR chỉ sửa chính sách)

- **Q-001:** HR chỉ được sửa default_policy và allowed departments; khóa các trường name/mode/ngưỡng/is_active và toàn bộ tạo cửa/thiết bị/thu hồi. PATCH HR chỉ gửi default_policy, không gửi nguyên form có trường OWNER; server chặn trường ngoài quyền bằng 403. OWNER giữ quyền đầy đủ.
- **Bố cục:** 2 cột 5/7: trái = danh sách thẻ cửa (tên, pill chế độ, pill mức ngưỡng, số thiết bị online/tổng) + nút "Thêm cửa"; phải = chi tiết cửa chọn:
  - Form: tên · chế độ (Chấm công + ra vào / Chỉ ra vào) · chính sách (Mọi nhân viên / Chỉ phòng ban được phép + chọn phòng ban) · mức ngưỡng (`Segmented`: Mặc định / Nghiêm ngặt / Tuỳ chỉnh + ô số khi Tuỳ chỉnh), hiện **số cos** của mức đang chọn kèm nhãn nguồn (từ `GET /api/v1/models/active`).
  - Bảng thiết bị: tên, pill trạng thái, lần thấy cuối, phiên bản app, nút "Thu hồi".
  - Nút chính "Thêm thiết bị" → `Modal` hiện **mã QR + mã 6 số + địa chỉ Hub + đồng hồ đếm ngược 10 phút**.
- **Dữ liệu:** `/api/v1/gates`, `PUT /gates/{id}/allowed-departments`, `GET/POST /api/v1/devices`, `POST /devices/{id}/revoke`; trạng thái online qua WS `device_status`.

## W-08 · Hàng chờ xác nhận khuôn mặt (OWNER, HR)

- **Q-004/Q-006:** PENDING cũ chỉ thay sau 5 mẫu mới lưu thành công; ACTIVE cũ giữ tới duyệt mới. Hai người duyệt cùng hồ sơ chỉ một người thành công; người còn lại thấy “Hồ sơ đã được xử lý” (409 PROFILE_ALREADY_REVIEWED). Lỗi reload gallery báo tạm ngưng nhận dạng, không báo duyệt xong sớm.
- **Bố cục:** 2 cột 4/8: trái = danh sách hồ sơ `PENDING_REVIEW` (tên NV, phòng ban, thời gian, người đăng ký, cờ ⚠ nếu nghi trùng); phải = chi tiết: lưới 5 ảnh mẫu lớn (2× = 224 px) kèm điểm phát hiện/độ nghiêng; nếu `duplicate_of_employee_id`: khung cảnh báo vàng "Giống {tên NV khác} (cos {điểm})" ; ô ghi chú ; 2 nút: mềm "Từ chối", chính "Xác nhận" (nếu có cảnh báo trùng: phải nhập ghi chú mới bấm được Xác nhận).
- **Dữ liệu:** `GET /api/v1/face-profiles?status=PENDING_REVIEW`, `GET /face-samples/{id}/image`, `POST /face-profiles/{id}/approve|reject`.
- **Trống:** "Không có hồ sơ chờ xác nhận".

## W-09 · Bảng công (OWNER, HR; MANAGER chỉ đọc team)

- **Q-001/Q-008–Q-010:** MANAGER được xuất Excel team, server giới hạn scope ngay cả bỏ/sửa bộ lọc. WAITING_IN hiển thị Chưa đến — tạm thời, ký hiệu C; IN_PROGRESS Đang làm việc — tạm thời. Chưa chốt không hiện vắng sớm. Tự recompute giữ sửa tay/LEAVE; event nhận muộn trong cửa sổ tính lại và giữ finalized. Tổng công đếm ngày hiệu lực duy nhất, không cộng thêm ngày giải trình. Công thức phút/định dạng Excel theo đặc tả §5.5–5.8.
- **Bố cục:** `PageHero` "Bảng công tháng {MM/yyyy}" → thanh công cụ: chọn tháng · lọc phòng ban · tìm NV | mềm "Đánh dấu nghỉ" · chính "Xuất Excel" → **lưới NV × ngày** (cột cố định Mã, Tên; mỗi ô ngày 36×36 tô màu nền theo nhóm trạng thái + chữ tắt: ✓ Đ, M (muộn), S (sớm), V (vắng), T (thiếu giờ ra), P (phép), L (lễ), – (không ca)) → cột tổng cuối: ngày công, lần muộn, phút muộn.
- **Bấm ô** → `Drawer` chi tiết ngày: giờ vào/ra, event, nguồn; HR/OWNER có nút "Sửa" (form giờ vào/ra + lý do bắt buộc) — **ẩn khi ô là của chính người đang đăng nhập**.
- **Dữ liệu:** `GET /api/v1/attendance/days?from=&to=&department_id=`, `PATCH /attendance/days/{id}`, `POST /attendance/leave`, `GET /attendance/export?month=` (tải .xlsx).
- Chú giải màu cố định ở cuối lưới.

## W-10 · Giám sát (SECURITY, OWNER; HR chỉ xem)
- **Bố cục:** 3 vùng: trái 7/12 = **luồng sự kiện realtime** (thẻ dọc: giờ, cửa, tên/“Người lạ”, pill kết quả, điểm cos & ngưỡng nhỏ màu xám) ; phải 5/12 = **Cảnh báo chưa xử lý** (thẻ UNKNOWN/SPOOF có crop 96×96, giờ, cửa; nút "Xử lý") ở trên + **Thao tác nhanh** ở dưới: "Mở cửa thủ công" (chọn cửa + lý do) và "Chấm công hộ" (tìm NV có phương thức Chấm hộ + cửa chấm công + lý do).
- **Xử lý cảnh báo:** `Modal`: crop lớn, thông tin; chọn Đã xử lý / Báo động giả / Là nhân viên (chọn NV) + ghi chú. Ghi rõ dưới nút: "Không thêm ảnh này vào hồ sơ khuôn mặt".
- **Dữ liệu:** WS `/ws/monitor` (`event`, `alert`, `device_status`); `GET /api/v1/events?result=UNKNOWN,SPOOF&handled=false`; `GET /events/{id}/snapshot`; `POST /events/{id}/handle`; `POST /gates/{id}/manual-open`; `POST /attendance/manual`.
- **Chuyển động (GSAP):** event mới trượt vào đầu + nháy nền một lần theo nhóm màu; SPOOF rung nhẹ 2 lần; âm báo nhẹ cho cảnh báo (tắt được).
- **Mất WS:** dải đỏ trên cùng "Mất kết nối thời gian thực — đang nối lại".

## W-11 · Tra cứu sự kiện (OWNER, HR, SECURITY; MANAGER team)
- **Bố cục:** thanh lọc: khoảng thời gian · cửa · kết quả (nhiều lựa chọn) · NV · người thực hiện (cho MANUAL_*) | mềm "Xuất CSV" → `Table`: thời gian, cửa, thiết bị, kết quả (pill), NV, điểm, ngưỡng (mức), số khung, người thực hiện, lý do → **tab thứ hai "Báo cáo chấm công hộ"**: bảng theo người chấm (tên, số lượt trong khoảng thời gian, số NV khác nhau) để phát hiện lạm dụng.
- **Dữ liệu:** `GET /api/v1/events?...`, `GET /events/export?format=csv&...`, `GET /api/v1/events/manual-report?from=&to=`.

## W-12 · Giải trình (OWNER, HR, MANAGER)

- **Q-011:** Xét vai trò **người gửi** theo nhánh đầu tiên phù hợp: (1) có OWNER, kể cả kiêm HR → HR khác; (2) HR không OWNER → OWNER khác; (3) MANAGER chính phòng mình, không OWNER/HR → HR khác; (4) còn lại → MANAGER đúng phòng ban người gửi, khác người gửi. MANAGER chỉ quản lý phòng khác thuộc nhánh (4). Không có người duyệt hợp lệ thì giữ PENDING, hiện cần bố trí người duyệt. Server luôn chặn tự duyệt; thứ tự chỉ dùng chọn nhóm duyệt, không loại bỏ quyền khác của tài khoản.
- **Bố cục:** `Segmented` Chờ duyệt / Đã xử lý → `Table`: NV, phòng ban, ngày, loại, giờ đề nghị, giờ đã ghi nhận, lý do, gửi lúc, (đã xử lý: người duyệt, kết quả, ghi chú) → hàng chờ có nút Duyệt / Từ chối (modal ghi chú; bắt buộc khi từ chối). Giải trình của chính người đang đăng nhập **không hiện nút duyệt** (server cũng chặn).
- **Dữ liệu:** `GET /api/v1/attendance/requests?status=&scope=`, `POST …/{id}/approve|reject`.

## W-14 · Cấu hình nhận dạng (OWNER sửa; HR chỉ xem)

- **Q-001/Q-007/Q-008:** HR xem toàn bộ nhưng không có quyền Lưu/PUT. OWNER bật liveness chỉ sau T13/chốt L trong [0,1]; W nguyên dương, các ngưỡng đếm nguyên 1..W. Lỗi giữ cấu hình cũ, không áp một phần. Health model_verified=false hoặc gallery lỗi báo chưa sẵn sàng/tạm ngưng; không coi HTTP 200 của health là nhận dạng ready.
- **Bố cục:** các thẻ xếp dọc:
  1. **Mô hình đang chạy** (chỉ đọc): tên, epoch, SHA-256 (rút gọn, bấm để sao chép), phiên bản runtime, trạng thái cổng kiểm tra lúc khởi động (từ `/health`).
  2. **Ngưỡng nhận dạng**: bảng 3 dòng (Mặc định 0,4233 · Nghiêm ngặt 0,4657 · b̃/s 0,3736 "chỉ tham khảo") với **nhãn nguồn bắt buộc** và **bảng đánh đổi** (FPIR / FNIR trên BLUFR, đặc tả §4.4) + ghi chú "Số đo trên BLUFR (gallery 1000 người), chưa đo tại văn phòng". Mức theo từng cửa chỉnh ở W-07.
  3. **Bộ quyết định**: các tham số §4.5 (`InputNumber` kèm đơn vị: khung, giây) — W, ngưỡng MATCH/UNKNOWN/SPOOF, thời gian mất mặt, cooldown, khung/giây tối đa.
  4. **Chống giả mạo**: `Switch` bật/tắt + ngưỡng L (khoá nhập khi chưa hiệu chỉnh, hiện "Chưa hiệu chỉnh — bật sau T13").
  5. Nút chính "Lưu cấu hình" (xác nhận) → audit.
- **Dữ liệu:** `GET /api/v1/models/active`, `GET/PUT /api/v1/settings/recognition`, `GET /health`.

## W-16 · Nhật ký thao tác (OWNER)
- **Bố cục:** lọc thời gian · người thực hiện · hành động → `Table`: thời gian, người/thiết bị, hành động (nhãn tiếng Việt), đối tượng, chi tiết (mở rộng dòng hiện `detail` dạng key–value).
- **Dữ liệu:** `GET /api/v1/audit-logs?...`.
