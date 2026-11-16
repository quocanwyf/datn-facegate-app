# Các quyết định đã chốt — Q-001 đến Q-013

Ngày 14/11/2026, người dùng đã xác nhận review và duyệt toàn bộ 32 specs; xem [lịch sử duyệt](LICH-SU-DUYET.md#approved-2026-11-14). Sau đó người dùng đã chốt đủ **13/13 quyết định Q-001 đến Q-013** như dưới đây.

Mỗi mục giữ căn cứ câu hỏi ban đầu và quyết định người dùng đã xác nhận trong chat. Các câu hỏi này đã được chốt ở cấp specs; nguồn chuẩn đã được đồng bộ ngày 14/11/2026 theo yêu cầu tiếp theo của người dùng. Các đoạn căn cứ trước quyết định được giữ để tra lịch sử; trạng thái đồng bộ hiện tại xem mục cuối. Chưa triển khai hoặc nghiệm thu app.

Các nội dung cũ đã được §0a giải quyết (bỏ TLS, consent version, log đọc ảnh, retention, refresh device token, so sánh model, xác nhận xóa 2 bước) đã áp dụng §0a, không coi là câu hỏi mới.

## Q-001 — Quyền API khác ma trận nghiệp vụ

- Căn cứ: §6 cho MANAGER đọc bảng công/xuất Excel, HR đọc cấu hình, và OWNER/HR ghi chính sách cửa. OpenAPI export chỉ OWNER/HR, settings chỉ OWNER, ghi gates chỉ OWNER.
- Ảnh hưởng: FG-GATE-001, FG-AI-004, FG-ATT-005.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok); trả lời “1. có; 2. có; 3. có” cho ba câu hỏi phân quyền.
- Quyết định 1: MANAGER được xuất Excel bảng công của team thuộc phạm vi phòng ban mình quản lý; server giới hạn phạm vi, không xuất ngoài team.
- Quyết định 2: HR được xem cấu hình nhận dạng; quyền sửa cấu hình nhận dạng vẫn chỉ OWNER.
- Quyết định 3: HR được sửa chính sách ra vào của cửa, gồm chính sách cho phép và danh sách phòng ban được phép. Quyết định này không cấp thêm quyền tạo cửa, đổi chế độ cửa, đổi ngưỡng hoặc quản trị thiết bị.
- Cần đồng bộ: `GET /attendance/export` thêm MANAGER và kiểm team; `GET /settings/recognition` thêm HR; thao tác sửa chính sách cửa/danh sách phòng ban cho HR và giới hạn các trường ngoài phạm vi trên. UI W-07/W-09/W-14 cần thể hiện tương ứng.
- Specs đã cập nhật. Bảng x-roles gốc và ma trận API vẫn phản ánh OpenAPI hiện tại, chưa tự sửa nguồn chuẩn/code trong bước ghi nhận quyết định này.

## Q-002 — Nhân viên SUSPENDED và gallery

- §4.6/DB §5 loại SUSPENDED khỏi gallery, nhưng §5.1/5.4 và WS yêu cầu nhận ra để trả DENIED_INACTIVE.
- Ảnh hưởng: FG-EMP-001, FG-FACE-003, FG-ACCESS-001.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “chọn 1”.
- Quyết định: nhân viên `SUSPENDED` có dữ liệu khuôn mặt hợp lệ vẫn được nhận ra danh tính. Khi nhận ra phải trả `DENY/INACTIVE`, hiển thị “Tài khoản đang tạm khoá”, ghi `DENIED_INACTIVE`, không mở cửa và không tính công.
- Giữ dữ liệu khuôn mặt khi tạm khóa. Điều kiện FACE, consent có hiệu lực, profile ACTIVE và template đúng model vẫn áp dụng. Quyết định không cho phép nhận dạng người đã xóa sinh trắc/rút đồng ý hoặc `TERMINATED`.
- Cần đồng bộ: quy tắc gallery tại đặc tả §4.6, thiết kế DB §5 và logic chuyển trạng thái nhân viên để hỗ trợ định danh SUSPENDED nhưng tách khỏi quyền được phép qua cửa. Không tự chốt dùng gallery chung hay gallery phụ trong bước ghi nhận này.
- Specs FG-EMP-001, FG-FACE-003, FG-ACCESS-001 đã cập nhật theo quyết định; chưa sửa nguồn chuẩn hoặc triển khai code.

