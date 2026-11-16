# T13/T14 — rà soát bảo mật thay đổi

Theo skill differential-review (methodology/adversarial/reporting), baseline **4aceb59**, ngày 16/11/2026. Đây là rà soát tập trung do cùng Codex thực hiện, không phải audit độc lập/chứng nhận toàn hệ thống.

## Kết luận

| Mức | Chưa sửa, đã xác nhận trong phạm vi | Đã sửa trong đợt này |
|---|---|---|
| Critical | 0 | 0 |
| High | 0 | 0 |
| Medium | 0 | 3 |

**Khuyến nghị: CONDITIONAL cho demo nghiên cứu.** Mã tích hợp được kiểm và các đường ghi được bảo vệ; triển khai PAD/GPU vẫn cần dữ liệu T13, người dùng chốt L, video kiosk thật và cổng CUDA. Không suy ra “không có lỗi” ngoài phạm vi đã đọc.

## Phạm vi / baseline / blast radius

- Đọc toàn bộ 8 file app thay đổi/mới: api/settings; biz/access, enrollment, kiosk_service, recognition_policy; recog/runtime, liveness, performance; các caller/phụ thuộc một bước (device auth, enroll sessions, quyết định, file riêng, model loader/gallery, quyền Owner, error/contract).
- Đọc script thu dữ liệu/hiệu chỉnh/phê duyệt/benchmark/demo/static server và form cấu hình web. 55 file Python app được kiểm kê AST; không tuyên bố đọc sâu toàn bộ 55 file.
- Lịch sử nền: `ed90ab6` worker/đăng ký, `12d8581` khóa quyền/consent và barrier T06, `5b8b7af` giám sát sau commit. Giữ khóa Device→Gate→Employee và barrier thu hồi; thêm Company FOR SHARE trước các khóa đó, không loại bỏ kiểm consent/actor/quyền.
- [security-calls.json](security-calls.json): require_approval 3 call site app; lock_recognition_policy 2; live_score 2; record_decision 1; persist_enrollment 1; verify_bundle 2; FrameTiming 1. Đây là tham chiếu cú pháp, không phải số lần thực thi/coverage.
- [security-routes.json](security-routes.json): current_user 68 route references; settings vẫn OWNER, không thêm REST operation/quyền công khai. Không đổi token/JWT/secret hoặc mở tường lửa.

## Phát hiện và khắc phục

### M-01 — Kết quả suy luận cũ sau khi bật PAD

Kiosk hợp lệ gửi ảnh khi cờ tắt; OWNER bật PAD trong lúc worker đang xử lý; điểm quyết định cũ không có p_live vẫn có thể đến record_decision sau khi PUT đã xong. Điểm ghi trước đây chỉ kiểm lại Device/Gate/Employee, chưa kiểm snapshot settings. Khai thác cần thiết bị hợp lệ và trúng thời điểm đổi cấu hình; nguy cơ chấp nhận một lượt theo policy cũ.

Sửa: `biz/recognition_policy.py:9` giữ **Company FOR SHARE** tới commit, so snapshot policy/L/cờ. `access.py:18` và `enrollment.py:25` gọi trước khóa khác/ghi profile. Nếu settings đã đổi, 503 yêu cầu quét lại; nếu event đang commit thì PUT phải chờ nên không báo policy mới có hiệu lực sớm. Luồng service rollback cooldown nếu ghi event thất bại vẫn giữ nguyên.

Kiểm: PostgreSQL test bật bằng marker fixture, snapshot cũ bị chặn/snapshot hiện tại được nhận; cập nhật cấu hình không hợp lệ không đổi một phần. Đã chạy WS/DB thật CPU smoke sau thêm commit guard. Chưa vét cạn mọi interleave của PostgreSQL/file/restart.

### M-02 — Trộn mẫu đăng ký giữa hai policy

