# T13 — Chống giả mạo (MiniFASNet) + hiệu chỉnh ngưỡng L
> Phụ thuộc: T04, T08 · Máy: Hy (tích hợp) + **laptop An** (hiệu chỉnh với người tình nguyện) · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T13/bao-cao.md`.

## Mục tiêu
Bật lớp chống giả mạo thụ động; chọn ngưỡng L bằng bộ thử nội bộ. Đây là **kiểm thử chức năng**, không phải kết quả nghiên cứu.

## Đọc trước
Đặc tả §4.2 bước 4, §4.5, M7 ở §12, §13 mục 3 · skill `hub-rules`.

## Được ghi vào
`03-app/hub/vendor/silentface/` (mô hình + trọng số + **LICENSE Apache-2.0** gốc) · `03-app/hub/app/recog/liveness.py` · `03-app/hub/scripts/` · `03-app/ket-qua-kiem-thu/<ngày>_T13/` (chỉ số liệu tổng hợp, **không** lưu ảnh mặt người tình nguyện vào repo).

## Các bước
1. Lấy mã + trọng số từ repo `minivision-ai/Silent-Face-Anti-Spoofing`; chép LICENSE; ghi commit/ngày vào `vendor/silentface/NGUON.md`.
2. **Đọc mã gốc để xác minh cách crop** (tỉ lệ phóng 2,7 / 4,0 → 80×80) và cách cộng điểm hai mô hình; cài `liveness.score()` theo đúng mã gốc (ghi dòng mã đã đối chiếu).
3. Bộ thử (An tổ chức, người tình nguyện đồng ý, dữ liệu để **ngoài repo**): mỗi người ~20 lượt cho 4 nhóm — mặt thật · ảnh in · ảnh trên màn hình điện thoại · video phát lại.
4. `scripts/calibrate_liveness.py --data …` → phân phối `p_live` từng nhóm, tỉ lệ chặn/cho qua theo các mức L; đề xuất L.
5. An chọn L → `PUT /settings/recognition` (`anti_spoof_enabled=true`, `liveness_threshold=L`).

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | LICENSE + nguồn ghi đủ |
| 2 | Bảng tỉ lệ theo nhóm và theo L (số lượt thật), ghi rõ "kiểm thử chức năng, số người N, điều kiện ánh sáng/thiết bị" |
| 3 | Cờ tắt chống giả mạo vẫn hoạt động (test) |
| 4 | Kiosk hiện đúng DENY/SPOOF (video) |

## Điều kiện dừng
Không xác minh được cách crop trong mã gốc · giấy phép trọng số khác Apache-2.0.

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Chỉ bật sau hiệu chỉnh/chốt L, miền [0,1]; server 422 nếu L thiếu/sai hoặc ngưỡng khung không nguyên1..W; không lưu một phần cấu hình lỗi.