## Q-003 — Mốc xác định Kiosk offline

- Kiosk UI nói mất WS >3 giây vào K-11; WS §1.1 dùng không nhận gì 15 giây, ping mỗi 10 giây.
- Ảnh hưởng: FG-KIOSK-001.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với đề xuất ba mốc kết nối.
- Kết nối đã bị ngắt rõ ràng: nếu sau 3 giây vẫn chưa nối lại thì hiện K-11; nối lại trước mốc này thì không cần hiện K-11 vì lần ngắt đó.
- Kết nối còn mở nhưng không nhận phản hồi/message từ Hub: sau 15 giây kể từ lần nhận cuối thì coi là mất kết nối và hiện K-11, không cộng thêm 3 giây chờ.
- Tự thử nối lại với khoảng chờ 1 → 2 → 4 → 8 → 15 giây, các lần sau tối đa 15 giây giữa hai lần thử. Ping mỗi 10 giây khi không gửi khung vẫn theo WS.
- Cần đồng bộ diễn giải điều hướng K-11 trong UI và WS để phân biệt disconnect với timeout im lặng. Không sửa các quy tắc token bị thu hồi hoặc hủy enrollment dở đã có.
- FG-KIOSK-001 đã cập nhật theo xác nhận, giữ APPROVED; chưa sửa nguồn chuẩn/code hoặc chạy nghiệm thu kết nối.

## Q-004 — Thay bản đăng ký đang chờ

- K-06 hỏi thay PENDING; DB chỉ một PENDING/employee. Hợp đồng chưa mô tả đầy đủ thời điểm thay/hủy phiên và mẫu tạm.
- Ảnh hưởng: FG-KIOSK-002, FG-FACE-002.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng í” với phương án đăng ký lại.
- Hỏi xác nhận trước khi đăng ký lại nếu đã có hồ sơ chờ duyệt. Không xác nhận thì giữ hồ sơ chờ cũ, không bắt đầu thay thế.
- Khi đang chụp bộ mới, giữ nguyên bản chờ cũ. Chỉ thay bản chờ cũ khi đủ 5 mẫu hợp lệ và lưu bộ mới thành công; sau thay thế vẫn tối đa một PENDING_REVIEW cho nhân viên.
- Hủy, hết phiên, mất mạng hoặc lưu bộ mới thất bại trước khi hoàn tất thay thế: giữ bản chờ cũ, không để bộ chụp dở trở thành bản chờ thay thế.
- Nếu có hồ sơ ACTIVE trước đó, hồ sơ ấy vẫn hoạt động đến khi bản mới được duyệt, với điều kiện nhân viên vẫn thỏa quyền/consent/trạng thái hiện hành.
- Đồng bộ mô tả K-06/K-08 và luồng enroll WS. Không tự bổ sung endpoint cancel/replace, không lựa chọn cơ chế file/DB; xử lý phục hồi/tranh chấp vẫn thuộc Q-006.
- FG-KIOSK-002 và FG-FACE-002 đã cập nhật, giữ APPROVED; chưa triển khai hoặc nghiệm thu app.

## Q-005 — Consent khi từ chối hoặc xóa

- agree=false đặt MANUAL; revoke xóa sinh trắc. Nguồn chưa quy định đủ hồ sơ cũ/consent_at/by khi agree=false sau từng đăng ký hoặc khi DELETE face hành chính.
- Ảnh hưởng: FG-FACE-001, FG-FACE-004.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với bảng xử lý từ chối/rút đồng ý, xóa hành chính và đăng ký lại.

