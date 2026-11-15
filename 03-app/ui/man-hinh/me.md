# LAYOUT MÀN HÌNH — TRANG NHÂN VIÊN `/me` (web responsive, điện thoại dọc)
> Theo `ui/design-system.md` (theme `web-antd-theme.json`, Canopy) và `dac-ta-app.md` §9.2. Thiết kế cho chiều rộng 360–430 px, vẫn dùng được trên máy tính (giới hạn rộng 480, căn giữa).
> Màn: E-01, E-02, E-03, E-04, E-05, E-06, E-08, E-10 (E-07 thông báo, E-09: **đã bỏ**).

## Khung chung
- **Thanh trên** 56 px: tiêu đề màn (Be Vietnam Pro 18) + avatar chữ cái (bo 10) mở menu tài khoản (Đổi mật khẩu, Đăng xuất).
- **Thanh dưới** 64 px (cố định): 4 mục icon + nhãn 11 — Hôm nay (E-02) · Bảng công (E-03) · Giải trình (E-06) · Khuôn mặt (E-08); người có vai trò MANAGER có thêm mục thứ 5 "Duyệt" (E-10, có số chờ).
- Nền `bg`, thẻ trắng bo 16, lề 16.
- Nếu người dùng chỉ có vai trò quản trị mà không gắn nhân viên → chuyển sang `/admin`.

## E-01 · Đăng nhập (dùng chung cho `/me` và `/admin`)
- **Bố cục:** nền `hero-mist`; thẻ giữa rộng tối đa 400, bo 20: tiêu đề "Đăng nhập" (h2) → ô Email (nhãn trong, cao 56) → ô Mật khẩu (nút hiện/ẩn) → nút chính toàn rộng "Đăng nhập" → dòng nhỏ "Bản trình diễn nghiên cứu".
- **Dữ liệu:** `POST /api/v1/auth/login` → nếu `must_change_password` → thẻ "Đổi mật khẩu lần đầu" (`POST /auth/change-password`). Sau đăng nhập: có vai trò OWNER/HR/SECURITY/MANAGER → hỏi "Vào trang quản trị hay trang cá nhân?" (2 nút); chỉ EMPLOYEE → `/me`.
- **Trạng thái:** sai thông tin "Email hoặc mật khẩu không đúng" · bị khoá `429` "Thử lại sau ít phút".

## E-02 · Hôm nay

- **Q-008/Q-009:** Ngày có ca chưa tới giờ/chưa quét: NOT_STARTED “Chưa bắt đầu”; từ start chưa quét trước chốt: WAITING_IN “Chưa đến — tạm thời”; đã vào/chưa chốt: IN_PROGRESS “Đang làm việc — tạm thời”. Chỉ chốt mới ABSENT/nhóm đủ giờ; HOLIDAY/LEAVE/OFF ưu tiên.
- **Bố cục:** lời chào "Chào {tên}" + ngày (dd/MM/yyyy, thứ) → **thẻ lớn ca hôm nay**: tên ca + giờ ca; hai ô cạnh nhau **Giờ vào** / **Giờ ra** (số 28 Be Vietnam Pro, hoặc "—"); pill trạng thái ngày công (nhãn ở `status.json`; chú thích nhỏ "tạm thời" nếu chưa chốt) → thẻ "Lượt qua cửa hôm nay": danh sách (giờ · tên cửa · nhãn kết quả); cửa `ACCESS_ONLY` có ghi chú "không tính công".
- **Trường hợp:** không có ca → thẻ "Hôm nay bạn không có ca" · ngày lễ → "Hôm nay là ngày lễ: {tên}" · NV `MANUAL` → dòng "Bạn chấm công tại quầy lễ tân".
- **Dữ liệu:** `GET /api/v1/me/today` (làm mới khi trang được mở lại / kéo xuống).
- **Chuyển động (GSAP):** ô giờ vào/ra "lật" khi giá trị đổi so với lần tải trước.

## E-03 · Bảng công tháng

- **Q-010:** Ngày công đếm ngày duy nhất NORMAL/LATE/EARLY/LATE_EARLY sau điều chỉnh, không cộng riêng ngày có giải trình. Phút tính theo đặc tả §5.5, không quy đổi nửa ngày.
- **Bố cục:** bộ chọn tháng (‹ Tháng 11/2026 ›) → `Calendar` dạng lưới tháng gọn: mỗi ô ngày có chấm màu theo nhóm trạng thái → chú giải màu (gập lại được) → 4 `KpiTile` 2×2: Ngày công · Số lần muộn · Tổng phút muộn · Ngày thiếu giờ ra/vắng.
- **Dữ liệu:** `GET /api/v1/me/attendance?month=YYYY-MM`.
- **Hành động:** chạm ngày → E-04.

