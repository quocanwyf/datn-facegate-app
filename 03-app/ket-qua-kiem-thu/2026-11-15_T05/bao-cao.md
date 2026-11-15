# Báo cáo T05 — Ghép thiết bị, PIN, WS và đăng ký/nhận dạng thật

- Trạng thái: **XONG phạm vi T05**.
- Commit triển khai: **ed90ab6** (`T05: connect kiosk pairing enrollment and recognition`); baseline thiết kế đã duyệt: 71800ae; nền T04: c110df6.
- Máy: Windows, Python 3.13.13, torch 2.11.0+cpu, OpenCV 4.14.0; websockets 17.4, pillow-heif 1.8.1. CPU, chưa bật chống giả mạo (T13).
- Quyết định mới được người dùng duyệt trong chat 15/11/2026: 5 lần nhập sai khóa lượt thử từ IP đó 10 phút; giữ request mã 6 số, đổi thông báo. Không tăng device.pairing_attempts cho mã đích không biết. Bộ đếm IP ở RAM của một tiến trình Hub, reset khi khởi động lại; PIN có bộ đếm/thời hạn khóa trong DB.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Test WS | 15/15 ca giao thức: auth, timeout, seq trùng/chồng, BUSY, lỗi có seq, 5 bước enroll, thu hồi giữa phiên, không ảnh trả về | ws-tests.log | Đạt |
| 2 | Đăng ký thật → PENDING → duyệt DB → OK; người khác UNKNOWN | U03: đủ 5 mẫu hợp lệ; NV006 là nhãn demo từ seed. Sau duyệt bởi tài khoản HR khác người đăng ký và restart nạp gallery: 1 OK, 2 ALREADY. U04: DENY/UNKNOWN, không có OK/ALREADY | real-run-03/messages.jsonl, summary.json | Đạt |
| 3 | Event có truy vết; MATCH không ảnh | MATCH: model V1 s3, score 0.8180371, threshold 0.42327544 DEFAULT_VAL, n_frames=3, has_snapshot=false. UNKNOWN: n_frames=5, crop=true; top1_score=NULL theo schema vì không có nhóm khung khớp | real-run-03/events.json | Đạt |
| 4 | Không gửi ảnh về Kiosk | Kiểm đệ quy các message của test; lượt thật chỉ config/state/result/enroll_progress/enroll_done, không ảnh/vector/token trả lại | ws-tests.log, real-run-03/messages.jsonl | Đạt |

Bộ hồi quy đầy đủ: **66 passed, 1 skipped, 3 warnings trong 59,44 giây** (`pytest-full.log`). Skip duy nhất là test màu T02 chưa có LFW. REST/PIN/auth riêng 22/22 (`rest-tests.log`); lint OpenAPI **0 lỗi, 4 cảnh báo** (`openapi-lint.log`); kiểm bí mật SẠCH (`secret-check.log`). Không nới ngưỡng hay sửa vendor/research.

## Ca bổ sung và dữ liệu thật

`real-run-03/resilience-summary.json` và `resilience.log`: TOO_SIMILAR không tăng accepted; ngắt sau 4 mẫu giữ PENDING; lỗi ghi file trước thay thế giữ PENDING và 5 sample cũ; bộ mới đủ 5 mới thay PENDING, ACTIVE cũ vẫn giữ; SUSPENDED trả DENY/INACTIVE không OPEN; giả lập lỗi xóa file trên hồ sơ thật trả 503 nhưng consent vẫn NULL/MANUAL và gallery loại nhân viên; thử lại xóa hoàn tất. Không tạo ngày công trước T09.

Ảnh đầu vào do người dùng cung cấp tại D:/WorkSpace/DATN/U03 (17 JPG) và U04 (6 HEIF). Chỉ giải mã/chuyển JPEG trong RAM như đầu vào camera. Ảnh mẫu đã căn chỉnh/crop và DB thử đặt ngoài repo, đường dẫn ghi trong private-inputs.json. Không commit ảnh, vector, token hay checkpoint. Hồ sơ/sự kiện thử tạo từ pipeline thật, không seed giả. DB demo facegate_dev không bị reset hoặc gán ảnh thử.