| Thao tác | Kết quả đã duyệt |
|---|---|
| Không đồng ý (`agree=false`) hoặc rút đồng ý | Xóa dữ liệu khuôn mặt hiện có, kể cả hồ sơ ACTIVE/PENDING; đặt `face_consent_at` và `face_consent_by` cùng NULL; chuyển `attendance_method=MANUAL` |
| OWNER/HR bấm xóa dữ liệu khuôn mặt | Cùng kết quả xóa/rút ở trên; dùng khuôn mặt lại cần đồng ý và đăng ký lại |
| Đồng ý đăng ký lại | Ghi nhận thời điểm/người thực hiện lần đồng ý mới; giữ hồ sơ đang hoạt động đến khi bản mới được duyệt, nếu trạng thái/quyền vẫn hợp lệ |
| Mọi trường hợp xóa | Xóa ảnh mẫu/profile/embedding/template và crop liên kết theo quy tắc đã có; giữ lịch sử công và event, đặt snapshot_path liên quan NULL; ghi biometric_deleted_at/audit |

- Hủy chụp theo Q-004 không tự coi là rút đồng ý. Chọn “Không đồng ý” ở K-07 là hành vi từ chối sử dụng khuôn mặt theo Q-005, nên không giữ hồ sơ cũ để tiếp tục nhận dạng.
- Cần đồng bộ nghiệp vụ consent/xóa trong đặc tả, DB và mô tả API/UI tương ứng; không thêm bảng phiên bản điều khoản hoặc endpoint mới. Xử lý lỗi file/DB và phục hồi còn thuộc Q-006.
- FG-FACE-001 và FG-FACE-004 đã cập nhật, giữ APPROVED; chưa sửa nguồn chuẩn/code và chưa chạy nghiệm thu app.

## Q-006 — Phục hồi lỗi hồ sơ, file và gallery

- Nguồn bắt gallery cập nhật trước API thành công và xóa cả file/DB, nhưng chưa chốt rollback/retry/file tạm/duyệt đồng thời/gallery rỗng.
- Ảnh hưởng: FG-FACE-002/003/004, FG-AI-002, FG-KIOSK-001.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với sáu ý xử lý lỗi.
- Chỉ báo thành công khi các bước bắt buộc đã hoàn tất; lỗi phải báo rõ để thử lại, không báo xong khi dữ liệu/file/gallery còn chưa đạt kết quả yêu cầu.
- Đăng ký lại thất bại giữ bản cũ theo Q-004. Không để bộ thu dở hoặc lưu thất bại thay thế hồ sơ cũ hợp lệ.
- Khi rút đồng ý/xóa: ngừng dùng khuôn mặt đó để nhận dạng. Nếu xóa file lỗi thì báo chưa hoàn tất, cho thử lại; không khôi phục quyền nhận dạng trong thời gian chưa dọn xong. Giữ lịch sử công/event theo Q-005.
- Nếu không cập nhật được danh sách nhận dạng: tạm ngưng nhận dạng đến khi phục hồi, không tiếp tục quyết định bằng dữ liệu gallery chưa cập nhật.
- Hai người duyệt cùng hồ sơ: chỉ xử lý một lần; người còn lại nhận thông báo “Hồ sơ đã được xử lý”, không tạo lần duyệt/thay hồ sơ thứ hai.
- Không có hồ sơ đủ điều kiện để nhận dạng: Kiosk hiện “Chưa có dữ liệu khuôn mặt”, không kết luận UNKNOWN hoặc ghi sự kiện người lạ chỉ vì gallery rỗng. Enrollment vẫn là luồng riêng, không bị coi là UNKNOWN.
- Cần đồng bộ mô tả lỗi/trạng thái trong đặc tả, REST/WS/UI khi cần. Chưa tự đặt mã lỗi/message enum/status HTTP hoặc thêm endpoint; không khẳng định giao dịch file+DB nguyên tử. Cơ chế kỹ thuật phải đáp ứng các hành vi đã duyệt.
- Các specs bị ảnh hưởng đã cập nhật, giữ APPROVED; chưa triển khai hay nghiệm thu app.

## Q-007 — Điều kiện bật liveness và ràng buộc cấu hình

