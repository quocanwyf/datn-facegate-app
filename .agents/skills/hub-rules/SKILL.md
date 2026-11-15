---
name: hub-rules
description: Luật bắt buộc khi viết hoặc sửa code Hub (03-app/hub) — nạp mô hình, trích feature, worker suy luận, bộ quyết định, sự kiện chỉ thêm, dữ liệu khuôn mặt. Dùng mỗi khi động vào app/recog, app/biz, app/db, vendor hoặc scripts parity. Không dùng cho code web/kiosk.
---

# hub-rules

## Nạp mô hình (đặc tả §4.1) — cổng 4 bước, sai là dừng khởi tạo nhận dạng, giữ health chẩn đoán
1. `sha256(best.pt)` == `sha256` của dòng `r18_uniface_v1_lam0.6_m0.45_s3_e28:best` trong `vendor/manifest/manifest_24.json` (`120489621a…ef88`).
2. `vendor/manifest/strip_map_ban_sao.json` có bản ghi `source_sha256` = hash bước 1 và `dest_sha256` = `meta.sha256` của cùng khoá trong `02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json` (`b00612f5…a065`).
3. `evaltest.features.load_backbone(path, device, row=<dòng manifest>, expected_sha=<hash bước 1>)` — chạy `verify_checkpoint` (fingerprint, head, epoch 18, best val).
4. `meta["t_eq30"]` khớp `meta.t_eq30` trong `ket_qua_blufr_lfw.json` (|Δ| ≤ 1e-6).
Trước khi import: `os.environ["DATN_CODE_DIR"] = <hub>/vendor/code`. Không bao giờ trích lại backbone rồi so byte lúc khởi động.

## Trích feature — một đường duy nhất
```python
warped_bgr, _ = norm_crop(img_bgr, landmarks)          # fr.align.template, trả tuple
rgb = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
x = torch.from_numpy(np.ascontiguousarray(rgb))[None]   # uint8 (1,3,112,112)
emb = extract_features(backbone, x, device)             # evaltest.features: flip-cộng, L2, fp16 khi CUDA
```
Không tự chuẩn hoá ảnh, không tự lật, không đổi kích thước khác 112.

## Phát hiện mặt
`YuNetDetector(score_threshold=0.6).detect(img_bgr)` → chọn **bbox lớn nhất** (không dùng `FaceAligner`, không dùng `pick_center_face` ngoài script parity).

## Worker suy luận
Một thread + `queue.Queue`; mỗi việc là (kind, payload, future). Endpoint/WS chỉ `await asyncio.wrap_future(...)`. Tối đa 2 khung chờ mỗi thiết bị, quá thì trả `BUSY`.

## Bộ quyết định (đặc tả §4.5) — hàm thuần `decide(window, params) -> Decision`
- Khung hợp lệ mới vào cửa sổ (tối đa W=5); khung không hợp lệ không vào; không có khung hợp lệ > `lost_face_sec` → xoá cửa sổ; IoU bbox với khung trước < `iou_reset` → xoá rồi thêm.
- `live = p_live >= L` (tắt chống giả mạo → `live = True`); `match = s >= tau` (**dùng ≥**).
- Thứ tự: SPOOF (≥ `spoof_min` khung không live) → MATCH (một id có ≥ `match_min` khung live∧match) → UNKNOWN (đủ W khung, ≥ `unknown_min` khung live∧¬match, không id nào ≥ 2 phiếu).
- Sau kết luận: xoá cửa sổ. Test vét cạn: `tests/test_decision_exhaustive.py` (chuỗi 1–8 khung trên {INVALID, NL, LA, LB, LN} + mất mặt + IoU).

## Dữ liệu
- `recognition_event` chỉ INSERT; cảnh báo xử lý ở `event_handling`; xoá dữ liệu khuôn mặt chỉ được đặt `snapshot_path = NULL`.
- Xoá dữ liệu khuôn mặt (nghỉ việc / bấm xoá / rút đồng ý): xoá file ảnh mẫu + `face_profile` (cascade sample/embedding/template) + file crop của event có `event_handling.linked_employee_id` = NV (đặt `snapshot_path` NULL) + ghi `biometric_deleted_at` + nạp lại gallery + audit.
- Gallery định danh = NV `ACTIVE` hoặc `SUSPENDED` ∧ `FACE` ∧ có `face_consent_at` ∧ hồ sơ `ACTIVE`; nạp lại **trước khi** API trả thành công.
- Ngưỡng đọc từ `threshold_profile` theo `gate.threshold_level` (hoặc `custom_threshold`), ghi vào event `threshold_used`, `threshold_level`.

## Không được
Sửa `vendor/` hoặc `02-thuc-nghiem/`; ghi số không có log; lưu khung hình đầy đủ; trả ảnh khuôn mặt cho Kiosk.

## Quyết định đồng bộ Q-002/Q-004–Q-008
Chỉ báo thành công sau mọi bước bắt buộc. Đăng ký lại lỗi giữ bản cũ; rút/xóa phải ngừng dùng dữ liệu đó để nhận dạng, xóa file lỗi thì báo chưa hoàn tất và cho thử lại, không khôi phục consent/quyền nhận dạng. Gallery cập nhật lỗi thì tạm ngưng nhận dạng đến khi phục hồi. Duyệt đồng thời cùng hồ sơ chỉ một lần có hiệu lực, lần sau báo “Hồ sơ đã được xử lý”. Gallery không có hồ sơ đủ điều kiện: hiện “Chưa có dữ liệu khuôn mặt”, không tạo UNKNOWN/cảnh báo người lạ. Không giả định giao dịch file+DB nguyên tử.
- SUSPENDED đủ điều kiện vẫn nhận ra nhưng DENIED_INACTIVE, không mở cửa/công; TERMINATED/MANUAL/rút consent không gallery.
- Rút/từ chối/xóa hành chính: NULL consent_at/by, MANUAL và xóa ACTIVE/PENDING; giữ event/công.
- Giữ PENDING cũ tới khi 5 mẫu mới lưu thành công; ACTIVE cũ tới duyệt mới.
- Xét vai trò **người gửi** theo nhánh đầu tiên phù hợp: (1) có OWNER, kể cả kiêm HR → HR khác; (2) HR không OWNER → OWNER khác; (3) MANAGER chính phòng mình, không OWNER/HR → HR khác; (4) còn lại → MANAGER đúng phòng ban người gửi, khác người gửi. MANAGER chỉ quản lý phòng khác thuộc nhánh (4). Không có người duyệt hợp lệ thì giữ PENDING, hiện cần bố trí người duyệt. Server luôn chặn tự duyệt; thứ tự chỉ dùng chọn nhóm duyệt, không loại bỏ quyền khác của tài khoản.
- Model chưa xác minh giữ health degraded/model_verified=false; không chạy nhận dạng. Q-007 kiểm cấu hình W dương/ngưỡng 1..W, L [0,1] và chỉ bật sau T13.
