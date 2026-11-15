# T04 — Lõi nhận dạng: phát hiện, trích feature, gallery, bộ quyết định, worker
> Phụ thuộc: T01, T03 · Máy: máy Hy (CPU) · Cần checkpoint: có
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T04/bao-cao.md`.

## Mục tiêu
Các khối nhận dạng chạy độc lập, có test; chưa nối WS (T05).

## Đọc trước
Đặc tả §4.2–4.6 · skill `hub-rules` · `03-app/db/thiet-ke-db.md` (face_*, recognition_model, threshold_profile).

## Được ghi vào
`03-app/hub/app/recog/` · `03-app/hub/tests/` · `03-app/ket-qua-kiem-thu/<ngày>_T04/`.

## Các bước
1. `detector.py`: bọc `YuNetDetector` (score 0,6), chọn mặt lớn nhất, tính `yaw_ratio`, kiểm `min_face_px`, `max_abs_yaw_ratio` → trả `FrameObs(valid, reason, bbox, landmarks, det_score, yaw_ratio)`.
2. `embedder.py`: đúng đường trích trong skill `hub-rules` (một hàm `embed(img_bgr, landmarks) -> np.ndarray[512]`).
3. `liveness.py`: giao diện `score(img_bgr, bbox) -> float | None`; bản này trả `None` (chống giả mạo làm ở T13); bộ quyết định coi `None` = live.
4. `gallery.py`: nạp template (NV ACTIVE/SUSPENDED ∧ FACE ∧ có consent ∧ hồ sơ ACTIVE) thành ma trận `N×512` (CUDA nếu có, không thì CPU); `top1(emb) -> (employee_id, score)`; `reload()` an toàn luồng.
5. `decision.py`: hàm thuần `decide(window, params)` + `DeviceSession` (cửa sổ, mất mặt, IoU, cooldown) theo skill `hub-rules`.
6. `worker.py`: một thread + hàng đợi; API `submit(kind, payload) -> Future`; giới hạn 2 việc chờ/thiết bị.
7. Test: `test_decision_exhaustive.py` (vét cạn chuỗi 1–8 khung trên {INVALID, NL, LA, LB, LN} + mất mặt + IoU; so với cài đặt tham chiếu viết riêng trong test; kiểm ưu tiên SPOOF > MATCH > UNKNOWN, giá trị đúng bằng ngưỡng dùng `≥`, INVALID không đổi cửa sổ, cửa sổ rỗng sau kết luận); `test_worker.py` (không chặn event loop: đo độ trễ một endpoint giả trong lúc worker bận); `test_embed_smoke.py` (nếu có thư mục ảnh thử `TEST_FACES_DIR` — ảnh của chính Hy/An tự chụp, **không commit**; không có thì skip).

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | `test_decision_exhaustive.py` pass (ghi số chuỗi đã kiểm) |
| 2 | `test_worker.py` pass: độ trễ endpoint giả khi worker bận < 50 ms **[khởi đầu]** (ghi số đo) |
| 3 | Embedding cùng ảnh qua `embedder.embed` = gọi thẳng `extract_features` (max |Δ| ≤ 1e-6 trên CPU) |
| 4 | Gallery nạp được từ DB (kể cả rỗng) |

## Điều kiện dừng
Phải đổi tiền xử lý / ngưỡng / luật quyết định so với đặc tả mới qua được test → dừng, báo.

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Gallery định danh ACTIVE/SUSPENDED đủ FACE/consent/profile/template; chỉ ACTIVE xét cho qua. Gallery rỗng trả NO_GALLERY không UNKNOWN; reload lỗi tạm ngưng. Giữ dữ liệu gallery nhất quán trước thành công.
