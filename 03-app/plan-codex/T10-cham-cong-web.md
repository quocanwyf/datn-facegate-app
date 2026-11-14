# T10 — Chấm công (web quản trị)
> Phụ thuộc: T07, T09 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T10/bao-cao.md`.

## Mục tiêu
Màn W-06 (ca, phân ca, ngày lễ), W-09 (bảng công tháng), W-12 (giải trình) đúng `ui/man-hinh/admin.md`.

## Đọc trước
`ui/man-hinh/admin.md` (W-06, W-09, W-12) · `ui/design-system.md` · skill `cham-cong-vn`, `api-contract`.

## Được ghi vào
`03-app/web/` · `03-app/ket-qua-kiem-thu/<ngày>_T10/`.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | Lưới W-09 đúng chữ tắt + màu theo `status.json`; tải Excel được |
| 2 | Không có nút sửa ô ngày công của chính mình; không có nút duyệt giải trình của chính mình (Playwright kiểm) |
| 3 | Lỗi `ASSIGNMENT_OVERLAP` hiện đúng câu tiếng Việt |
| 4 | Ảnh chụp 3 màn; typecheck/lint sạch |
