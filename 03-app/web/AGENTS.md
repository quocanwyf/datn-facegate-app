# AGENTS.md — Web (`/admin` + `/me`)

Đọc thêm skill `api-contract` và các skill ngoài: `react-best-practices`, `web-design-guidelines`, `gsap`, `playwright` (xem `03-app/SKILLS-NGOAI.md`).

## Stack
React 18 · Vite · TypeScript strict · **Ant Design 5** · React Router · TanStack Query · `openapi-typescript` + `openapi-fetch` (client sinh từ `03-app/openapi/openapi.yaml`) · dayjs (locale `vi`) · `lucide-react` · **GSAP** (`gsap` + `@gsap/react`) · `@fontsource/be-vietnam-pro` + `@fontsource/inter` (subset vietnamese) · Playwright cho E2E. Dùng pnpm.

## Cấu trúc
```
web/src/
  api/          # schema.d.ts (SINH TỰ ĐỘNG — không sửa tay), client.ts (openapi-fetch + làm mới token)
  theme/        # antdTheme.ts (= 03-app/ui/tokens/web-antd-theme.json), status.ts (= ui/tokens/status.json), fonts.ts
  components/   # StatusPill, KpiTile, PageHero, AppShell, …
  admin/        # màn W-xx (một thư mục mỗi màn)
  me/           # màn E-xx
  shared/       # auth, route guard theo vai trò, format ngày giờ
```

## Lệnh
```powershell
pnpm install
pnpm gen:api        # openapi-typescript ../openapi/openapi.yaml -o src/api/schema.d.ts
pnpm dev            # http://localhost:5173 (proxy /api → http://localhost:8000)
pnpm typecheck; pnpm lint; pnpm test:e2e
```

## Luật
1. **Không viết type API bằng tay.** Đổi API = đề xuất sửa `openapi.yaml` → An duyệt → `pnpm gen:api`.
2. Màu, chữ, bo góc **chỉ** qua theme (`ConfigProvider theme`) và `web-css-vars.css`; không hard-code hex trong component (trừ file theme).
3. Nhãn + màu trạng thái **chỉ** lấy từ `status.ts` (bản sao `ui/tokens/status.json`).
4. Mỗi màn theo đúng `03-app/ui/man-hinh/admin.md` / `me.md`: bố cục, dữ liệu, trạng thái tải/trống/lỗi/403, chữ tiếng Việt.
5. Route guard theo vai trò (đặc tả §6) — nhưng server vẫn là nơi kiểm quyền thật.
6. GSAP chỉ ở các chỗ ghi trong `design-system.md` §7; dùng `useGSAP` để tự dọn; tôn trọng `prefers-reduced-motion`.
7. `/me` thiết kế cho điện thoại 360–430 px (kiểm bằng Playwright viewport 390×844); `/admin` cho ≥ 1280 px.
8. Ngày `dd/MM/yyyy`, giờ `HH:mm`, múi giờ công ty (lấy từ API).
