# T00 — Môi trường dev, skill ngoài, cơ sở dữ liệu
> Phụ thuộc: — · Máy: máy Hy (Windows) · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T00/bao-cao.md`.

## Mục tiêu
Máy Hy chạy được: PostgreSQL 16 với schema + seed của dự án, Python, Node, máy ảo Android; repo có đủ skill ngoài.

## Đọc trước
`README-BAN-GIAO.md` · `AGENTS.md` · `03-app/SKILLS-NGOAI.md` · `03-app/db/thiet-ke-db.md` (mục 7–8) · `03-app/kiosk/AGENTS.md` (phần máy ảo).

## Được ghi vào
`.agents/skills/` (skill ngoài + `NGUON.md`) · `.env` (không commit) · `03-app/ket-qua-kiem-thu/<ngày>_T00/`.

## Các bước
1. Cài (ưu tiên `winget`): Git, Python 3.13, Node.js LTS (≥ 20) + `corepack enable` (pnpm), PostgreSQL 16, Android Studio. Ghi lệnh đã dùng.
2. Tạo DB: role `facegate` (mật khẩu tự đặt), DB `facegate_dev` owner `facegate`. Chạy lần lượt `03-app/db/schema.sql`, `03-app/db/seed.sql` bằng `psql -v ON_ERROR_STOP=1`.
3. Chạy `03-app/db/test_constraints.sql` (tự ROLLBACK) — lưu output.
4. `copy .env.example .env`, điền `DATABASE_URL`; `JWT_SECRET` sinh bằng `python -c "import secrets;print(secrets.token_urlsafe(48))"`.
5. Cài skill ngoài theo `03-app/SKILLS-NGOAI.md` vào `.agents/skills/` của repo; viết `.agents/skills/NGUON.md`.
6. Android Studio: tạo AVD tablet ngang (API 34+), Camera Front = **Webcam0**; khởi động, mở app Camera của máy ảo, chụp màn hình thấy hình webcam.
7. Chạy `python 03-app/tools/kiem-bi-mat.py` (kiểm repo không có file cấm) — phải sạch.

## Tiêu chí nghiệm thu
| # | Tiêu chí | Cách kiểm |
|---|---|---|
| 1 | Phiên bản Python, Node, pnpm, psql, Android Studio/AVD ghi trong báo cáo | output lệnh `--version` |
| 2 | `schema.sql` + `seed.sql` chạy không lỗi; `select count(*) from employee` = 24 | log psql |
| 3 | `test_constraints.sql` cho dòng cuối **`44 | 44`** | log psql |
| 4 | Mỗi skill trong `SKILLS-NGOAI.md`: đã cài (đường dẫn) hoặc ghi rõ lý do bỏ qua | `NGUON.md` |
| 5 | Máy ảo hiện hình webcam | ảnh chụp màn |
| 6 | `kiem-bi-mat.py` báo sạch; `.env` không bị git theo dõi | output + `git status` |

## Điều kiện dừng
- Không cài được PostgreSQL 16 hoặc `test_constraints.sql` khác 44/44 → dừng, **không sửa file trong `03-app/db/`**, báo An.
- Máy không có webcam / AVD không lấy được webcam → ghi lại, vẫn hoàn thành phần còn lại (An quyết phương án khác ở T08).
