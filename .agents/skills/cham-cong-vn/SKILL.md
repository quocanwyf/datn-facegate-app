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
`HOLIDAY` → `LEAVE` → `OFF` (không ca) → `NOT_STARTED` (chưa tới giờ vào, chưa quét) → `IN_PROGRESS` (chưa tới thời điểm chốt `end + 4h`, đã vào) → `ABSENT` (đã chốt, không vào) → `MISSING_OUT` (đã chốt, có vào, không ra **hoặc** ra trước `end − forgot_out_before_end_h` → bật `suspect_forgot_out`) → `NORMAL` / `LATE` / `EARLY` / `LATE_EARLY` với `late = check_in > start + grace_in`, `early = end − 2h ≤ check_out < end − grace_out`.
Kèm `late_min`, `early_min`, `worked_min` (trừ nghỉ trưa cố định).

## Hàm
- `recompute_day(employee_id, work_date)` **idempotent**: tính lại toàn bộ từ event + giải trình APPROVED + holiday/leave. Gọi khi có event mới, khi duyệt giải trình, khi sửa tay, khi chốt.
- `finalize_day` chạy lúc `end + 4h` (Scheduler) → `finalized = true`. Không gửi kết luận "thiếu chấm công" trước thời điểm chốt.

## Giải trình
- Loại: FORGOT_IN (cần giờ vào) · FORGOT_OUT (cần giờ ra) · NOT_RECOGNIZED · BUSINESS_TRIP · OTHER; mỗi NV mỗi ngày tối đa 1 giải trình `PENDING` (409 `REQUEST_PENDING_EXISTS`).
- Người duyệt: MANAGER của phòng ban người gửi; **người duyệt ≠ người gửi** (403 `SELF_REVIEW_FORBIDDEN`): MANAGER gửi → HR duyệt; HR gửi → OWNER; OWNER gửi → HR.
- Duyệt → `recompute_day` dùng giờ đề nghị, `source = ADJUSTED`, giữ event gốc.

## Sửa tay, nghỉ phép, chấm hộ
- Sửa ngày công: chỉ OWNER/HR, **lý do bắt buộc**, không sửa của chính mình (403 `SELF_EDIT_FORBIDDEN`) → `source = MANUAL`, audit.
- Nghỉ phép: OWNER/HR đánh dấu → `LEAVE`.
- Chấm công hộ: OWNER/HR/SECURITY, chỉ NV `attendance_method = MANUAL`, người chấm ≠ NV (403 `SELF_MANUAL_FORBIDDEN`), lý do bắt buộc, thời điểm = hiện tại → event `MANUAL_ATTENDANCE`. Có báo cáo số lượt theo người chấm (`/events/manual-report`).

## Xuất Excel tháng (`/attendance/export?month=`)
- Sheet **"Tổng hợp"**: Mã NV · Họ tên · Phòng ban · Ngày công (NORMAL+LATE+EARLY+LATE_EARLY+ngày được duyệt giải trình) · Số lần muộn · Tổng phút muộn · Tổng phút về sớm · Số ngày vắng · Số ngày thiếu giờ ra · Số ngày nghỉ phép.
- Sheet **"Chi tiết"**: Mã NV · Họ tên · Ngày (dd/MM/yyyy) · Ca · Giờ vào · Giờ ra (HH:mm) · Trạng thái (nhãn tiếng Việt từ `status.json`) · Nguồn · Phút muộn · Phút về sớm · Ghi chú (lý do sửa / giải trình).
- Tên file: `bang-cong-YYYY-MM.xlsx`. Dùng openpyxl; cột ngày/giờ định dạng đúng kiểu ngày giờ Excel.

## Test bắt buộc (`hub/tests/test_attendance_rules.py`)
đi muộn · về sớm · ra ăn trưa quên quét (→ MISSING_OUT + cờ) · đến sớm hơn 3 h · ngày lễ · không ca · cửa ACCESS_ONLY không tính công · giải trình duyệt/từ chối · quản lý tự gửi → chuyển HR · chấm hộ chính mình → 403 · event đến sau thời điểm chốt.