- T13 cần An chọn L sau kiểm thử, UI khóa khi chưa hiệu chỉnh. Cần xác nhận xử lý `anti_spoof_enabled=true` khi L null và quan hệ giữa W với các ngưỡng kết luận.
- Ảnh hưởng: FG-AI-004/005.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với năm ý giới hạn cấu hình.
- Chỉ bật chống giả mạo sau thử nghiệm T13 và chốt L; chưa hiệu chỉnh thì giữ tắt. Không tự đặt L để bỏ qua T13.
- L dùng khi bật phải có giá trị trong [0,1], bao gồm hai biên. Thiếu/sai ngưỡng không được bật. OpenAPI đã mô tả true cần L khác NULL, lỗi 422; cần đồng bộ đầy đủ điều kiện hiệu chỉnh và miền giá trị.
- W là số nguyên dương; match_min, unknown_min, spoof_min là số nguyên từ 1 đến W. Không tự áp thêm quan hệ giữa các tổng ngưỡng ngoài quyết định này; bộ quyết định vẫn dùng thứ tự ưu tiên đã có.
- Giữ mặc định W=5, MATCH=3, UNKNOWN=4, SPOOF=3. Đây vẫn là tham số cấu hình khởi đầu.
- Cấu hình không hợp lệ thì báo lỗi và giữ nguyên toàn bộ cấu hình cũ, không áp dụng một phần; kiểm tra ở server, UI hỗ trợ kiểm sớm.
- Đồng bộ đặc tả/RecognitionSettings/UI và quy tắc vận hành khi cần; không thêm endpoint hoặc tự đặt mã lỗi mới. Specs FG-AI-004/005 đã cập nhật, chưa triển khai/nghiệm thu app.

## Q-008 — Readiness và ví dụ trạng thái WS

- Cổng model sai làm Hub dừng nhưng UI/WS dự kiến health/MODEL_NOT_VERIFIED. WS §1.7 minh họa NORMAL ngay lúc vào, trong khi §5.5 nói IN_PROGRESS trước chốt.
- Ảnh hưởng: FG-AI-001, FG-SYS-001, FG-ATT-002.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với bốn ý đề xuất.
- Mô hình chưa xác minh thì không nhận dạng, không mở cửa hoặc ghi công bằng khuôn mặt; không nới bất kỳ bước kiểm model nào.
- Giữ API kiểm tra trạng thái để báo rõ lỗi. Tách việc API kiểm tra còn chạy khỏi nhận dạng sẵn sàng; khi model chưa xác minh không trả trạng thái ready. Kiosk hiện “Máy chủ chưa sẵn sàng”. Không tự mở rộng quyết định thành bảo đảm mọi API quản trị vẫn hoạt động khi DB/Hub lỗi.
- Ngày làm việc thông thường đã quét vào nhưng chưa chốt công: hiển thị “Đang làm việc — tạm thời” (`IN_PROGRESS`). Giữ ưu tiên HOLIDAY/LEAVE/OFF theo nghiệp vụ.
- Kết luận NORMAL/LATE/EARLY/LATE_EARLY khi chốt theo quy tắc tính công; sửa ví dụ WS §1.7 ghi NORMAL ngay lúc vào. Quyết định không tự sửa dữ liệu công hoặc ví dụ nguồn trong bước ghi nhận này.
- Cần đồng bộ đặc tả cổng khởi động (dừng phần nhận dạng khi model sai nhưng giữ kiểm tra trạng thái), Health/WS/UI và ví dụ minh họa. Dùng trường trạng thái hiện có khi phù hợp, không tự thêm endpoint/enum/mã lỗi.
- FG-AI-001, FG-SYS-001, FG-ATT-002 đã cập nhật theo xác nhận, giữ APPROVED; chưa triển khai hoặc nghiệm thu app.

## Q-009 — Các ca tính công chưa đầy đủ

