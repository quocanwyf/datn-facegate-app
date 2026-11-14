# GIAO THỨC WEBSOCKET — Kiosk ↔ Hub và Giám sát
> Đi kèm `openapi.yaml` (REST). Theo `dac-ta-app.md` v1.4.2 §4.5, §5.3, §8. Bản demo: **WS thường (`ws://`) trong LAN**.
> Định dạng: message điều khiển là **JSON text frame**; ảnh camera là **binary frame** (JPEG) gửi ngay sau message `frame` tương ứng.

## 1. `/api/v1/ws/kiosk`
### 1.1 Kết nối và xác thực
1. Kiosk mở `ws://<hub>/api/v1/ws/kiosk` (**không** đặt token trong URL).
2. Message đầu tiên **bắt buộc** trong 5 s: `{"type":"auth","device_token":"…","app_version":"1.0.0"}`.
3. Hub trả `{"type":"config", …}` (mục 1.3) hoặc `{"type":"error","code":"DEVICE_REVOKED"|"TOKEN_INVALID"}` rồi đóng (close code 4401).
4. Hub cập nhật `device.last_seen_at`, đẩy `device_status` lên `/ws/monitor`.
5. Ping: Kiosk gửi `{"type":"ping"}` mỗi 10 s khi không có khung; Hub trả `{"type":"pong"}`. Không nhận được gì trong 15 s → Kiosk coi là mất kết nối (K-11).

### 1.2 Gửi khung — DỪNG-VÀ-CHỜ
```
Kiosk: {"type":"frame","seq":42,"mode":"recognize"}      ← JSON
Kiosk: <binary JPEG, cạnh dài ≤ 640, chất lượng 80>          ← binary ngay sau
Hub:   {"type":"state", "seq":42, …} | {"type":"result","seq":42, …}
Kiosk: chỉ gửi seq 43 SAU KHI nhận phản hồi của seq 42 (và cách khung trước ≥ 1/max_fps giây)
```
- `seq` tăng dần trong một kết nối; Hub bỏ khung có `seq` ≤ seq đã xử lý.
- Chế độ đăng ký: `{"type":"frame","seq":7,"mode":"enroll","enroll_session_id":"…","employee_id":"…"}`.
- Hub xử lý khung trong **worker suy luận riêng**; nếu hàng đợi đầy (> 2 khung/thiết bị) trả `{"type":"state","seq":n,"state":"BUSY"}` — Kiosk chờ 200 ms rồi gửi tiếp.
- Sau `result`, Kiosk hiển thị K-04 trong `result_display_sec` và **không gửi khung** trong thời gian đó.

### 1.3 Message Hub → Kiosk
| `type` | Trường | Ý nghĩa |
|---|---|---|
| `config` | `gate{id,name,mode}`, `research_banner` (chuỗi), `max_fps`, `frame_long_side`, `jpeg_quality`, `result_display_sec`, `server_time` | Gửi sau auth và khi cấu hình đổi |
| `state` | `seq`, `state`, `bbox?` `[x,y,w,h]` theo toạ độ ảnh đã gửi, `frames_in_window?` | Phản hồi khung chưa đi tới kết luận |
| `result` | `seq`, `result`, `reason?`, `employee?{name,code}`, `attendance?{kind,time,status}`, `door`, `message` | Kết luận của bộ quyết định (mục 1.4) |
| `enroll_progress` | `seq`, `accepted` (0–5), `total` (5), `reason?` | Sau mỗi khung ở chế độ enroll |
| `enroll_done` | `profile_id`, `profile_status:"PENDING_REVIEW"`, `duplicate_warning` (bool) | Đủ 5 mẫu, đã lưu |
| `error` | `code`, `message` | Lỗi; xem 1.6 |
| `pong` | — | |

**`state`** ∈ `NO_FACE` · `TOO_FAR` (mặt nhỏ hơn `min_face_px`) · `LOOK_STRAIGHT` (`|yaw_ratio|` > `max_abs_yaw_ratio`) · `HOLD_STILL` (đang gom khung, chưa đủ) · `CHECKING` (đã có ≥ 1 khung hợp lệ trong cửa sổ) · `BUSY`. Chữ hiển thị: `ui/tokens/status.json` → `kiosk_state_hint_vi`.

