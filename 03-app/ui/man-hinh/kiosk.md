# LAYOUT MÀN HÌNH — KIOSK APP (React Native, tablet/máy ảo Android, xoay ngang)
> Theo `ui/design-system.md` (theme `kiosk-theme.json`, Fresh Bloom) và `dac-ta-app.md` §9.1. Màn chuẩn 1280×800 dp; máy ảo dùng cấu hình tablet ngang tương đương.
> Giao thức: `openapi/ws-protocol.md` (WS `/ws/kiosk`). REST: `openapi/openapi.yaml`.
> Danh sách màn: K-01, K-02, K-04, K-05, K-06, K-07, K-08, K-09, K-11 (K-03 thử thách, K-10 cài đặt, K-12 so sánh: **đã bỏ**).

## Sơ đồ điều hướng
```
K-01 ─(ghép xong)→ K-02 ⇄ K-04 (tự quay lại sau 3 s)
K-02 ─(chạm giữ góc phải trên 3 s)→ K-05 → K-06 → K-07 ─(Đồng ý)→ K-08 → K-09 → K-02
                                                    └(Không đồng ý)→ thông báo → K-02
mọi màn ─(mất WS > 3 s)→ K-11 ─(nối lại)→ màn trước đó (đăng ký đang dở thì huỷ, về K-02)
```

---
## K-01 · Ghép thiết bị
- **Mục đích:** gắn tablet với một cửa, lấy device token. **Vai trò:** người cài đặt (Chủ DN đứng cạnh).
- **Bố cục:** nền `bg`; thẻ trắng giữa màn rộng 560, bo 32: tiêu đề "Ghép thiết bị" (32) → mô tả 1 dòng → vùng camera nhỏ 320×240 quét QR → đường phân cách "hoặc nhập tay" → ô "Địa chỉ Hub" (vd. `http://192.168.1.10:8000`) → 6 ô mã → nút inverse "Ghép thiết bị".
- **Thành phần:** `PillButton`, ô nhập bo 16, camera (react-native-vision-camera, chế độ đọc mã QR).
- **Dữ liệu:** QR chứa `{"hub":"http://…","code":"123456"}` → `POST /api/v1/kiosk/pair`. Lưu `device_token`, `hub_url`, `gate` vào SecureStore.
- **Trạng thái:** đang gửi (nút khoá + spinner) · lỗi theo `error.code`: `PAIRING_EXPIRED` "Mã đã hết hạn, vui lòng tạo mã mới trên trang quản trị" · `PAIRING_INVALID` "Mã không đúng" · `PAIRING_LOCKED` "Nhập sai quá 5 lần, mã đã bị khoá" · lỗi mạng "Không kết nối được Hub. Kiểm tra địa chỉ và Wi-Fi".
- **Chuyển động:** thẻ fade-in 200 ms; lỗi rung nhẹ ô mã.
- **Ghi chú máy ảo:** địa chỉ Hub trên cùng máy là `http://10.0.2.2:8000`.

## K-02 · Chờ quét (màn chính)
- **Mục đích:** quét mặt liên tục, hiển thị gợi ý. **Vai trò:** mọi người qua cửa.
- **Bố cục:** camera trước **toàn màn hình** (lật gương) → lớp phủ: `ScanFrame` oval giữa (rộng 42% chiều ngang) → `HintBar` dưới khung → góc trái trên `ClockBadge` (giờ 40 + tên cửa 18 + chấm kết nối) → góc phải trên vùng chạm giữ 3 s (vô hình, 96×96) mở K-05 → dải `ResearchBanner` góc dưới phải.
- **Dữ liệu:** WS `/ws/kiosk`, gửi `frame` mode `recognize` theo kiểu **dừng-và-chờ** (≤ 4 khung/s, cạnh dài 640, JPEG 80); nhận `state` (cập nhật `HintBar` + màu khung + `bbox` để vẽ khung chữ nhật mảnh quanh mặt nếu có) và `result` (→ K-04). Nhận `config` lúc kết nối (tên cửa, chế độ).
- **Gợi ý theo `state`:** lấy nguyên chữ ở `ui/tokens/status.json` → `kiosk_state_hint_vi`.
- **Trạng thái:** camera chưa cấp quyền → thẻ "Cần quyền camera" + nút mở cài đặt · WS đang nối → chấm kết nối vàng.
- **Chuyển động:** khung trắng→lime khi `TRACKING`/`CHECKING` (200 ms); vệt quét chạy dọc 1,6 s khi `CHECKING`.

## K-04 · Kết quả
- **Mục đích:** báo kết quả rõ từ 1–2 m trong 3 s. **Không hiển thị ảnh khuôn mặt.**
- **Bố cục:** `ResultPanel` phủ toàn màn, căn giữa: icon 96 → dòng chính 56 → dòng phụ 28 → (OK cửa chấm công) chip trạng thái ngày công → thanh đếm ngược mảnh 3 s ở đáy.
| `result` / `reason` | Nhóm màu | Icon (Phosphor Fill) | Dòng chính | Dòng phụ |
|---|---|---|---|---|
| OK, `attendance.kind=IN` | success | CheckCircle | **{Tên}** · {mã NV} | "Vào {HH:mm} · {nhãn trạng thái}" |
| OK, `kind=OUT` | success | CheckCircle | **{Tên}** | "Ra {HH:mm}" |
| OK, cửa ACCESS_ONLY (`kind=NONE`) | success | DoorOpen | **{Tên}** | "Mời vào" |
| ALREADY | progress | ClockCounterClockwise | **{Tên}** | "Đã ghi nhận lúc {HH:mm}" |
| DENY, `reason=UNKNOWN` | error | XCircle | "Không nhận diện được" | "Vui lòng liên hệ lễ tân" |
| DENY, `reason=RULE` | error | Prohibit | **{Tên}** | "Bạn không được phép vào khu vực này" |
| DENY, `reason=INACTIVE` | error | Prohibit | **{Tên}** | "Tài khoản đang tạm khoá" |
| DENY, `reason=SPOOF` | danger-strong | ShieldWarning | "Không thể xác thực" | "Vui lòng nhìn trực tiếp vào camera" |
- **Âm thanh:** OK / ALREADY / DENY theo design-system §8.
- **Chuyển động:** OK phóng 0,9→1 + vẽ dấu ✓; DENY/SPOOF rung ±12 px ×3; hết 3 s mờ dần về K-02.

