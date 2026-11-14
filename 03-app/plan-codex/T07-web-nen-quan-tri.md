# T07 — Web: nền (theme, shell, đăng nhập) + màn quản trị lõi
> Phụ thuộc: T06 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T07/bao-cao.md`.

## Mục tiêu
Web Admin chạy được với theme Canopy, đăng nhập, phân quyền route và các màn W-01, W-03, W-04, W-05, W-07, W-08, W-14, W-16.

## Đọc trước
`03-app/ui/design-system.md` · `ui/man-hinh/admin.md`, `ui/man-hinh/me.md` (E-01) · `ui/tokens/*` · `03-app/web/AGENTS.md` · skill `api-contract`, `react-best-practices`, `web-design-guidelines`, `gsap`, `playwright`.

## Được ghi vào
`03-app/web/` · `03-app/ket-qua-kiem-thu/<ngày>_T07/`.

## Các bước
1. Vite + React + TS + AntD 5; `theme/antdTheme.ts` từ `web-antd-theme.json` (token không có trong phiên bản AntD thì bỏ và ghi lại); font Be Vietnam Pro + Inter **subset vietnamese**; `web-css-vars.css`; `status.ts` từ `status.json`.
2. Component chung: `AppShell` (Sider gradient, Header, chấm Hub, chuông), `PageHero`, `StatusPill`, `KpiTile`.
3. Đăng nhập (E-01/W-01), làm mới token, route guard theo vai trò, trang chọn `/admin` hay `/me`.
4. Các màn W-03, W-04, W-05, W-07 (kèm modal QR ghép thiết bị), W-08, W-14, W-16 đúng `admin.md`.
5. GSAP: chuyển trang + stagger hàng bảng (design-system §7).
6. Playwright: đăng nhập theo từng vai trò (OWNER, HR, SECURITY, MANAGER, EMPLOYEE) → kiểm menu đúng quyền; luồng duyệt hồ sơ khuôn mặt (dùng hồ sơ tạo ở T05); chụp màn mỗi trang.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | `pnpm typecheck`, `pnpm lint` sạch |
| 2 | Playwright pass; ảnh chụp mọi màn trong `ket-qua-kiem-thu/<ngày>_T07/screens/` |
| 3 | Chữ tiếng Việt có dấu hiển thị đúng font (ảnh chụp chữ "Đăng nhập, Nhân viên, Bảng công, Giải trình, Xác nhận khuôn mặt") |
| 4 | Không có mã màu hex ngoài thư mục `theme/` (`rg "#[0-9A-Fa-f]{6}" src --glob '!src/theme/**'` rỗng) |
| 5 | Chạy skill `web-design-guidelines` rà các màn; ghi điểm đã sửa |
