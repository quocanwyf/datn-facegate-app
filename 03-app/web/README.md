# FaceGate Web — T07

React 18 · Vite · TypeScript strict · Ant Design 5 · Canopy. API và type sinh từ `../openapi/openapi.yaml`.

## Chạy giao diện với Hub đang hoạt động

Tại thư mục `03-app/web`:

```powershell
& "$env:APPDATA/npm/pnpm.cmd" install --frozen-lockfile
& "$env:APPDATA/npm/pnpm.cmd" dev
```

Mở http://127.0.0.1:5173/login. Proxy mặc định `/api` → http://127.0.0.1:8000. Có thể đặt `FACEGATE_HUB_URL` trước khi khởi động Vite để dùng Hub khác.

Màn T07: đăng nhập/đổi mật khẩu/chọn không gian; nhân viên và chi tiết; phòng ban/tài khoản; cửa và QR ghép thiết bị; duyệt khuôn mặt; cấu hình nhận dạng; nhật ký. Dashboard có KPI thật; bảng event/realtime hoàn thiện trong T11. Các tab ca/công/event của nhân viên nối tiếp ở T10–T11; `/me` ở T12.

Phiên chỉ giữ trong bộ nhớ tab. Access token được làm mới tự động, các request đồng thời dùng chung một lượt xoay refresh; tải lại trang cần đăng nhập lại. Lỗi refresh 401 xoá phiên. Đăng xuất/đổi mật khẩu theo API thật.

## Kiểm tra

```powershell
& "$env:APPDATA/npm/pnpm.cmd" gen:api
& "$env:APPDATA/npm/pnpm.cmd" typecheck
& "$env:APPDATA/npm/pnpm.cmd" lint
& "$env:APPDATA/npm/pnpm.cmd" build
& "$env:APPDATA/npm/pnpm.cmd" exec playwright install chromium
& "$env:APPDATA/npm/pnpm.cmd" test:e2e
```

Bộ trên dùng API fixture để kiểm các nhánh lỗi và form, không ghi DB. Bộ `playwright.real.config.ts` dùng Hub thật và DB kiểm thử riêng; tạo bằng `tests/start_real_hub.py`, dùng 5 mẫu nhận đủ từ ảnh thật ngoài repo. Chi tiết trong [kịch bản T07](../ket-qua-kiem-thu/2026-11-15_T07/REVIEW-T07.md). Ảnh sinh trắc chỉ nằm tại AppData, ảnh chụp đưa vào Git che từng ảnh mẫu ngay khi Playwright chụp; không bật trace/video cho bộ thật.

`review:auth` và `review-employees.cmd` vẫn là chế độ xem fixture riêng, không dùng để khẳng định Hub thật hoạt động.