- §5.5 chưa gán rõ trạng thái đã tới giờ, chưa vào, chưa chốt; chưa đầy đủ cách giữ sửa tay/LEAVE qua recompute và event đến sau chốt.
- Ảnh hưởng: FG-ATT-002/003.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với sáu ý đề xuất.
- Chưa tới giờ ca và chưa quét: hiển thị “Chưa bắt đầu”. Đã tới giờ nhưng chưa quét, chưa chốt: hiển thị “Chưa đến — tạm thời”, chưa kết luận vắng. Áp dụng cho ngày có ca thông thường, giữ ưu tiên lễ/nghỉ/không ca.
- Đến thời điểm chốt vẫn không có giờ vào: `ABSENT` — Vắng, trừ các trạng thái ưu tiên khác theo luật nghiệp vụ.
- Giờ công đã sửa thủ công hoặc đã đánh dấu nghỉ LEAVE được giữ khi hệ thống tự tính lại. Tính lại tự động không được ghi đè kết quả sửa hợp lệ hoặc bỏ trạng thái nghỉ đã đánh dấu.
- Sự kiện được nhận muộn nhưng thời điểm xảy ra thuộc cửa sổ ca vẫn tham gia tính lại ngày công, kể cả ngày đã chốt; giữ `finalized=true` nếu đã chốt. Phân biệt thời điểm xảy ra và thời điểm nhận; không tạo cơ chế Kiosk lưu/gửi bù offline ngoài phạm vi.
- Sự kiện xảy ra ngoài cửa sổ ca chỉ tính ra vào, không tính công. Giữ event gốc, không sửa thời điểm để ép vào ca.
- Cần đồng bộ đặc tả/API/DB/UI về cách biểu diễn “Chưa đến — tạm thời”, bảo toàn sửa tay/LEAVE và sự kiện đến muộn. Chưa tự thêm enum DB/HTTP hoặc đổi nghĩa NOT_STARTED/ABSENT trong hợp đồng gốc.
- FG-ATT-002 và FG-ATT-003 đã cập nhật, giữ APPROVED; chưa triển khai/nghiệm thu app.

## Q-010 — Công thức phút và tổng ngày công

- Nguồn nói trừ nghỉ trưa cố định nhưng chưa chốt làm tròn, phút từ grace hay giờ ca, ca không đủ nghỉ; skill cộng ngày có giải trình cần tránh đếm hai lần.
- Ảnh hưởng: FG-ATT-002/005.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với sáu ý công thức và ví dụ.
- Trong khoảng grace thì phút muộn/sớm bằng 0. Vượt grace: phút muộn tính từ giờ bắt đầu ca, phút về sớm tính từ giờ kết thúc ca, không chỉ tính phần vượt grace. Giữ quy tắc phân loại MISSING_OUT/về sớm đã có.
- Ví dụ thiết kế, không phải số đo app: ca bắt đầu 08:30, grace_in=10 phút; vào 08:40 → late_min=0; vào 08:41 → late_min=11.
- Phút làm việc chỉ là phần giao giữa khoảng vào–ra hợp lệ và khoảng ca, trừ phần giao với giờ nghỉ trưa; không cộng công cho đến sớm/về muộn ngoài ca, không trừ phần nghỉ nằm ngoài khoảng đã làm.
- Kết quả số phút lấy phần nguyên sau khi tính chênh lệch. So sánh điều kiện grace bằng timestamp đầy đủ, không cắt giây trước khi so; không làm tròn từng mốc để thay đổi điều kiện muộn/sớm.
- Mỗi cặp nhân viên/ngày có trạng thái hiệu lực NORMAL/LATE/EARLY/LATE_EARLY tính 1 ngày công; các trạng thái khác thống kê riêng, không cộng vào chỉ số này. Không tính công nửa ngày trong demo.
- Giải trình được duyệt cập nhật kết quả cùng ngày; chỉ tính ngày đó theo trạng thái hiệu lực, không cộng thêm một ngày do có giải trình. Không đếm trùng theo số event hoặc số giải trình.
- Cần đồng bộ công thức trong đặc tả, skill nghiệp vụ và mô tả tổng hợp/xuất Excel; chưa sửa các nguồn chuẩn hoặc code. FG-ATT-002/005 đã cập nhật theo xác nhận, giữ APPROVED; chưa nghiệm thu app.

## Q-011 — Chuyển cấp khi nhiều vai trò

- §6 cho nhiều vai trò, §5.7 quy định MANAGER→HR, HR→OWNER, OWNER→HR nhưng chưa có ưu tiên khi tài khoản nhiều vai trò.
- Ảnh hưởng: FG-REQ-002, FG-AUTH-002.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với bảng thứ tự vai trò người gửi.

| Thứ tự xét người gửi | Nhóm người duyệt hợp lệ |
|---|---|
| Có OWNER, kể cả kiêm HR hoặc vai trò khác | HR khác người gửi |
| Có HR, không có OWNER | OWNER khác người gửi |
| Là MANAGER của chính phòng ban mình, không có OWNER/HR | HR khác người gửi |
| Các trường hợp còn lại | MANAGER đúng phòng ban của người gửi, khác người gửi |