### 1.4 `result`
| `result` | `reason` | `door` | `employee` | `attendance` | Ghi event |
|---|---|---|---|---|---|
| `OK` | — | `OPEN` | có | cửa chấm công: `kind` = `IN` / `OUT`, `time`, `status` (trạng thái ngày công tạm thời); cửa ACCESS_ONLY: `kind:"NONE"` | `MATCH` |
| `ALREADY` | — | `OPEN` | có | `{kind:"NONE", time: thời điểm lượt trước}` | **không** (trong cooldown) |
| `DENY` | `UNKNOWN` | `DENY` | — | — | `UNKNOWN` (+ crop) |
| `DENY` | `SPOOF` | `DENY` | — | — | `SPOOF` (+ crop) |
| `DENY` | `RULE` | `DENY` | có | — | `DENIED_RULE` |
| `DENY` | `INACTIVE` | `DENY` | có | — | `DENIED_INACTIVE` |
`message`: câu tiếng Việt ngắn do Hub soạn (Kiosk có thể dùng thay chữ mặc định ở `ui/man-hinh/kiosk.md`). **Không bao giờ gửi ảnh khuôn mặt về Kiosk.**

### 1.5 Lý do loại mẫu khi đăng ký (`enroll_progress.reason`)
`NO_FACE` "Không thấy khuôn mặt" · `MULTI_FACE` "Có nhiều khuôn mặt trong khung" · `TOO_SMALL` "Khuôn mặt quá nhỏ — lại gần hơn" · `POSE` "Nghiêng quá nhiều — nhìn theo hướng dẫn" · `SPOOF` "Không xác thực được khuôn mặt thật" (chỉ khi bật chống giả mạo) · `TOO_SIMILAR` "Tư thế gần giống mẫu trước — đổi hướng một chút" (cos với mẫu đã nhận > 0,98 **[khởi đầu]**).

### 1.6 Mã lỗi
`TOKEN_INVALID`, `DEVICE_REVOKED` (Kiosk xoá token → K-01) · `AUTH_TIMEOUT` · `BAD_MESSAGE` · `FRAME_DECODE_FAILED` (bỏ khung, Kiosk gửi khung tiếp) · `SESSION_EXPIRED` (enroll, quay về K-02) · `MODEL_NOT_VERIFIED` (Hub chưa qua cổng khởi động — Kiosk hiện K-11 với thông báo "Máy chủ chưa sẵn sàng").

### 1.7 Ví dụ một lượt chấm công
```json
{"type":"frame","seq":101,"mode":"recognize"}              // + JPEG
{"type":"state","seq":101,"state":"CHECKING","bbox":[212,88,190,236],"frames_in_window":1}
{"type":"frame","seq":102,"mode":"recognize"}              // + JPEG
{"type":"state","seq":102,"state":"CHECKING","bbox":[214,90,188,233],"frames_in_window":2}
{"type":"frame","seq":103,"mode":"recognize"}              // + JPEG
{"type":"result","seq":103,"result":"OK","employee":{"name":"Võ Thanh Tùng","code":"NV006"},
 "attendance":{"kind":"IN","time":"2026-11-16T08:27:41+07:00","status":"NORMAL"},"door":"OPEN","message":"Chào buổi sáng"}
```

## 2. `/api/v1/ws/monitor`
- Dùng cho W-02, W-07, W-10. Message đầu bắt buộc: `{"type":"auth","access_token":"…"}`; vai trò OWNER, HR, SECURITY (MANAGER: chỉ event của team).
- Access token hết hạn khi đang mở: Hub gửi `{"type":"error","code":"TOKEN_EXPIRED"}` và đóng 4401 → web làm mới token, nối lại.
- **Hub → web:**
| `type` | Trường |
|---|---|
| `event` | đối tượng `Event` như REST (`openapi.yaml` → `Event`) |
| `alert` | `Event` có `result` ∈ UNKNOWN/SPOOF (gửi thêm một lần dưới dạng `alert` để hiện ở cột cảnh báo) |
| `alert_handled` | `{event_id, handling}` |
| `device_status` | `{device_id, gate_id, online, last_seen_at}` |
| `counters` | `{open_alerts, pending_face_profiles, pending_requests}` — gửi khi đổi |
- Lọc theo phạm vi ở **server**; client không tự lọc dữ liệu nhạy cảm.

## 3. Kiểm thử bắt buộc
- `hub/tests/test_ws_kiosk.py`: auth sai/thiếu/quá hạn; dừng-và-chờ (khung gửi chồng bị bỏ theo `seq`); BUSY; đủ chuỗi tới `result` với `decide()` giả lập; enroll đủ 5 mẫu → `enroll_done`; DEVICE_REVOKED giữa chừng.
- `hub/scripts/kiosk_sim.py`: Kiosk giả lập đọc thư mục ảnh/video, gửi theo giao thức, in ra từng message nhận được (dùng cho T05, T14).
