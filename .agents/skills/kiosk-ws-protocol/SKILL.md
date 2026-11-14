---
name: kiosk-ws-protocol
description: Giao thức WebSocket giữa Kiosk App và Hub (/api/v1/ws/kiosk) và kênh giám sát (/api/v1/ws/monitor) — dùng khi viết KioskSocket, màn K-02/K-04/K-08, endpoint ws_kiosk.py, ws_monitor.py hoặc kiosk_sim.py. Bản demo dùng ws:// trong LAN.
---

# kiosk-ws-protocol
Chi tiết đầy đủ: `03-app/openapi/ws-protocol.md`. Tóm tắt luật không được sai:

1. **Auth bằng message đầu tiên** `{"type":"auth","device_token":…}` trong 5 s; không đặt token trong URL. Sai → `error` + đóng 4401.
2. **Dừng-và-chờ:** JSON `{"type":"frame","seq":n,"mode":"recognize"|"enroll",…}` rồi **ngay sau** là binary JPEG. Không gửi khung `n+1` trước khi nhận `state`/`result` của `n`; giới hạn `max_fps` từ `config`.
3. Ảnh gửi: cạnh dài `frame_long_side` (640), JPEG `jpeg_quality` (80), camera trước đã lật gương (embedding bất biến với lật; chỉ ảnh hưởng hướng hiển thị bbox).
4. `result` ∈ OK / ALREADY / DENY (+ `reason` UNKNOWN|SPOOF|RULE|INACTIVE). Hiển thị theo `ui/man-hinh/kiosk.md` K-04 + `status.json` `kiosk.display`. Trong `result_display_sec` không gửi khung.
5. `BUSY` → chờ 200 ms gửi lại. Không nhận gì 15 s → K-11, nối lại lùi dần 1→2→4→8 s (tối đa 15 s).
6. Enroll: kèm `enroll_session_id`, `employee_id`; nhận `enroll_progress` (accepted/5, `reason` loại mẫu) → `enroll_done` (`PENDING_REVIEW`, `duplicate_warning`).
7. Hub **không bao giờ** gửi ảnh khuôn mặt về Kiosk.
8. `/ws/monitor`: auth bằng access token ở message đầu; server lọc theo vai trò/phạm vi; message `event`, `alert`, `alert_handled`, `device_status`, `counters`.
Kiểm: `hub/tests/test_ws_kiosk.py`, `hub/scripts/kiosk_sim.py`.