- Luôn chặn tự duyệt, kể cả tài khoản nhiều vai trò. MANAGER chỉ quản lý phòng ban khác được xử lý như trường hợp còn lại khi gửi giải trình của bản thân.
- Không có người duyệt hợp lệ: giữ PENDING và hiển thị thông báo cần bố trí người duyệt, không tự duyệt hoặc tự chuyển sang nhóm ngoài quy tắc. Không thêm push/thông báo ngoài app.
- Thứ tự trên chỉ dùng chọn nhóm duyệt giải trình, không biến thành thứ bậc quyền toàn hệ thống hoặc loại bỏ các vai trò khác của tài khoản.
- Cần đồng bộ đặc tả §5.7, quy tắc nghiệp vụ/API/UI kiểm phạm vi duyệt; chưa tự thêm trường phân công hoặc endpoint. FG-REQ-002/FG-AUTH-002 đã cập nhật theo xác nhận, giữ APPROVED; chưa triển khai/nghiệm thu.

## Q-012 — KPI và query rút gọn trong UI

- W-02 gọi events?limit=10, OpenAPI dùng page/size. Có mặt/Đi muộn/Chưa đến chưa đủ định nghĩa tổng hợp khi lễ/ca/trạng thái tạm.
- Ảnh hưởng: FG-DASH-001.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với bảng định nghĩa và bốn ý phạm vi/thời gian/truy vấn.

| Chỉ số | Định nghĩa đã duyệt |
|---|---|
| Có mặt | Số nhân viên đã ghi nhận giờ vào ca hôm nay |
| Đi muộn | Trong nhóm có mặt, giờ vào vượt giờ bắt đầu ca + grace_in |
| Chưa đến | Đã tới giờ ca nhưng chưa có giờ vào |
| Lượt người lạ | Số sự kiện UNKNOWN hôm nay, không gồm SPOOF |

- Ba chỉ số nhân viên chỉ tính ACTIVE có ca hôm nay, loại HOLIDAY/LEAVE/OFF; mỗi nhân viên đếm một lần theo giờ công hiệu lực. Đi muộn là tập con của Có mặt, không cộng hai nhóm để ra tổng người.
- Chỉ số cập nhật tạm thời trong ngày; có thể tính Đi muộn từ giờ vào/grace mà không đổi trạng thái IN_PROGRESS thành LATE trước chốt theo Q-008.
- “Lượt người lạ” đếm event, không khẳng định là số người riêng biệt. Ngày hôm nay theo timezone công ty; event UNKNOWN lọc theo thời điểm xảy ra trong ngày đó.
- 10 sự kiện mới nhất dùng `GET /events?page=1&size=10`, theo thứ tự mới nhất trước; không thêm query limit ngoài hợp đồng.
- Cần đồng bộ mô tả UI W-02, tên nhãn và định nghĩa tổng hợp với đặc tả/API khi cần; không thêm biểu đồ, endpoint hoặc trường counters WS ngoài nguồn. FG-DASH-001 đã cập nhật, giữ APPROVED; chưa triển khai/nghiệm thu.

## Q-013 — Quản trị công ty và timezone

- §6 có dòng Công ty; DB có company.name/timezone, nhưng không có màn/API company riêng.
- Ảnh hưởng: FG-SYS-001.
- Trạng thái: **ĐÃ CHỐT — ĐÃ ĐỒNG BỘ NGUỒN 14/11/2026**.
- Người quyết định: người dùng trong chat, ngày 14/11/2026 (Asia/Bangkok), trả lời “đồng ý” với bốn ý về công ty và múi giờ.
- Dùng một công ty từ dữ liệu seed của dự án; múi giờ demo cố định `Asia/Ho_Chi_Minh`.
- Web/Kiosk hiển thị tên công ty và ngày giờ theo cấu hình đó. Múi giờ người vận hành hoặc máy tính không thay đổi cách xác định ngày công/ngày sự kiện của công ty.
- Không bổ sung màn hình/API sửa công ty hoặc timezone trong demo. Dòng phân quyền “Công ty” trong ma trận không được dùng để suy ra tính năng CRUD công ty ngoài phạm vi này.
- FG-SYS-001 đã cập nhật theo xác nhận, giữ APPROVED; chưa thay seed/cấu hình thực tế hoặc triển khai/nghiệm thu app.

