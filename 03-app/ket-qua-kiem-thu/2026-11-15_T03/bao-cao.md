# Báo cáo T03 — Khung Hub, Alembic, xác thực và phân quyền

- Trạng thái: XONG phạm vi T03.
- Commit nền: 6a1411b; commit triển khai tra lịch sử `T03: implement database migrations and JWT authentication`.
- Máy: Windows 11, Python 3.13.13, PostgreSQL 16.16 native cổng 5433; FastAPI 0.163.0, SQLAlchemy 2.1.8, asyncpg 0.32.0, Alembic 1.20.1 (`install.log`, `install-asyncio.log`). CPU; T03 không cần checkpoint.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | DB Alembic mới: 44/44 | 44 tổng, 44 đạt, transaction rollback | constraints.log, test-databases.json | Đạt |
| 2 | pg_dump schema tương đương | Diff chuẩn hóa rỗng; đủ bảng/cột/constraint/index/function/trigger | ref-schema.sql, migrated-schema.sql, schema.diff, schema-raw.diff | Đạt |
| 3 | Seed và login nv001@demo.local / Demo@123 | HTTP 200, đúng NV001/OWNER+EMPLOYEE, access 900 giây | seed.log, http-smoke.log, pytest.log | Đạt |
| 4 | Test auth và RBAC | **30 passed, 1 skipped** trong 24,75 giây; skip thuộc T02 thiếu LFW | pytest.log | Đạt |
| 5 | Health db=true | HTTP thật: db=true, degraded/model_verified=false | http-smoke.log | Đạt |
| Bổ sung | WAITING_IN / health khi chưa xác minh | Hợp lệ không giờ vào/chưa chốt; hai UPDATE vi phạm đều bị CHECK chặn; rollback. Nhận dạng chưa bật | tests/test_auth.py, pytest.log | Đạt |

## Đã làm

SQLAlchemy 2 có đủ 23 bảng. Bổ sung rõ EXCLUDE, NULLS NOT DISTINCT, biểu thức và chiều DESC của index sau khi sinh model từ schema. Toàn bộ DDL ORM compile được; Alembic compare_metadata với DB tham chiếu trả `[]`. Trigger được giữ nguyên trong bản SQL cố định đi cùng revision; không dùng create_all thay migration.

Migration dùng bản sao schema tại thời điểm triển khai, không đọc trực tiếp tài liệu có thể thay đổi về sau. Công cụ verify tạo hai DB mới có tên trong test-databases.json, không reset DB demo. Chỉ tạo dữ liệu kiểm constraint trong transaction rollback theo plan; không seed mặt, event hay ngày công.

Auth dùng argon2id trong thread pool, JWT access 15 phút/refresh 7 ngày, DB chỉ lưu SHA256 refresh. Xoay refresh có khóa hàng, test hai request đồng thời chỉ một 200/một 401. Đổi mật khẩu thu hồi toàn bộ refresh. Mỗi request đọc lại tài khoản/vai trò từ DB; kiểm MANAGER theo phòng ban và công ty. CORS giới hạn origin .env. Lỗi có envelope tiếng Việt và không echo mật khẩu/token/input.

Hub đang chạy cổng 8000 trên máy Hy. Lõi nhận dạng/worker/gallery thuộc T04 nên health degraded đúng trạng thái, không nhận dạng hoặc mở cửa bằng mặt. Không archive FG-AUTH-001 vì còn nghiệm thu giao diện T07/T12.

## Vấn đề gặp và xử lý

- Lần đầu thiếu greenlet khi dùng SQLAlchemy async: đổi dependency thành SQLAlchemy[asyncio]; đã cài và kiểm lại.
- `schema-raw.diff` chỉ khác nonce `\\restrict`/`\\unrestrict` do pg_dump tự sinh và dòng trắng trong thân ba hàm PL/pgSQL do CRLF. Không thay câu SQL/cột/constraint/trigger. Công cụ giữ raw diff và chỉ chuẩn hóa hai loại khác biệt này.
- Test đầu kỳ vọng must_change_password=true nhưng seed thực tế đặt false. Giữ nguyên seed, sửa kỳ vọng và thêm test đặt true trong giao dịch rollback để kiểm đúng cả hai trạng thái (`pytest-first-run.log` giữ bằng chứng lần lỗi).
- Pydantic EmailStr mặc định chặn tên miền demo.local. Kiểm cú pháp email theo format của OpenAPI cho phép tài khoản seed; không kiểm DNS/TLD ngoài hợp đồng.
- Trình sinh model cảnh báo FK vòng employee ↔ user_account. Hai FK vẫn giữ đầy đủ; raw migration tạo đúng thứ tự và thêm FK consent sau. compare_metadata không có khác biệt.

## File đã tạo / sửa

app/config.py, app/main.py, app/errors.py, app/api/, app/auth/, app/db/; alembic.ini và alembic/; scripts/seed.py, scripts/verify_t03_db.py; tests/test_auth.py; requirements.txt, pyproject.toml; báo cáo/log và REVIEW-T03.md.

## Đề xuất cho thiết kế

Không sửa nguồn chuẩn, không cần đổi schema/hợp đồng. Endpoint tài nguyên và kiểm toàn bộ đường dẫn OpenAPI tiếp tục T06; UI và phiên trình duyệt tiếp tục T07/T12.

## Cần An làm

Không cần thao tác để tiếp tục T04. T02 vẫn chờ chạy riêng theo RUN-T02.md lúc An rảnh.