Lượt đầu `real-run` chưa ra UNKNOWN: giải mã HEIF giữa các lần gửi làm giãn nhịp và reset cửa sổ; giữ nguyên log lỗi. Đã sửa simulator chuẩn bị JPEG trong RAM trước gửi, không thay ảnh/ngưỡng/luật mất mặt. Lượt 02 xác nhận OK/UNKNOWN; lượt 03 bổ sung cooldown: 2 ALREADY nhưng chỉ 1 MATCH + 1 UNKNOWN trong DB. Các bộ ảnh có mẫu POSE bị từ chối vẫn được giữ trong chuỗi gửi và log.

## Đã làm

- Cấp mã ghép 6 số 10 phút; tuần tự hóa cấp mã chống trùng; lưu băm mã/token; token thiết bị 30 ngày, ghép chỉ một lần, thu hồi có hiệu lực với REST/WS.
- Enrollers chỉ id/tên; PIN cá nhân khóa 15 phút sau 5 sai, lưu bộ đếm dù trả lỗi; phiên đăng ký 5 phút gắn thiết bị/người thực hiện, lọc NV ACTIVE và ghi consent mới.
- WS auth bằng message đầu trong 5s, timeout im lặng 15s, JSON header + binary JPEG, seq tăng, bỏ trùng, BUSY khi gửi chồng/hàng đợi đầy. Pipeline chỉ chạy trong thread worker; API await future.
- Enroll giữ mẫu mới trong RAM; chỉ lưu bộ 5 mẫu hợp lệ. File mới được ghi trước thay PENDING cũ; DB rollback/lỗi IO không mất bản cũ. ACTIVE giữ tới khi duyệt. So trùng theo STRICT_TEST từ DB; không gửi ảnh về Kiosk.
- Recognize đọc ngưỡng theo cửa, xét quyền qua cửa theo trạng thái/phòng ban, ghi event có truy vết/crop đúng loại. Cooldown không ghi event trùng; lỗi ghi có bước hoàn lại cooldown. attendance giữ kind=NONE tới T09.
- agree=false thu hồi consent trước thao tác xóa file, xóa cache mẫu đang thu, xóa hồ sơ/mẫu/vector/crop liên kết và reload gallery trước thành công. Lỗi không khôi phục quyền nhận dạng. Gallery phục hồi gửi config cho Kiosk.

## File chính

hub/app/api/{devices,kiosk,ws_kiosk}.py; auth/{device,pairing}.py; biz/{access,enroll_sessions,enrollment,face_data,files,kiosk_service}.py; recog/runtime.py; config/main/errors/session/detector và dependency; scripts/{kiosk_sim,review_t05,review_t05_resilience}.py; tests/{test_pairing,test_kiosk_rest,test_ws_kiosk}.py và điều chỉnh fixture transaction auth.

Các bản thiết kế Q-001–Q-013 đã được người dùng duyệt/sẵn có từ session thiết kế, cùng mô tả khóa IP vừa chốt, được đồng bộ Git để contract/seed/specs và code thống nhất khi pull. Không tự thay yêu cầu khác. Lịch sử dừng ban đầu giữ tại bao-cao-dung-lan-dau.md.

## Đề xuất / giới hạn

Cảnh báo hiện có của vendor skimage/torch và TestClient được ghi nguyên trong log. Không sửa vendor để giấu cảnh báo. T05 chưa có UI Expo hoặc trang duyệt W-08 (T07/T08), monitor/công được nối trong T09/T11. Không archive spec còn AC UI/luồng chưa kiểm; bộ quyết định FG-AI-003 đủ AC sau bằng chứng cooldown thật sẽ được archive kèm commit.

## Cần An làm

Không có bước bắt buộc để tiếp tục T06. T02 vẫn chạy riêng theo RUN-T02.md khi An rảnh. Kịch bản review T05 ở REVIEW-T05.md; không cần chạy lại để Codex tiếp tục.
