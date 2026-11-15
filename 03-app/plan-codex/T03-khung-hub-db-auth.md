# T03 — Khung Hub, CSDL bằng Alembic, xác thực + phân quyền
> Phụ thuộc: T00 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T03/bao-cao.md`.

## Mục tiêu
Hub FastAPI chạy được với DB tạo bằng Alembic (tương đương `schema.sql`), đăng nhập JWT, phân quyền theo vai trò + phạm vi.

## Đọc trước
`03-app/db/thiet-ke-db.md` · `03-app/db/schema.sql` · `03-app/openapi/openapi.yaml` (tag Auth, Me, System) · đặc tả §6, §10.1 · skill `hub-rules`, `api-contract` · `03-app/hub/AGENTS.md`.

## Được ghi vào
`03-app/hub/` (trừ `vendor/`) · `03-app/ket-qua-kiem-thu/<ngày>_T03/`.

## Các bước
1. Khung `app/` theo `hub/AGENTS.md`; `config.py` đọc `.env`; tiền tố `/api/v1`; middleware lỗi → dạng `Error`.
2. `db/models.py` (SQLAlchemy 2) cho 23 bảng; Alembic revision đầu: tạo bảng + CHECK + partial unique + EXCLUDE (btree_gist) + trigger (`op.execute` SQL thô lấy từ `schema.sql` cho phần ORM không diễn tả được).
3. `scripts/seed.py`: nạp `03-app/db/seed.sql` vào DB đã migrate.
4. Auth: `POST /auth/login|refresh|logout|change-password` (argon2id, JWT access 15 phút, refresh 7 ngày lưu băm trong `auth_refresh_token`, xoay vòng; đổi mật khẩu thu hồi mọi refresh token); `GET /me`; `GET /health`, `/version`.
5. RBAC: dependency `require_roles(...)` + helper phạm vi MANAGER (`scope_department_id`); đọc vai trò từ DB mỗi request.
6. Test: auth (sai mật khẩu, hết hạn, refresh xoay vòng, token cũ bị từ chối), RBAC (mỗi vai trò gọi 1 endpoint được + 1 không được).

## Tiêu chí nghiệm thu
| # | Tiêu chí | Cách kiểm |
|---|---|---|
| 1 | DB mới tạo bằng `alembic upgrade head` → `test_constraints.sql` = **44/44** | log psql |
| 2 | `pg_dump --schema-only` của DB Alembic và DB từ `schema.sql` không khác về bảng/cột/kiểu/ràng buộc/trigger (cho phép khác tên ràng buộc tự sinh) | file diff + giải thích từng dòng khác |
| 3 | Seed nạp được; đăng nhập `nv001@demo.local` / `Demo@123` lấy token | test |
| 4 | Test auth + RBAC pass | pytest log |
| 5 | `GET /health` trả `db: true` | output |

## Điều kiện dừng
Không diễn tả được ràng buộc nào của `schema.sql` → dừng, báo (không bỏ ràng buộc).

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Schema có WAITING_IN; vẫn chạy 44/44 ca gốc và thêm kiểm riêng WAITING_IN không check_in/finalized=false bằng transaction rollback. Health vẫn phục vụ khi model chưa xác minh, model_verified=false/degraded, không nhận dạng.
