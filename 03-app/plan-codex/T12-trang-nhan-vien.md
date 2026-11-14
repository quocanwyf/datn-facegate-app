# T12 — Trang nhân viên `/me`
> Phụ thuộc: T07, T09 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T12/bao-cao.md`.

## Mục tiêu
E-01 … E-10 (trừ E-07, E-09) đúng `ui/man-hinh/me.md`, dùng tốt trên điện thoại.

## Đọc trước
`ui/man-hinh/me.md` · `ui/design-system.md` · skill `api-contract`, `gsap`, `playwright`.

## Được ghi vào
`03-app/web/` · `03-app/ket-qua-kiem-thu/<ngày>_T12/`.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | Playwright viewport 390×844: mọi màn không tràn ngang, thanh dưới cố định, chạm được (ảnh chụp) |
| 2 | E-02 khớp DB cho 3 trường hợp: chưa quét / đã vào / đã vào + ra |
| 3 | E-10 không hiện giải trình của chính người duyệt |
| 4 | Rút đồng ý (E-08) → NV chuyển MANUAL, dữ liệu khuôn mặt bị xoá (kiểm DB) |
| 5 | Mở được từ máy ảo Android bằng trình duyệt tới `http://10.0.2.2:5173/me` (ảnh chụp) |