Nếu đã gom 4 mẫu lúc tắt PAD, bật PAD rồi chỉ mẫu thứ 5 được kiểm có thể tạo bộ 5 gồm mẫu cũ chưa kiểm. Sửa `runtime.py` lưu chữ ký policy theo phiên/nhân viên; đổi policy thì bỏ bộ gom cũ, thu lại đủ 5. Mẫu nonlive không vào cache/vector; profile chỉ commit khi snapshot vẫn hiện hành.

Kiểm: regression gài 4 mẫu cũ chưa có p_live, đổi policy và cho nonlive; kết quả accepted=0/SPOOF, không embed/lưu mẫu. Đây là fixture điều khiển, không dùng để báo tỷ lệ chống giả mạo.

### M-03 — Kiểm kích thước sau khi đã cấp phát ảnh JPEG

Đường cũ gọi OpenCV giải mã đầy đủ rồi mới so frame_long_side. Thiết bị hợp lệ có thể gửi JPEG nén nhỏ nhưng kích thước pixel vượt cấu hình, gây áp lực RAM trước khi bị loại. Sửa `runtime.py` đọc header bằng Pillow trước OpenCV, chỉ nhận JPEG/kích thước trong policy; giữ giới hạn byte WS hiện có. Không giải mã pixel trong bước đọc header.

Kiểm: JPEG tổng hợp 800×800 với cấu hình640 bị BAD_MESSAGE trước khi imdecode được gọi. Không tạo ảnh người hay event cho test này.

## Các biên tin cậy đã kiểm

- Trọng số/mã upstream ghim commit và SHA; Apache LICENSE giữ nguyên; weights_only=True, strict state_dict; không chạy script upstream tùy ý. 33 file T01 tiếp tục so byte với nguồn; silentface có manifest riêng và kiểm không có payload ngoài danh sách (bỏ qua cache Python dẫn xuất).
- Marker phê duyệt ở HUB_DATA_DIR riêng, REST không tạo marker; so L/bundle/policy/số nhóm/thời điểm/người chốt. Marker thiếu/hỏng/khác policy: không bật hoặc không ghi quyết định. Filesystem/CLI admin được tin cậy như .env; marker **không phải chữ ký chống quản trị máy cố tình giả báo cáo**.
- Dataset chỉ ngoài repo, resolve path ngăn vượt root, camera capture cần consent đã ghi và thao tác Space; calibration chặn video trùng/split sai/nhóm thiếu. Report không có ảnh/vector/đường dẫn từng video hoặc danh tính người thử.
- CLI benchmark chỉ clone prefix T13/T14 từ T08 riêng, không áp dụng DB bất kỳ. Token/mật khẩu không ghi log; default lấy kín hoặc dùng demo rõ ràng. Thu hồi thiết bị và cancel các simulation còn lại khi lỗi.
- Static server chỉ serve web/dist đã resolve, chặn traversal/symlink vượt dist và không trả SPA cho /api. Kiểm thực tế: web200, health DBtrue/modeltrue, unauth employees401, unknown API404 trong shared-demo-check.json.
- Timing opt-in chỉ stage/total; không thêm trường WS hay log JPEG/bbox/vector. GPU synchronize và n từng stage được ghi để tránh báo thời gian enqueue hoặc 0 giả cho stage chưa chạy.

## Bằng chứng và giới hạn

Backend: pytest-full.log ở T13; browser OWNER/HR và build/lint; vendor manifest/parity; CPU WS smoke1/3. Chưa có quay 4 nhóm, hiệu quả PAD trên camera cụ thể, 20 lượt kiosk, CUDA, mạng LAN/tường lửa máy khác, stress/fuzz hoặc toàn bộ tổ hợp crash/file rollback. Script hiệu chỉnh/đo 20 lượt mới kiểm syntax và cổng dữ liệu thiếu; đường thành công đầy đủ cần video thật. Những thiếu hụt này là điều kiện nghiệm thu còn lại, không được thay bằng fixture.
