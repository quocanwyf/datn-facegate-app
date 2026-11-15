# Rà soát bảo mật T06 — auth, RBAC, device token

## Kết luận trong phạm vi rà soát

| Mức | Phát hiện | Đã sửa | Còn mở có bằng chứng |
|---|---:|---:|---:|
| HIGH | 1 | 1 | 0 |
| MEDIUM | 1 | 1 | 0 |

Kết luận: các finding cụ thể bên dưới đã được sửa và kiểm hồi quy. Đây là rà soát có trọng tâm, không phải chứng nhận không còn lỗ hổng cho toàn bộ dự án.

Khuyến nghị: **APPROVE phạm vi T06** theo các kiểm thử đã ghi; rủi ro nghiệp vụ của phạm vi vẫn MEDIUM vì có quyền và xóa sinh trắc. Không mở rộng kết luận sang các task chưa triển khai.

Skill dùng: [differential-review của Trail of Bits](https://github.com/trailofbits/skills/tree/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/differential-review/skills/differential-review), bản ghim 149d7b21f4067765b82e67029730b42d228ef4b4, CC-BY-SA-4.0. Đã đọc SKILL.md, methodology.md, adversarial.md, reporting.md. Skill được cài bằng skill-installer; nguồn/license giữ trong .agents/skills/differential-review.

## Baseline, trust boundary và phạm vi

- Baseline: ab712c9 (T05). Auth/RBAC gốc từ ce1e5f1, Kiosk từ ed90ab6; git log/blame tại `security-history.log`.
- Nhánh tin cậy: JWT người dùng → đọc lại tài khoản/vai trò DB; device token → thiết bị ACTIVE/còn hạn/cửa được gán; PIN → người đăng ký OWNER/HR; dữ liệu đầu vào API luôn chưa tin cậy.
- Bất biến: HR không sửa/cấp OWNER; MANAGER không thoát team; ảnh chỉ OWNER/HR; sau rút consent/khóa/đổi chính sách đã hoàn tất không được mở cửa bằng quyền cũ; reload khác không hoàn tất hộ thao tác sinh trắc chưa xong.
- Kiểm kê 44 module app, chiến lược MEDIUM/FOCUSED. Người rà soát phụ đọc khoảng 23 module liên quan và lịch sử; agent chính đọc phần triển khai/đầu vào/client/đối chiếu specs. Không đọc lại toàn bộ vendor mô hình.
- `security-callers.json` ghi caller AST và dependency FastAPI theo route: 39 route tham chiếu current_user. Đây là số tham chiếu tĩnh, không phải tỷ lệ bao phủ dòng/chạy động. Gồm auth/dependencies, security, device/pairing, api quản trị và pipeline ghi event/xóa sinh trắc.

## HIGH — quyết định dùng quyền đã thay đổi trong lúc ghi event

Vị trí baseline: `hub/app/biz/access.py` ed90ab6, trước đây đọc Device/Gate/Employee bằng session.get không khóa.

Kịch bản: MATCH đã đọc nhân viên ACTIVE/consent và gate policy; trong lúc await tiếp theo, một request suspend/rút consent/đổi chính sách commit, trả thành công; MATCH tiếp tục với object cũ và ghi OPEN. gate_locks của Kiosk không bảo vệ các API quản trị.

Đã sửa: giữ khóa PostgreSQL **FOR NO KEY UPDATE** theo thứ tự Device → Gate → Employee từ kiểm quyền đến commit event. Khóa tương thích FK KEY SHARE nhưng xung đột với các writer quyền/trạng thái; kiểm cả hạn device token. `permission-locks.log` ghi SQL compile thật. Không có cửa sổ thành công thu hồi trước rồi mới commit OPEN từ snapshot cũ.

Hồi quy thực thi: `scripts/review_t06.py` dùng frame ảnh thật qua detector/backbone/bộ quyết định, giữ ngay trước INSERT bằng advisory lock. Request suspend đồng thời phải chờ khóa DB; chỉ hoàn tất sau event commit. `real-run-02/summary.json` và `real-run-03/summary.json`: `concurrent_suspend_waits_for_real_match_commit=true`. Không tạo event giả để kiểm ca này.

## MEDIUM — reload giải phóng pause của thao tác khác

Vị trí: `api/faces.py` và `recog/runtime.py`. Event pause dùng chung không có chủ sở hữu; reload khác có thể clear trong khi approval còn cleanup. Bản sửa đầu theo employee vẫn có lỗi cùng nhân viên: suspend ghi đè token của approval.

Đã sửa: `recog/mutations.py` quản lý generation và pending token dưới cùng Lock với Event. Key phân biệt `employee/<id>/review/<profile>/approve|reject`, `.../status`, `.../delete`. Reload chỉ hoàn tất token khớp snapshot; reload không liên quan hoặc snapshot cũ không được clear pause. Xóa toàn bộ chỉ giải phóng các token đã chụp của đúng nhân viên **sau** xóa file/DB và reload thành công; không xóa token mới hơn hoặc người khác.

Hồi quy: 5 test tại `tests/test_mutation_barrier.py` bao gồm snapshot cũ, failed cleanup, cùng nhân viên approval+suspend, ownership retry và phạm vi full-delete. Log riêng `mutation-barrier-tests.log`, đồng thời nằm trong pytest cuối. Rà lại độc lập đã xác nhận sửa đúng hai finding, không thấy gap cụ thể mới trong phạm vi đó.

## Quyền và bảo vệ đã đối chiếu

- JWT giới hạn HS256, kiểm type access/refresh, thời hạn, trạng thái DB; refresh băm và xoay vòng có khóa; đổi/reset mật khẩu thu hồi refresh.
- HR bị chặn mọi thao tác lên tài khoản OWNER/cấp OWNER. Quyền/role scope kiểm từ DB, scope MANAGER bắt buộc đúng phòng ban/công ty.
- DTO lấy từ OpenAPI, update whitelist; không mass-assign company/status/consent từ payload nhân viên. Dữ liệu NaN/Infinity bị chặn. Không echo input bí mật vào lỗi.
- Device token chỉ lưu hash; ghép một lần, hết hạn 30 ngày/thu hồi có hiệu lực; khóa sai mã theo IP đã được người dùng chốt, không tin X-Forwarded-For trong app LAN.
- Sau inference, finalize enrollment kiểm lại người đăng ký ACTIVE/còn OWNER/HR, thiết bị ACTIVE và consent/version. File ảnh theo UUID trong HUB_DATA_DIR, path resolve không thoát root; response Kiosk không có ảnh/vector.
- Rút/xóa commit consent NULL/MANUAL trước IO; lỗi không khôi phục quyền nhận dạng, có retry/503; nạp gallery trước báo thành công.

## Kiểm thử và giới hạn

Log quyền: `admin-tests.log`, `pytest-full.log`; ảnh thật/file/galleries: `real-review-03.log`, `real-run-03/summary.json`; sinh client/tsc: web/kiosk-*.log. Có 50 ca đọc theo 5 nhóm vai trò, ghi OWNER/HR, chặn HR sửa field cửa của OWNER, scope MANAGER, thu hồi refresh, duyệt đồng thời 200/409 và xóa lỗi/retry.

Chưa rà API chấm công/giám sát còn để T09/T11 hoặc UI/native SecureStore chưa triển khai. Race row-lock đã tái hiện với suspend; gate/device dựa cùng khóa được kiểm SQL và đọc mã, chưa có bài thử đồng thời riêng cho từng writer. Không tuyên bố đã thử mọi điểm crash/cancel hoặc mọi lịch interleave file+DB. HTTP LAN, một công ty và không TLS/rate-limit phức tạp là phạm vi demo đã duyệt, không ghi thành finding yêu cầu thêm tính năng.
