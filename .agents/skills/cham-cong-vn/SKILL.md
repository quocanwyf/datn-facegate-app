---
name: cham-cong-vn
description: Quy tắc nghiệp vụ chấm công, giải trình, chấm công hộ và xuất bảng công tháng (đặc tả §5.5–5.8) — dùng khi viết recompute_day, finalize_day, API/màn bảng công, giải trình, chấm hộ, xuất Excel. Không dùng cho phần nhận dạng.
---

# cham-cong-vn

## Ca và phân ca
- Ca không qua nửa đêm, dài ≤ 17 h; phân ca theo **thứ** (ISO 1 = Thứ Hai), cá nhân ưu tiên hơn phòng ban; DB chặn chồng lấn (409 `ASSIGNMENT_OVERLAP`).
- Ngày lễ toàn công ty (`holiday`) → trạng thái `HOLIDAY` (vẫn ghi giờ nếu có quét).

## Gán event vào ngày công
- Chỉ event `MATCH` được phép tại cửa `ATTENDANCE_ACCESS` và `MANUAL_ATTENDANCE`. Cửa `ACCESS_ONLY` **không tính công**.
- Cửa sổ của **ca**: `[start − attendance_window_before_h, end + attendance_window_after_h]` (mặc định 3 h / 4 h), theo múi giờ công ty — không theo ngày lịch.
- `check_in` = event sớm nhất; `check_out` = event muộn nhất có thời điểm ≥ `check_in + min_checkout_after_checkin_min` (30 phút).

## Trạng thái (xét theo thứ tự)
`HOLIDAY` → `LEAVE` → `OFF` (không ca) → `NOT_STARTED` (chưa tới giờ vào, chưa quét) → `WAITING_IN` (từ start, chưa vào/chưa chốt) → `IN_PROGRESS` (chưa tới thời điểm chốt `end + 4h`, đã vào) → `ABSENT` (đã chốt, không vào) → `MISSING_OUT` (đã chốt, có vào, không ra **hoặc** ra trước `end − forgot_out_before_end_h` → bật `suspect_forgot_out`) → `NORMAL` / `LATE` / `EARLY` / `LATE_EARLY` với `late = check_in > start + grace_in`, `early = end − 2h ≤ check_out < end − grace_out`.
- Trong grace: phút muộn/sớm bằng 0. Nếu `check_in > start + grace_in`: `late_min=floor((check_in-start)/60 giây)`; với trường hợp được phân loại về sớm: `early_min=floor((end-check_out)/60 giây)`. Vượt grace tính từ giờ ca, không chỉ phần vượt grace. Giữ luật MISSING_OUT, không biến thiếu giờ ra thành EARLY.
- So sánh bằng timestamp đầy đủ; lấy phần nguyên kết quả phút sau phép tính. Ví dụ thiết kế: start 08:30, grace 10 phút; vào 08:40 → 0 phút muộn; 08:41 → 11 phút muộn.
- Với cặp giờ hợp lệ, `a=max(check_in,start)`, `b=min(check_out,end)`; `gross=max(0,b-a)`, `rest` là phần giao của `[a,b]` với khoảng nghỉ trong ca (0 nếu không có). `worked_min=floor(max(0,gross-rest)/60 giây)`. Không cộng ngoài ca hoặc trừ phần nghỉ không giao thời gian làm. Ví dụ ca 08:30–17:30 nghỉ 12:00–13:00, vào 08:00 ra 18:00 chỉ tính 480 phút.
- Tổng ngày công đếm cặp `(employee_id,work_date)` duy nhất có trạng thái hiệu lực NORMAL/LATE/EARLY/LATE_EARLY, mỗi ngày 1; trạng thái khác thống kê riêng, không quy đổi nửa ngày. Giải trình APPROVED cập nhật cùng ngày rồi tính theo trạng thái, không cộng thêm ngày theo số request/event.

## Hàm
- `recompute_day(employee_id, work_date)` **idempotent**: tính lại toàn bộ từ event + giải trình APPROVED + holiday/leave. Gọi khi có event mới, khi duyệt giải trình, khi sửa tay, khi chốt.
- `finalize_day` chạy lúc `end + 4h` (Scheduler) → `finalized = true`. Không gửi kết luận "thiếu chấm công" trước thời điểm chốt.

