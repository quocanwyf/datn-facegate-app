# T05 — WebSocket Kiosk, ghép thiết bị, đăng ký khuôn mặt, ghi sự kiện
> Phụ thuộc: T04 · Máy: máy Hy · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T05/bao-cao.md`.

## Mục tiêu
Kiosk (hoặc Kiosk giả lập) ghép được, quét được, đăng ký được; Hub ghi event đúng.

## Đọc trước
`03-app/openapi/ws-protocol.md` · `openapi.yaml` (tag Kiosk, Gates: devices) · đặc tả §5.2–5.4 · skill `kiosk-ws-protocol`, `hub-rules`.

## Được ghi vào
`03-app/hub/` · `03-app/ket-qua-kiem-thu/<ngày>_T05/`.

## Các bước
1. `POST /devices` (mã 6 số băm, hết hạn 10 phút, `qr_payload`), `POST /devices/{id}/revoke`, `POST /kiosk/pair` (khóa lượt thử theo IP 10 phút sau 5 lần sai, chốt 15/11/2026; giữ request mã 6 số), device token 30 ngày (băm trong DB).
2. `GET /kiosk/enrollers`, `POST /kiosk/enroll/sessions` (PIN cá nhân, khoá 15 phút sau 5 lần sai), `GET …/employees`, `POST …/consent`.
3. `ws_kiosk.py` đúng ws-protocol: auth, `config`, dừng-và-chờ theo `seq`, `BUSY`, ping/pong, mã lỗi.
4. Chế độ `recognize`: khung → worker → `DeviceSession` → kết luận → `biz/access.py` (status NV, `default_policy`, phòng ban được phép) → ghi `recognition_event` (MATCH/UNKNOWN/SPOOF/DENIED_*), crop cho UNKNOWN/SPOOF, cooldown → `result`. Trường `attendance` để `{kind:"NONE"}` cho tới T09 (T09 nối `recompute_day`).
5. Chế độ `enroll`: nhận 5 mẫu hợp lệ (lý do loại theo ws-protocol §1.5), lưu PNG 112×112 RGB, embedding + template, kiểm trùng ở mức STRICT_TEST → `face_profile` `PENDING_REVIEW` (chỉ thay PENDING cũ sau đủ 5 mẫu và lưu thành công) → `enroll_done`.
6. `scripts/kiosk_sim.py --hub http://localhost:8000 --pair-code 123456 --images <thư mục>`: ghép, gửi khung, in message.
7. `tests/test_ws_kiosk.py` (các ca trong ws-protocol §3).

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | `test_ws_kiosk.py` pass |
| 2 | Chạy `kiosk_sim.py` với ảnh của Hy: đăng ký 5 mẫu → hồ sơ PENDING; duyệt tay trong DB (tạm, tới T06 có API) → quét lại ra `OK`; ảnh người khác ra `DENY/UNKNOWN` — dán log message |
| 3 | `recognition_event` có đủ `model_id`, `top1_score`, `threshold_used`, `threshold_level`, `n_frames`; MATCH không có `snapshot_path` |
| 4 | Không có ảnh khuôn mặt nào trong message gửi về Kiosk (test kiểm) |

## Điều kiện dừng
Giao thức trong ws-protocol không đủ để cài một hành vi → dừng, ghi câu hỏi.

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Test NO_GALLERY không event; MODEL_NOT_VERIFIED/RECOGNITION_UNAVAILABLE ngừng nhận dạng, error frame có seq. Enroll chụp lại giữ bản PENDING cũ tới đủ5/lưu thành công, giữ ACTIVE cũ tới duyệt; agree=false xóa/NULL consent/MANUAL. SUSPENDED trả DENY/INACTIVE không mở cửa/công.
