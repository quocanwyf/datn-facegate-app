# T06 — REST theo openapi.yaml + client TypeScript
> Phụ thuộc: T03 · Máy: máy Hy · Cần checkpoint: không
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T06/bao-cao.md`.

## Mục tiêu
Cài các endpoint quản trị (trừ nhóm chấm công — T09, sự kiện/giám sát — T11) và dựng khung client TS cho web + kiosk.

## Đọc trước
`openapi.yaml` (tag Organization, Employees, Faces, Gates, Settings, Me một phần, Dashboard) · đặc tả §5.1, §5.9, §6 · skill `api-contract`, `hub-rules`.

## Được ghi vào
`03-app/hub/` · `03-app/web/` (chỉ `package.json` khung + `src/api/`) · `03-app/kiosk/` (chỉ `package.json` khung + `src/api/`) · `03-app/ket-qua-kiem-thu/<ngày>_T06/`.

## Các bước
1. Endpoint: `/departments`, `/users` (+ roles, kiosk-pin, reset-password), `/employees` (+ suspend, reactivate, terminate, DELETE face), `/face-profiles` (+ approve/reject → nạp lại gallery trước khi trả), `/face-samples/{id}/image`, `/gates` (+ allowed-departments), `/devices` (nếu T05 chưa làm), `/settings/recognition`, `/models/active`, `/audit-logs`, `/dashboard/today` (đếm từ DB), `/me/face`, `/me/face/revoke`.
2. Xoá dữ liệu khuôn mặt đúng skill `hub-rules` (file + DB + gallery + audit).
3. Audit cho mọi thao tác ghi quản trị (`action` liệt kê trong `thiet-ke-db.md` §4.5).
4. `tests/test_openapi_contract.py`: mọi path+method trong yaml có trong `app.openapi()`.
5. Khung client: `web/` và `kiosk/` có script `gen:api` = `openapi-typescript ../openapi/openapi.yaml -o src/api/schema.d.ts` + `src/api/client.ts` (openapi-fetch, gắn token).

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | Contract test pass (liệt kê path chưa cài nếu thuộc T09/T11 — được phép, ghi rõ) |
| 2 | Test quyền: mỗi ô của ma trận đặc tả §6 thuộc phạm vi task có ≥ 1 test |
| 3 | Terminate / xoá khuôn mặt: file + dòng biến mất, gallery giảm 1, có audit |
| 4 | `pnpm gen:api` chạy được ở cả `web/` và `kiosk/`; `tsc --noEmit` pass |
| 5 | Chạy skill `security review` cho phần auth/RBAC/device token; ghi kết quả |

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Test HR GET settings nhưng không PUT; HR sửa gate policy/departments không trường OWNER; MANAGER Excel chỉ team kể cả thiếu lọc/ngoài scope. 409 duyệt hồ sơ đồng thời, 503 xóa chưa xong/gallery lỗi. Sinh client với WAITING_IN, RecognitionSettings mới.