## E-04 · Chi tiết ngày
- **Bố cục:** tiêu đề ngày → thẻ: ca, giờ vào, giờ ra, phút muộn/về sớm, giờ làm, pill trạng thái, nhãn nguồn (`source`), cảnh báo vàng nếu `suspect_forgot_out` ("Có thể bạn quên quét khi ra về") → danh sách event trong ngày → nút chính "Gửi giải trình" (ẩn nếu đã có giải trình đang chờ cho ngày này; hiện pill trạng thái giải trình thay vào).
- **Dữ liệu:** `GET /api/v1/me/days/{date}`.

## E-05 · Gửi giải trình
- **Bố cục:** form 1 cột: Ngày (điền sẵn) · Loại (`Select`, nhãn ở `status.json`) · Giờ vào đề nghị (hiện khi FORGOT_IN/NOT_RECOGNIZED/BUSINESS_TRIP) · Giờ ra đề nghị (FORGOT_OUT/…) · Lý do (bắt buộc) · nút "Gửi".
- **Dữ liệu:** `POST /api/v1/me/requests`. Lỗi `409 REQUEST_PENDING_EXISTS` → "Ngày này đã có giải trình đang chờ duyệt".

## E-06 · Giải trình của tôi
- **Bố cục:** `Segmented` Chờ duyệt / Đã xử lý → danh sách thẻ: ngày · loại · giờ đề nghị · pill trạng thái · ghi chú người duyệt; thẻ PENDING có nút "Huỷ".
- **Dữ liệu:** `GET /api/v1/me/requests?status=`, `POST /api/v1/me/requests/{id}/cancel`.

## E-08 · Dữ liệu khuôn mặt

- **Q-005/Q-006:** Rút đồng ý xóa ACTIVE/PENDING, mẫu/vector/crop liên kết, NULL consent_at/by, MANUAL; muốn dùng lại phải đồng ý/đăng ký lại. Giữ công/event. Xóa file lỗi báo chưa hoàn tất và cho thử lại, không khôi phục nhận dạng trong lúc chờ.
- **Bố cục:** thẻ trạng thái hồ sơ (pill `face_profile.status`) · "Đã đồng ý lúc {dd/MM/yyyy HH:mm}" hoặc "Chưa đồng ý" · phương thức chấm công (Khuôn mặt / Chấm công hộ) → khối giải thích 3 dòng (dữ liệu lưu gì, ở đâu, khi nào xoá) → nút danger viền "Rút đồng ý và xoá dữ liệu khuôn mặt".
- **Hành động:** bấm → `Modal.confirm` "Sau khi rút, bạn sẽ không chấm công bằng khuôn mặt được nữa và phải chấm công tại quầy lễ tân. Tiếp tục?" → `POST /api/v1/me/face/revoke`.
- **Dữ liệu:** `GET /api/v1/me/face`.
- Không hiển thị ảnh mẫu ở đây.

## E-10 · Duyệt giải trình (MANAGER)

- **Q-011:** Xét vai trò **người gửi** theo nhánh đầu tiên phù hợp: (1) có OWNER, kể cả kiêm HR → HR khác; (2) HR không OWNER → OWNER khác; (3) MANAGER chính phòng mình, không OWNER/HR → HR khác; (4) còn lại → MANAGER đúng phòng ban người gửi, khác người gửi. MANAGER chỉ quản lý phòng khác thuộc nhánh (4). Không có người duyệt hợp lệ thì giữ PENDING, hiện cần bố trí người duyệt. Server luôn chặn tự duyệt; thứ tự chỉ dùng chọn nhóm duyệt, không loại bỏ quyền khác của tài khoản.
- **Bố cục:** danh sách thẻ giải trình chờ của team (tên NV, ngày, loại, giờ đề nghị, lý do, giờ thực tế đã ghi nhận) → mỗi thẻ 2 nút: mềm "Từ chối", chính "Duyệt" → bottom sheet nhập ghi chú (bắt buộc khi từ chối).
- **Dữ liệu:** `GET /api/v1/attendance/requests?status=PENDING&scope=team` (server đã loại giải trình của chính người duyệt), `POST …/{id}/approve|reject`.
- **Trạng thái:** trống "Không có giải trình chờ duyệt".