## Giải trình
- Loại: FORGOT_IN (cần giờ vào) · FORGOT_OUT (cần giờ ra) · NOT_RECOGNIZED · BUSINESS_TRIP · OTHER; mỗi NV mỗi ngày tối đa 1 giải trình `PENDING` (409 `REQUEST_PENDING_EXISTS`).
- Người duyệt: MANAGER của phòng ban người gửi; **người duyệt ≠ người gửi** (403 `SELF_REVIEW_FORBIDDEN`): xét thứ tự người gửi theo quy tắc Q-011 dưới đây.
- Duyệt → `recompute_day` dùng giờ đề nghị, `source = ADJUSTED`, giữ event gốc.

## Sửa tay, nghỉ phép, chấm hộ
- Sửa ngày công: chỉ OWNER/HR, **lý do bắt buộc**, không sửa của chính mình (403 `SELF_EDIT_FORBIDDEN`) → `source = MANUAL`, audit.
- Nghỉ phép: OWNER/HR đánh dấu → `LEAVE`.
- Chấm công hộ: OWNER/HR/SECURITY, chỉ NV `attendance_method = MANUAL`, người chấm ≠ NV (403 `SELF_MANUAL_FORBIDDEN`), lý do bắt buộc, thời điểm = hiện tại → event `MANUAL_ATTENDANCE`. Có báo cáo số lượt theo người chấm (`/events/manual-report`).

## Xuất Excel tháng (`/attendance/export?month=`)
- Sheet **"Tổng hợp"**: Mã NV · Họ tên · Phòng ban · Ngày công (đếm ngày duy nhất NORMAL/LATE/EARLY/LATE_EARLY sau điều chỉnh, không cộng ngày riêng vì có giải trình) · Số lần muộn · Tổng phút muộn · Tổng phút về sớm · Số ngày vắng · Số ngày thiếu giờ ra · Số ngày nghỉ phép.
- Sheet **"Chi tiết"**: Mã NV · Họ tên · Ngày (dd/MM/yyyy) · Ca · Giờ vào · Giờ ra (HH:mm) · Trạng thái (nhãn tiếng Việt từ `status.json`) · Nguồn · Phút muộn · Phút về sớm · Ghi chú (lý do sửa / giải trình).
- Tên file: `bang-cong-YYYY-MM.xlsx`. Dùng openpyxl; cột ngày/giờ định dạng đúng kiểu ngày giờ Excel.

## Test bắt buộc (`hub/tests/test_attendance_rules.py`)
đi muộn · về sớm · ra ăn trưa quên quét (→ MISSING_OUT + cờ) · đến sớm hơn 3 h · ngày lễ · không ca · cửa ACCESS_ONLY không tính công · giải trình duyệt/từ chối · quản lý tự gửi → chuyển HR · chấm hộ chính mình → 403 · event đến sau thời điểm chốt.

## Quyết định Q-001/Q-008–Q-011
- MANAGER xuất Excel chỉ team, thiếu lọc vẫn giới hạn, lọc ngoài scope bị 403.
- NOT_STARTED trước start; WAITING_IN từ start chưa vào/chưa chốt; IN_PROGRESS đã vào/chưa chốt, nhóm đủ giờ chỉ sau chốt, ưu tiên lễ/nghỉ/không ca.
- Tự recompute giữ sửa MANUAL/LEAVE. Event nhận muộn dùng occurred_at trong cửa sổ ca tính lại ngày đã chốt, giữ finalized=true; ngoài cửa sổ chỉ ra vào.
- Xét vai trò **người gửi** theo nhánh đầu tiên phù hợp: (1) có OWNER, kể cả kiêm HR → HR khác; (2) HR không OWNER → OWNER khác; (3) MANAGER chính phòng mình, không OWNER/HR → HR khác; (4) còn lại → MANAGER đúng phòng ban người gửi, khác người gửi. MANAGER chỉ quản lý phòng khác thuộc nhánh (4). Không có người duyệt hợp lệ thì giữ PENDING, hiện cần bố trí người duyệt. Server luôn chặn tự duyệt; thứ tự chỉ dùng chọn nhóm duyệt, không loại bỏ quyền khác của tài khoản.
- Test thêm WAITING_IN/biên grace/làm tròn phút/giao nghỉ/ngày không đếm trùng, bảo toàn sửa/LEAVE và event muộn sau chốt.