## Trạng thái sau review

**13/13 mục đã chốt, không còn Q chưa có quyết định trong danh sách này.** Toàn bộ 32 specs giữ APPROVED; chưa có feature được xác nhận hoàn thành để chuyển archived.

Nguồn chuẩn đã được đồng bộ theo 13 quyết định. Thực hiện sau khi người dùng trực tiếp yêu cầu “đồng bộ nguồn chuẩn theo các quyết định trước khi triển khai”. Chưa có code app hoặc nghiệm thu tính năng trong thay đổi này.

| Nhóm quyết định | Nguồn hiện tại |
|---|---|
| Q-001 quyền | OpenAPI v1.1.0, đặc tả §6, UI W-07/W-09/W-14 |
| Q-002 gallery | Đặc tả §4.6, thiết kế DB §5/9, hub-rules, T04/T11 |
| Q-003/Q-004 | WS, UI K-06/K-08/K-11, T05/T08 |
| Q-005/Q-006 | Đặc tả §4.6/5.2/5.9, REST/WS, UI, hub-rules |
| Q-007 | RecognitionSettings, đặc tả §4.5, UI W-14, T13 |
| Q-008 | Health, đặc tả §4.1/5.5, WS, hub/AGENTS, T01/T03 |
| Q-009 | WAITING_IN đồng bộ DB/API/token, đặc tả §5.5, T09/T10/T12 |
| Q-010/Q-011 | Đặc tả §5.5/5.7/5.8, cham-cong-vn, API/UI, T09 |
| Q-012/Q-013 | Đặc tả §6, API dashboard, UI/token/FG-SYS-001 |

Báo cáo và giới hạn kiểm tra: [báo cáo đồng bộ](../../ket-qua-kiem-thu/2026-11-14_dong-bo-nguon/bao-cao.md). Dữ liệu seed và 44 ca test_constraints gốc giữ nguyên; không xác nhận chạy DB PostgreSQL 16 hoặc nghiệm thu app trong bước này.

## Ghi nhận yêu cầu đồng bộ nguồn trước đó (lịch sử)

> An ơi, bộ 32 specs đã được review/approved và người dùng đã chốt đủ Q-001 đến Q-013 trong `03-app/docs/specs/CAN-CHOT.md`; lịch sử xác nhận ở `LICH-SU-DUYET.md`. Nhờ An đồng bộ các nguồn chuẩn liên quan (đặc tả, DB nếu cần, OpenAPI/WS, UI, quy tắc nghiệp vụ/plan nếu bị ảnh hưởng) theo quyết định này, rồi gửi commit để đối chiếu. Đợt review mới cập nhật specs, chưa tự sửa nguồn chuẩn/code và chưa nghiệm thu app.

## Chi tiết biểu diễn hợp đồng đã đồng bộ
- WAITING_IN biểu diễn Chưa đến — tạm thời, check_in NULL/finalized=false; enum thứ 12 ở DB/API/UI.
- WS thêm NO_GALLERY và error RECOGNITION_UNAVAILABLE/OPERATION_INCOMPLETE có seq khi phản hồi frame.
- REST 409 PROFILE_ALREADY_REVIEWED; 503 BIOMETRIC_DELETE_INCOMPLETE/RECOGNITION_UNAVAILABLE. Giữ nguyên 77 operation và operationId, không thêm endpoint.

## Q-014 — 16/11/2026, đã chốt

- Người dùng trực tiếp chọn SECURITY tra cứu riêng NV MANUAL với thông tin tối thiểu để chấm hộ. Server giới hạn ACTIVE/MANUAL, không trả email/điện thoại/dữ liệu hồ sơ mặt; không mở API chi tiết/ghi nhân viên. Các vai trò khác giữ quyền riêng.
- Đồng bộ OpenAPI 1.1.1 và đặc tả 1.4.5; không đổi DB hoặc thêm endpoint.