## K-05 · Đăng nhập HR (PIN)
- **Mục đích:** mở chế độ đăng ký khuôn mặt. **Vai trò:** HR / Chủ DN (người có PIN).
- **Bố cục:** nửa trái: tiêu đề "Chế độ đăng ký" + mô tả + chọn tài khoản HR (danh sách 1 cột tên người có PIN, tối đa 4) ; nửa phải: 4 chấm PIN + `PinPad` 3×4 (phím Xoá, phím Huỷ).
- **Dữ liệu:** `GET /api/v1/kiosk/enrollers` (danh sách người có PIN của công ty — chỉ tên + id) → `POST /api/v1/kiosk/enroll/sessions` `{user_id, pin}` → `enroll_session_id` (hết hạn 5 phút).
- **Trạng thái:** sai PIN "PIN không đúng (còn {n} lần)" · khoá "Tạm khoá 15 phút do nhập sai nhiều lần" · không thao tác 30 s → tự về K-02.
- **Chuyển động:** chấm PIN bung khi nhập; sai → rung hàng chấm.

## K-06 · Chọn nhân viên
- **Bố cục:** thanh trên: nút "← Thoát" + tiêu đề "Chọn nhân viên" + đồng hồ phiên còn lại ; `SearchPill` rộng ; danh sách `ListRow` (tên 18/600, mã NV + phòng ban 15, chip trạng thái hồ sơ khuôn mặt theo `face_profile.status`).
- **Dữ liệu:** `GET /api/v1/kiosk/enroll/sessions/{id}/employees?q=` (chỉ NV `ACTIVE`).
- **Hành động:** chọn NV có hồ sơ `PENDING_REVIEW` → hỏi "Đã có bản chờ xác nhận. Đăng ký lại sẽ thay bản này?" ; NV `MANUAL` → vẫn cho chọn (họ có thể đổi ý đồng ý).
- **Trạng thái:** trống "Không tìm thấy nhân viên".

## K-07 · Điều khoản
- **Bố cục:** thẻ trắng giữa, rộng 720: tiêu đề "Đồng ý sử dụng khuôn mặt" → đoạn điều khoản ngắn cố định (≤ 6 dòng: mục đích chấm công & ra vào; lưu ảnh mẫu đã căn chỉnh và đặc trưng trên máy chủ nội bộ; xoá khi nghỉ việc hoặc rút đồng ý; có thể chấm công hộ nếu không đồng ý) → tên NV đã chọn → 2 nút: secondary "Không đồng ý", inverse "Đồng ý".
- **Dữ liệu:** `POST /api/v1/kiosk/enroll/sessions/{id}/consent` `{employee_id, agree}`. `agree=false` → Hub đặt `attendance_method=MANUAL` → thông báo "Đã ghi nhận. Bạn sẽ chấm công tại quầy lễ tân." 4 s → K-02.

## K-08 · Chụp đăng ký
- **Bố cục:** như K-02 (camera toàn màn + `ScanFrame`) + phía trên: `ProgressDots` 5 chấm + chữ "Mẫu {i}/5" ; dưới khung: gợi ý tư thế (thẳng → hơi trái → hơi phải → hơi ngẩng → hơi cúi) ; nút "Huỷ" góc trái.
- **Dữ liệu:** WS frame mode `enroll` kèm `enroll_session_id`, `employee_id`; nhận `enroll_progress {accepted,total,reason?}` → `enroll_done {profile_status:"PENDING_REVIEW", duplicate_warning?}`.
- **Lý do loại mẫu (hiển thị):** theo `reason` trong ws-protocol (vd. "Có nhiều khuôn mặt trong khung", "Khuôn mặt quá nhỏ", "Nghiêng quá nhiều").
- **Chuyển động:** chấm tiến độ bung + nháy khung lime khi nhận mẫu.

## K-09 · Đã gửi
- **Bố cục:** `ResultPanel` nhóm progress: icon HourglassMedium → "Đã gửi đăng ký" → "Chờ quản trị xác nhận trước khi dùng để chấm công" ; nếu có `duplicate_warning`: dòng thứ ba "Lưu ý: khuôn mặt giống một nhân viên khác — quản trị sẽ kiểm tra". Tự về K-02 sau 5 s.

## K-11 · Mất kết nối
- **Bố cục:** nền `bg`, icon WifiSlash 96, "Không kết nối được máy chủ", "Vui lòng báo lễ tân. Đang thử kết nối lại…" + bộ đếm lần thử.
- **Hành vi:** thử nối lại lùi dần 1 → 2 → 4 → 8 s (tối đa 15 s); token bị từ chối (`DEVICE_REVOKED`) → xoá token, về K-01.
