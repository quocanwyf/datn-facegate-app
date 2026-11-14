# T09 — Chấm công (backend)
> Phụ thuộc: T06 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T09/bao-cao.md`.

## Mục tiêu
Toàn bộ nghiệp vụ chấm công: ca, phân ca, ngày lễ, ngày công, chốt, giải trình, chấm hộ, nghỉ phép, xuất Excel, API `/me/*`.

## Đọc trước
Skill `cham-cong-vn` (bắt buộc) · đặc tả §5.5–5.8 · `openapi.yaml` (tag Schedule, Attendance, Me) · `db/thiet-ke-db.md` §4.4, §5.

## Được ghi vào
`03-app/hub/` · `03-app/ket-qua-kiem-thu/<ngày>_T09/`.

## Các bước
1. `/shifts`, `/shift-assignments` (409 khi chồng — bắt lỗi EXCLUDE), `/holidays`.
2. `biz/attendance.py`: `recompute_day`, `finalize_day`; Scheduler (APScheduler) chạy `finalize_day` lúc `end + 4h` của từng ca.
3. Nối vào luồng MATCH (T05): event tại cửa chấm công → `recompute_day` → `result.attendance {kind IN/OUT, time, status}`.
4. `/attendance/days` (+ PATCH có lý do, chặn tự sửa), `/attendance/leave`, `/attendance/manual`, `/attendance/requests` (+ approve/reject, luật người duyệt), `/attendance/export` (openpyxl, đúng cột trong skill).
5. `/me/today`, `/me/attendance`, `/me/days/{date}`, `/me/requests` (+ cancel).
6. `tests/test_attendance_rules.py` đủ các ca trong skill `cham-cong-vn`; test giờ dùng thời gian cố định (freezegun hoặc tham số `now`), múi giờ `Asia/Ho_Chi_Minh`.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | `test_attendance_rules.py` pass, liệt kê từng ca |
| 2 | `recompute_day` idempotent: chạy 2 lần cho cùng ngày → không đổi (test) |
| 3 | File Excel mẫu tháng (dữ liệu test) mở được, đúng 2 sheet + cột; đính kèm file trong thư mục kết quả |
| 4 | Contract test phần Schedule/Attendance/Me pass |
