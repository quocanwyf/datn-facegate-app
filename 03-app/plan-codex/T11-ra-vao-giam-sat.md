# T11 — Ra vào & giám sát (backend + web)
> Phụ thuộc: T05, T07 · Máy: máy Hy · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T11/bao-cao.md`.

## Mục tiêu
Kênh `/ws/monitor`, API sự kiện, mở cửa thủ công, báo cáo chấm hộ; màn W-02, W-10, W-11.

## Đọc trước
`openapi/ws-protocol.md` §2 · `openapi.yaml` (tag Events, Gates manual-open, Dashboard) · `ui/man-hinh/admin.md` (W-02, W-10, W-11) · đặc tả §5.4, F-06 trong `docs/lich-su-thiet-ke/thiet-ke-gd3.md` · skill `kiosk-ws-protocol`, `gsap`.

## Được ghi vào
`03-app/hub/` · `03-app/web/` · `03-app/ket-qua-kiem-thu/<ngày>_T11/`.

## Các bước
1. `/ws/monitor` (auth message đầu, lọc theo vai trò/phạm vi, các message ở ws-protocol §2); phát `event`/`alert` từ luồng T05.
2. `/events` (lọc), `/events/{id}/snapshot`, `/events/{id}/handle` (chỉ UNKNOWN/SPOOF; IS_EMPLOYEE không thêm ảnh vào hồ sơ), `/events/manual-report`, `/events/export` (CSV UTF-8 có BOM để Excel đọc tiếng Việt), `/gates/{id}/manual-open`.
3. Web: W-02 (KPI đếm GSAP), W-10 (3 vùng, event trượt vào, SPOOF rung, chấm hộ + mở cửa tay), W-11 (2 tab).

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | Quét bằng `kiosk_sim.py` → event hiện trên W-10 (ghi độ trễ đo được từ lúc Hub ghi event tới lúc web nhận; mục tiêu ≤ 1 s) |
| 2 | SECURITY không nhận dữ liệu ngoài phạm vi; MANAGER chỉ thấy team (test) |
| 3 | Xử lý cảnh báo IS_EMPLOYEE không đổi số mẫu của NV (test) |
| 4 | CSV mở bằng Excel hiện đúng tiếng Việt (ảnh chụp) |

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Test SUSPENDED định danh DENIED_INACTIVE không mở/công; KPI người lạ đếm UNKNOWN không SPOOF theo ngày công ty; không event giả vì gallery rỗng.
