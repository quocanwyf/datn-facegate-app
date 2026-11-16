# Báo cáo T09 — Chấm công backend

- Trạng thái: **XONG** phần backend T09; giao diện quản trị ở T10, giao diện cá nhân ở T12.
- Commit: ghi trong lịch sử Git của thư mục này.
- Máy: Windows, PostgreSQL 16; phiên bản Python/thư viện ở `environment.log`.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Bằng chứng |
|---|---|---|---|
| 1 | Quy tắc chấm công và chuyển cấp đủ ca | Test giờ cố định theo Asia/Ho_Chi_Minh: grace cả giây, làm tròn phút, giao giờ nghỉ, WAITING_IN, IN_PROGRESS, chốt, thiếu ra, lễ, nghỉ, không ca, chuyển cấp nhiều role | `pytest.log`, `tests/test_attendance_rules.py` |
| 2 | recompute idempotent | Tính hai lần giữ cùng id, updated_at, giờ, phút, trạng thái và finalized; event muộn cập nhật ngày đã chốt | `test_recompute_idempotent_late_event_and_window` |
| 3 | Excel tháng đủ 2 sheet/cột | File mở lại bằng openpyxl, kiểm tiêu đề, kiểu ngày/giờ, nhãn tiếng Việt, ngày công không trùng, team scope, chuỗi bắt đầu dấu = không thành công thức | `bang-cong-2026-11-test.xlsx`, test Excel |
| 4 | Contract Schedule/Attendance/Me | Có route thật, operationId khớp nguồn; response mẫu validate schema; GET không ghi dữ liệu | `pytest.log`, `test_openapi_contract.py`, `test_attendance_api.py` |

Toàn bộ backend: **129 passed, 2 skipped, 1 warning**, 78,43 giây. Hai skip là kiểm màu LFW T02 và smoke ảnh webcam khi chưa truyền biến môi trường; không phải test T09. Warning còn lại là thông báo deprecation từ Starlette TestClient/httpx. Không có test T09 bị skip.

## Đã làm

- CRUD ca/phân ca/ngày lễ; EXCLUDE PostgreSQL trả 409 ASSIGNMENT_OVERLAP, cá nhân ưu tiên phòng ban, kiểm quyền và company/team scope.
- Tính ngày từ event xảy ra trong cửa sổ ca; ACCESS_ONLY không tính công. Giữ sửa MANUAL, ý định LEAVE và finalized khi nhận event muộn. HOLIDAY đứng trước LEAVE; audit lệnh nghỉ giữ ý định nghỉ để khi xóa ngày lễ thì LEAVE phục hồi, không thêm cột DB.
- Ghi event MATCH và tính công cùng transaction; trả IN/OUT/NONE và trạng thái tạm thời cho Kiosk. Không đổi bộ nhận dạng, vendor hoặc hợp đồng WS.
- APScheduler lập job đúng end + attendance_window_after_h; quét bù ngày thiếu khi khởi động, làm nền để không giữ API chờ; làm mới lịch mỗi phút, lỗi DB sẽ thử lại. Job kiểm lại ca tại lúc chạy.
- API sửa/nghỉ/chấm hộ, gửi/hủy/duyệt/từ chối giải trình, bản thân và Excel. Chặn tự sửa, tự chấm hộ, tự duyệt ở server; Q-011 xét vai trò người gửi đúng thứ tự. Không có người hợp lệ thì không tự duyệt.
- `verify_t09.py` tạo DB riêng, migrate/seed chính thức, chạy test có rollback. Fixture giờ/event/ngày công chỉ dùng trong test; không đưa vào DB demo, không là bằng chứng nhận dạng.

## Vấn đề và cách xử lý

- PostgreSQL riêng sau khởi động máy không bind được cổng 5433. Đã khôi phục data directory cũ trên 127.0.0.1:15433, cập nhật cấu hình local ignored và cổng khởi động của PostgreSQL riêng. Không đổi PostgreSQL hệ thống ở 5432; không đưa mật khẩu vào log/Git.
- Lượt đầu thiếu thuộc tính bắt buộc trong fixture DB (model đã có trong seed, consent phải đủ at/by, device ACTIVE cần token hash). Đã sửa fixture theo ràng buộc thật, không nới DB. Giữ log các lượt đầu riêng.
- Test giao thức WS dùng service double nên không khởi động job DB thật; inject attendance_factory=None trong fixture. Ứng dụng thật vẫn bật scheduler mặc định. Khắc phục việc scheduler ngoài transaction test làm ảnh hưởng DB kiểm thử.
- Không thay OpenAPI, đặc tả, DB chuẩn hoặc token UI.

## Review

Xem `REVIEW-T09.md`. Phần mềm tiếp tục T10 → T12; không yêu cầu ngồi chung ở T09. Phép đo người thật và chống giả mạo vẫn ghi riêng trong T08/T13/T14.
