# Kịch bản test FaceGate theo checklist FG-001 đến FG-070

Ngày soạn 18/11/2026. Thứ tự và mã ca bám theo bảng “FaceGate - Checklist test chuc nang” đã tải lên Google Drive. Đây là hướng dẫn thực hiện. Kết quả của đợt chạy mới do người test ghi sau từng ca.

Bảng theo dõi nằm trong **DATN → Test chức năng** trên Google Drive của nhóm.

## Chuẩn bị một lần

1. Mở Web tại http://127.0.0.1:8000/login và mở bảng checklist trong tab bên cạnh.
2. Dùng hai cửa sổ trình duyệt hoặc hai hồ sơ trình duyệt để thao tác quản trị và nhân viên. Luôn kiểm tên người đang đăng nhập trước khi lưu.
3. Kiểm http://127.0.0.1:8000/api/v1/health. Phần Web cần database kết nối được. Các ca nhận dạng cần thêm model_verified=true và gallery có hồ sơ hợp lệ. Lần kiểm gần nhất trước khi soạn hướng dẫn ghi db=true, model_verified=false, gallery_size=0. Cần kiểm lại khi bắt đầu.
4. Kiosk phải mở được trên Android và ghép vào cùng Hub với Web. Máy ảo dùng http://10.0.2.2:8000. Điện thoại nối USB và đã adb reverse cổng 8000 có thể dùng http://127.0.0.1:8000. Điện thoại qua Wi-Fi dùng IP LAN của máy Hub khi Hub đã được cấu hình phục vụ LAN.
5. Mỗi lần test dùng một tiền tố riêng, ví dụ TEST-1811-A. Tên nhân viên, phòng, ca và lý do đều có tiền tố này để tìm lại được.
6. Trước các ca xóa dữ liệu, chọn hồ sơ demo dành riêng cho ca đó. Hồ sơ cần dùng tiếp cho nhận dạng phải còn dữ liệu đến FG-067.

Tài khoản demo theo kịch bản trong repo, mật khẩu ban đầu Demo@123. Nếu đã đổi mật khẩu trong phiên trước, dùng mật khẩu hiện hành.

| Vai trò | Email | Dùng cho |
|---|---|---|
| OWNER | nv001@demo.local | Cấu hình và quản trị toàn hệ thống |
| HR | nv002@demo.local | Nhân sự, bảng công, giải trình |
| MANAGER | nv005@demo.local | Quản lý phòng Kỹ thuật |
| EMPLOYEE | nv006@demo.local | Trang cá nhân, gửi giải trình |
| SECURITY | nv020@demo.local | Giám sát, chấm hộ, xử lý cảnh báo |
| Nhân viên chấm hộ | NV022 · Cao Nhật Minh | Chọn trong luồng chấm hộ, kiểm lại ACTIVE và MANUAL |

### Dữ liệu cần có để chạy theo đúng thứ tự

- Một nhân viên thử chưa có dữ liệu quan trọng, dùng tạo/sửa/khóa/nghỉ việc. Có thể tạo ở FG-007 rồi dùng tại FG-008 và FG-009.
- Một hồ sơ đã duyệt dành riêng để xóa tại FG-010.
- Hai hồ sơ PENDING khác nhau để thử duyệt và từ chối ở FG-021 đến FG-023.
- Một hồ sơ đã duyệt dành riêng để rút đồng ý tại FG-044.
- Một người tự nguyện đã có mẫu ACTIVE, giữ đến FG-067 để thử nhận dạng xuyên hệ thống.
- Hai yêu cầu PENDING của nhân viên khác người duyệt, dùng tại FG-029 và FG-030. Thêm một yêu cầu của MANAGER để kiểm nhánh duyệt tại FG-031.
- Hai cửa thử, một ATTENDANCE_ACCESS và một ACCESS_ONLY. Một thiết bị thử có thể thu hồi và ghép lại.

Nếu còn thiếu dữ liệu, chuẩn bị qua giao diện đăng ký FG-046 đến FG-050 hoặc gửi giải trình FG-042 trước khi bắt đầu lượt chạy chính. Nếu chưa chuẩn bị được, ghi “Thiếu điều kiện” ở ca tương ứng, nêu rõ thiếu gì rồi chuyển ca kế tiếp. Quay lại các ca này sau khi hoàn tất bước tạo dữ liệu phía dưới.

### Cách ghi vào bảng sau từng ca

- **Đạt** khi đã chạy đủ các bước và đối chiếu đúng kết quả mong đợi.
- **Lỗi** khi đã thử và hành vi lệch kết quả mong đợi. Ghi bước lỗi, thông báo và dữ liệu thử.
- **Thiếu điều kiện** khi thiếu Kiosk, mô hình, hồ sơ mặt, dữ liệu ngày công hoặc phần cứng cần thiết.
- **Đang test** trong lúc làm. **Chưa test** khi chưa thực hiện.
- Cột “Đã test” tự hiện ✓ khi chọn Đạt hoặc Lỗi. Dấu này cho biết đã chạy ca, kết quả nằm ở cột Trạng thái.
- Điền Người test, Ngày test, Kết quả thực tế và Lỗi/vướng mắc. Lưu ảnh lỗi với mã ca, ví dụ FG-025-buoc-2.png.
- Những ca có nhiều bước chỉ chọn Đạt sau khi kiểm đủ. Nếu chỉ kiểm được một phần, ghi số bước đã kiểm và giữ Đang test hoặc Thiếu điều kiện tùy tình huống.

Mẫu ghi lỗi có thể gửi ngay trong chat.

> FG-025 · nv001@demo.local · Bảng công · sửa ngày 13/11 của nhân viên TEST-1811-A · bước 2 · để trống lý do vẫn lưu được · mong đợi yêu cầu nhập lý do · ảnh đính kèm.

## FG-001 — Đăng nhập theo vai trò

**Tài khoản** lần lượt EMPLOYEE, MANAGER, HR, SECURITY, OWNER.

1. Để trống email/mật khẩu rồi bấm Đăng nhập. Sau đó thử email hợp lệ với mật khẩu sai.
2. Đăng nhập đúng bằng từng tài khoản. Ghi tên người dùng, vai trò và khu vực được mở.
3. Đăng xuất trước khi chuyển tài khoản.

**Đạt khi** trường bắt buộc được kiểm, mật khẩu sai hiện lỗi, mật khẩu đúng mở được khu vực phù hợp. EMPLOYEE vào Trang cá nhân. Tài khoản có quyền quản trị có thể chọn khu vực được cấp.

## FG-002 — Làm mới phiên và đăng xuất

**Tài khoản** EMPLOYEE, sau đó OWNER.

1. Đăng nhập và chuyển vài trang trong cùng phiên.
2. Nhấn F5, ghi lại màn hình sau tải lại. Bản Web hiện lưu phiên trong bộ nhớ, F5 có thể yêu cầu đăng nhập lại.
3. Đăng nhập lại, chọn Menu tài khoản → Đăng xuất. Dùng nút Back hoặc mở lại URL trang riêng.
4. Phần xoay refresh token khi access token hết hạn đối chiếu thêm ca tự động FG-070.

**Đạt khi** phiên hiện hành hoạt động, đăng xuất đưa về đăng nhập và trang riêng bị chặn sau đăng xuất. Ghi rõ hành vi F5. Mô tả “mở lại vẫn giữ phiên” trong checklist cũ cần đối chiếu hành vi lưu phiên hiện tại.

## FG-003 — Đổi mật khẩu

**Tài khoản** tài khoản thử do OWNER tạo, tránh đổi các tài khoản demo dùng chung.

1. Menu tài khoản → Đổi mật khẩu. Thử mật khẩu xác nhận khác nhau và thiếu trường bắt buộc.
2. Đổi bằng mật khẩu hợp lệ do bạn tự chọn.
3. Đăng nhập lại bằng mật khẩu mới. Thử mật khẩu cũ trong cửa sổ riêng.
4. Ghi nhận việc yêu cầu đăng nhập lại và hiệu lực các phiên cũ theo chính sách hệ thống.

**Đạt khi** dữ liệu sai bị chặn, mật khẩu mới đăng nhập được, mật khẩu cũ bị từ chối. Lưu mật khẩu mới ở nơi bạn quản lý để dùng tiếp.

## FG-004 — Phạm vi theo vai trò

1. OWNER mở từng mục quản trị. EMPLOYEE thử mở trực tiếp /admin/employees.
2. MANAGER mở Nhân viên/Bảng công và đối chiếu phòng Kỹ thuật với phòng khác.
3. SECURITY kiểm menu Giám sát/Sự kiện. HR kiểm các thao tác nhân sự.
4. Thử URL của mục không có quyền, kể cả khi tự nhập đường dẫn.

**Đạt khi** giao diện và dữ liệu phản ánh đúng quyền, truy cập ngoài quyền bị chặn. HR có chấm hộ nhưng thiếu quyền xử lý cảnh báo/mở cửa tay. SECURITY thiếu quyền quản lý hồ sơ nhân viên. MANAGER chỉ đọc dữ liệu trong phạm vi được giao.

## FG-005 — Dashboard hôm nay

**Tài khoản** OWNER hoặc HR → Tổng quan.

1. Ghi ngày đang xem và các số tổng hợp.
2. Mở Bảng công/Sự kiện cùng ngày, cùng phạm vi để đối chiếu từng chỉ số.
3. Làm mới trang và kiểm thông báo tải/trống/lỗi nếu có.

**Đạt khi** ngày, số liệu và phạm vi giữa các màn khớp nhau. Ghi trạng thái Hub nếu đang “chưa sẵn sàng”.

## FG-006 — Danh sách, tìm kiếm và lọc nhân viên

**Tài khoản** OWNER → Nhân viên.

1. Tìm NV006 theo mã rồi tìm theo một phần tên.
2. Kết hợp phòng ban, trạng thái và các bộ lọc đang có. Chuyển trang rồi đổi bộ lọc.
3. Tìm chuỗi không tồn tại và xóa bộ lọc.

**Đạt khi** danh sách đúng tiêu chí, đổi lọc về trang đầu phù hợp, trạng thái rỗng rõ ràng và xóa lọc trả về dữ liệu bình thường.

## FG-007 — Xem và cập nhật hồ sơ nhân viên

**Tài khoản** OWNER → Nhân viên.

1. Thêm nhân viên mã TEST1811A01, tên “Nhân viên thử 1811 A”, điền các trường bắt buộc. Nếu mã đã tồn tại, dùng hậu tố khác.
2. Tìm lại hồ sơ, mở chi tiết và các tab.
3. Sửa tên hoặc phòng ban của chính hồ sơ thử. Lưu rồi mở lại để đối chiếu.

**Đạt khi** tạo/sửa được, thông tin lưu đúng và mã trùng bị báo lỗi. Nhân viên mới mặc định FACE. Form hiện tại thiếu ô đổi phương thức trực tiếp, nên ghi nhận theo luồng thực tế. MANUAL được thiết lập qua luồng sinh trắc phù hợp.

## FG-008 — Tạm khóa và kích hoạt lại

**Tài khoản** OWNER → hồ sơ thử FG-007.

1. Tạm khóa và đối chiếu trạng thái trong danh sách/chi tiết.
2. Kích hoạt lại, tải lại danh sách.
3. Nếu kiểm tác động nhận dạng, dùng thêm hồ sơ thử có mẫu ACTIVE và Kiosk sẵn sàng.

**Đạt khi** trạng thái đổi đúng sau mỗi thao tác. Hồ sơ bị khóa phải bị từ chối khi nhận dạng. Nếu chưa thử Kiosk, ghi rõ phần trạng thái đã kiểm và phần nhận dạng còn chờ.

## FG-009 — Xác nhận nghỉ việc

**Tài khoản** OWNER → hồ sơ thử FG-007, đã hoàn tất FG-008.

1. Ghi lại mã, trạng thái và lịch sử công/sự kiện hiện có.
2. Chọn nghỉ việc, thử Hủy, rồi mở lại và xác nhận.
3. Mở lại hồ sơ/lịch sử. Nếu hồ sơ có mẫu mặt, kiểm hồ sơ mẫu sau thao tác.

**Đạt khi** trạng thái thành TERMINATED, sinh trắc được xóa theo đặc tả và lịch sử công/sự kiện còn. Nếu hồ sơ thử chưa từng có mẫu hoặc lịch sử, phần kiểm bảo toàn/xóa cần thêm hồ sơ có dữ liệu tương ứng.

## FG-010 — Xóa dữ liệu khuôn mặt

**Tài khoản** OWNER/HR → hồ sơ đã duyệt dành riêng cho ca này.

1. Ghi số mẫu, trạng thái mặt và lịch sử công trước khi xóa.
2. Chọn Xóa dữ liệu khuôn mặt và xác nhận.
3. Mở lại hồ sơ, đối chiếu consent/phương thức chấm công và kiểm nhận dạng khi Kiosk sẵn sàng.

**Đạt khi** mẫu bị xóa, consent được gỡ, phương thức thành MANUAL và mẫu hết hiệu lực nhận dạng. Công/sự kiện còn. Nếu thao tác báo chưa hoàn tất, ghi lỗi và trạng thái từng phần. Giữ người dùng cho FG-051 đến FG-067 ở hồ sơ khác.

## FG-011 — Phòng ban

**Tài khoản** OWNER → Phòng ban & tài khoản → Phòng ban.

1. Tạo phòng “TEST-1811-A Phòng thử”.
2. Sửa tên và chọn người quản lý phù hợp trong các lựa chọn giao diện.
3. Tải lại và đối chiếu tên, người quản lý.

**Đạt khi** dữ liệu đúng sau lưu, trường bắt buộc được kiểm. Dùng phòng thử để tránh ảnh hưởng phạm vi MANAGER demo.

## FG-012 — Tài khoản và phân quyền

**Tài khoản** OWNER → Phòng ban & tài khoản → Tài khoản.

1. Tạo tài khoản thử, ghi email và thông tin đăng nhập tạm do hệ thống cấp.
2. Gán vai trò và phạm vi phòng ban.
3. Đăng nhập bằng tài khoản thử trong cửa sổ riêng, kiểm menu/dữ liệu.
4. Thay đổi trạng thái tài khoản và thử đăng nhập lại.

**Đạt khi** quyền/phạm vi được áp dụng và tài khoản bị khóa bị chặn. Đối chiếu hiệu lực phiên đang mở nếu đang kiểm việc thu hồi phiên.

## FG-013 — Đặt lại mật khẩu và PIN Kiosk

**Tài khoản** OWNER → tài khoản thử có vai trò được phép đăng ký.

1. Dùng chức năng đặt lại mật khẩu. Đăng nhập bằng mật khẩu tạm và thực hiện bước đổi bắt buộc nếu được yêu cầu.
2. Đặt PIN Kiosk do bạn tự chọn cho tài khoản thử.
3. Trên Kiosk, chọn đúng người đăng ký, thử PIN sai một lần rồi PIN đúng.

**Đạt khi** mật khẩu mới và PIN đúng hoạt động, thông tin sai bị từ chối. Phần PIN cần Kiosk và ghi nhận riêng nếu chưa sẵn sàng.

## FG-014 — Ca làm và kiểm dữ liệu giờ

**Tài khoản** OWNER/HR → Ca & lịch → Ca.

1. Tạo “TEST-1811-A Ca ngày”, 08:30–17:30, nghỉ 12:00–13:00, grace vào/ra 10 phút.
2. Sửa tên hoặc grace, lưu rồi mở lại.
3. Thử giờ kết thúc bằng/trước giờ bắt đầu, ví dụ 22:00–06:00. Thử ca dài quá 17 giờ.

**Đạt khi** ca ngày hợp lệ lưu được, cấu hình sai bị chặn và giữ form để sửa. Bản hiện tại hỗ trợ ca cùng ngày, kết thúc sau bắt đầu, tối đa 17 giờ. Cụm “ca qua đêm” trong checklist cũ cần sửa thành ca kiểm dữ liệu không hợp lệ. Cửa sổ tiếp nhận sự kiện có thể vắt sang ngày kế tiếp.

## FG-015 — Phân ca

**Tài khoản** OWNER/HR → Ca & lịch → Phân ca.

1. Tạo nhân viên thử thứ hai TEST1811A02 nếu cần, vì FG-007 đã nghỉ việc.
2. Phân ca FG-014 cho người này theo Thứ Hai đến Thứ Sáu, từ ngày test.
3. Thêm phân ca trùng nhân viên/ngày trong tuần/khoảng hiệu lực.
4. Gỡ phân ca thử và kiểm lại danh sách. Tạo lại phân ca nếu còn cần cho ca sau.

**Đạt khi** phân ca hợp lệ lưu được, chồng lấn bị chặn và thao tác gỡ có hiệu lực.

## FG-016 — Ngày lễ

**Tài khoản** OWNER/HR → Ca & lịch → Ngày lễ.

1. Thêm 31/12/2026, tên “TEST-1811-A Ngày lễ”.
2. Kiểm bộ lọc năm và thử thêm trùng ngày.
3. Xóa bản ghi thử vừa thêm rồi kiểm danh sách.

**Đạt khi** ngày đúng, bản trùng bị chặn, xóa cập nhật đúng. Nếu dùng ngày khác, ghi chính xác ngày đã chọn.

## FG-017 — Cấu hình cổng

**Tài khoản** OWNER → Cửa & thiết bị.

1. Tạo hai cửa “TEST-1811-A Chấm công” và “TEST-1811-A Ra vào”.
2. Chọn lần lượt ATTENDANCE_ACCESS và ACCESS_ONLY.
3. Sửa tên hoặc cấu hình hợp lệ, mở lại chi tiết.

**Đạt khi** lưu đúng chế độ và thông tin cổng. Giữ hai cửa để dùng ở các ca Kiosk phía dưới.

## FG-018 — Phòng ban được phép qua cổng

**Tài khoản** OWNER, hai hồ sơ mặt tự nguyện thuộc hai phòng khác nhau.

1. Giới hạn cửa thử cho một phòng ban, ghi cấu hình.
2. Người thuộc phòng được phép đứng trước Kiosk đã ghép cửa đó.
3. Người ngoài phòng đứng trước Kiosk. Mở Sự kiện/Bảng công đối chiếu.

**Đạt khi** người được cấp quyền qua được, người ngoài phòng nhận DENY/RULE và có sự kiện tương ứng, lượt từ chối hết hiệu lực tính công. Thiếu hai hồ sơ/Kiosk thì ghi Thiếu điều kiện.

## FG-019 — Cấp mã ghép thiết bị

**Tài khoản** OWNER → Cửa & thiết bị.

1. Tạo thiết bị thử gắn cửa FG-017, lấy mã hoặc QR.
2. Trên Kiosk nhập đúng địa chỉ Hub và mã, hoặc quét QR.
3. Đối chiếu tên thiết bị, cửa và trạng thái trên Web/Kiosk.

**Đạt khi** ghép đúng thiết bị/cửa. Lưu tên thiết bị để dùng FG-020.

## FG-020 — Thu hồi thiết bị

**Tài khoản** OWNER và Kiosk đã ghép FG-019.

1. Khi Kiosk đang kết nối, thu hồi chính thiết bị thử.
2. Kiểm Kiosk trở về Ghép thiết bị và trạng thái Web.
3. Cấp mã mới, ghép lại để tiếp tục các ca sau.

**Đạt khi** thiết bị bị thu hồi ngừng quét và cần ghép lại. Token cũ hết hiệu lực.

## FG-021 — Danh sách hồ sơ mặt và ảnh mẫu

**Tài khoản** OWNER/HR → Xác nhận khuôn mặt.

1. Chọn một hồ sơ PENDING đã chuẩn bị bằng Kiosk.
2. Mở chi tiết, đối chiếu mã/tên, tư thế và ảnh mẫu với người đăng ký.
3. Mở lại bằng EMPLOYEE/SECURITY để kiểm phạm vi truy cập phù hợp.

**Đạt khi** ảnh đúng hồ sơ và chỉ người có quyền xem được. Người tự nguyện xác nhận ảnh của chính họ trong dữ liệu thử.

## FG-022 — Duyệt hồ sơ mặt

**Tài khoản** OWNER/HR.

1. Ghi hồ sơ PENDING và số mẫu trước duyệt.
2. Duyệt rồi mở lại danh sách/chi tiết.
3. Khi model/Kiosk sẵn sàng, người vừa duyệt thử nhận dạng.

**Đạt khi** hồ sơ thành ACTIVE và được đưa vào gallery. Nhận dạng thật là phần kiểm bắt buộc để kết luận hiệu lực cuối.

## FG-023 — Từ chối hồ sơ mặt

**Tài khoản** OWNER/HR, dùng hồ sơ PENDING thứ hai.

1. Mở hồ sơ, chọn Từ chối và nhập lý do nếu giao diện yêu cầu.
2. Kiểm trạng thái sau lưu.
3. Đối chiếu gallery/nhận dạng của người có hồ sơ bị từ chối.

**Đạt khi** hồ sơ bị từ chối và mẫu mới hết điều kiện kích hoạt. Với đăng ký thay thế, ghi thêm trạng thái hồ sơ cũ theo luồng thực tế.

## FG-024 — Bảng công quản trị

**Tài khoản** OWNER/HR, sau đó MANAGER → Bảng công.

1. Chọn tháng 11/2026, lọc NV006/phòng Kỹ thuật và mở một ngày có dữ liệu.
2. Đối chiếu ca, giờ vào/ra, trạng thái, nguồn và liên kết sự kiện.
3. MANAGER thử xem ngoài phạm vi.

**Đạt khi** số liệu đúng đối tượng, nguồn và phạm vi. Phân biệt ngày đang làm việc với ngày đã chốt.

## FG-025 — Sửa ngày công có lý do

**Tài khoản** OWNER/HR → ngày đã chốt của người khác.

1. Ghi giờ/trạng thái trước sửa. Thử sửa mà để trống lý do.
2. Nhập giờ hợp lệ và lý do “TEST-1811-A FG025”, lưu.
3. Mở lại ngày công và Nhật ký. Thử sửa ngày công của chính tài khoản hiện tại.

**Đạt khi** thiếu lý do bị chặn, sửa hợp lệ có nguồn Sửa tay và lưu bền, tự sửa công bị chặn. Nếu chưa có ngày phù hợp, ghi Thiếu điều kiện.

## FG-026 — Ghi nhận ngày nghỉ

**Tài khoản** OWNER/HR → Bảng công.

1. Chọn ngày của nhân viên thử, ghi trạng thái trước thao tác.
2. Thực hiện ghi nhận nghỉ qua chức năng hiện có, điền lý do theo form.
3. Tải lại và kiểm ngày đó ở Trang cá nhân của nhân viên.

**Đạt khi** ngày có trạng thái LEAVE, đúng người/ngày và vẫn giữ hiệu lực khi tải lại.

## FG-027 — Chấm công hộ

**Tài khoản** SECURITY → Giám sát.

1. Chọn Chấm công hộ, tìm NV022, kiểm ACTIVE/MANUAL và chọn cửa chấm công.
2. Để trống lý do rồi gửi. Sau đó nhập “TEST-1811-A FG027” và xác nhận một lần.
3. Kiểm sự kiện, thời gian hiện tại, người chấm và ngày công.
4. Kiểm danh sách chọn thiếu nhân viên FACE và chính người chấm.

**Đạt khi** bắt buộc lý do, chỉ chấm người hợp lệ, thời điểm do hệ thống ghi. Lượt gần nhau được xử lý theo quy tắc công hiện hành.

## FG-028 — Xuất Excel bảng công

**Tài khoản** OWNER/HR, sau đó MANAGER nếu kiểm phạm vi xuất.

1. Chọn tháng/phạm vi ở Bảng công rồi Xuất Excel.
2. Mở file tải về, kiểm hai sheet Tổng hợp và Chi tiết.
3. Đối chiếu một nhân viên và một ngày với Web, gồm giờ, nguồn, phút muộn và tổng ngày duy nhất.

**Đạt khi** file mở được, tiếng Việt/ngày/giờ đúng và số liệu đúng phạm vi. Duyệt nhiều yêu cầu cho một ngày phải giữ cách đếm ngày duy nhất.

## FG-029 — Duyệt giải trình

**Tài khoản** MANAGER của phòng nhân viên gửi. Chuẩn bị một yêu cầu PENDING của NV006.

1. Mở Giải trình hoặc Trang cá nhân → Duyệt, chọn yêu cầu có tiền tố thử.
2. Đối chiếu ngày/giờ gốc, giờ đề nghị và lý do. Duyệt bằng người khác người gửi.
3. EMPLOYEE mở kết quả và chi tiết ngày công tương ứng.

**Đạt khi** trạng thái APPROVED, ghi chú hiện đúng và ngày công có nguồn Đã giải trình. Nếu chưa có yêu cầu, tạo theo FG-042 rồi quay lại.

## FG-030 — Từ chối giải trình

**Tài khoản** người có quyền duyệt, dùng yêu cầu PENDING khác FG-029.

1. Thử Từ chối với ghi chú trống.
2. Nhập “TEST-1811-A Cần bổ sung thông tin” rồi xác nhận.
3. Người gửi mở kết quả và đối chiếu ngày công trước/sau.

**Đạt khi** yêu cầu thành REJECTED, có lý do và giờ đề nghị bị từ chối hết hiệu lực áp vào ngày công.

## FG-031 — Phạm vi hàng chờ duyệt

1. MANAGER tạo một yêu cầu của chính mình và mở hàng chờ.
2. Kiểm yêu cầu của nhân viên trong phòng, ngoài phòng và yêu cầu của bản thân.
3. HR kiểm yêu cầu của MANAGER. Nếu thử OWNER/HR tự gửi, dùng tài khoản còn lại đúng nhánh để xử lý.

**Đạt khi** người gửi khác người duyệt, MANAGER chỉ xử lý đúng phạm vi. Yêu cầu của MANAGER chính phòng do HR xử lý. Yêu cầu OWNER do HR khác, yêu cầu HR không OWNER do OWNER khác theo đặc tả.

## FG-032 — Luồng sự kiện trực tiếp

**Tài khoản** OWNER/SECURITY → Giám sát.

1. Giữ màn Giám sát mở và thực hiện một lượt Kiosk thật hoặc chấm hộ hợp lệ.
2. Đối chiếu tên người/cửa/thời gian/kết quả mà không cần tải lại toàn trang.
3. Tạm ngắt mạng của máy xem giám sát rồi nối lại, kiểm trạng thái kết nối và sự kiện tiếp theo.

**Đạt khi** sự kiện và trạng thái kết nối cập nhật đúng. Đánh dấu phần chấm hộ riêng nếu lượt nhận dạng chưa chạy được.

## FG-033 — UNKNOWN và ảnh crop

**Điều kiện** gallery có hồ sơ ACTIVE, model sẵn sàng, người thử chưa đăng ký.

1. Người tự nguyện chưa có mẫu đứng trước Kiosk.
2. OWNER/SECURITY mở cảnh báo UNKNOWN tương ứng và xem crop.
3. Tài khoản ngoài quyền thử mở ảnh/chi tiết.

**Đạt khi** UNKNOWN thật có cảnh báo/crop đúng quyền. Gallery trống phải trả NO_GALLERY, cần chuyển sang FG-054 để kiểm trường hợp đó.

## FG-034 — Xử lý cảnh báo

**Tài khoản** SECURITY, có cảnh báo thật chưa xử lý.

1. Mở cảnh báo, chọn “Là nhân viên”, thử để trống người liên kết.
2. Chọn đúng nhân viên, nhập nội dung xử lý và lưu.
3. Mở lại cảnh báo và hồ sơ mặt của nhân viên liên kết.

**Đạt khi** bắt buộc chọn người khi đánh dấu Là nhân viên, kết quả xử lý lưu được. Sự kiện gốc được giữ và số mẫu mặt của người liên kết không tăng.

## FG-035 — Mở cửa mô phỏng

**Tài khoản** SECURITY/OWNER → Giám sát.

1. Chọn Mở cửa mô phỏng, chọn cửa, thử để trống lý do.
2. Nhập “TEST-1811-A FG035” rồi xác nhận một lần.
3. Đối chiếu Sự kiện và Bảng công.

**Đạt khi** có sự kiện mở tay đúng cửa/người/lý do. Thao tác này không tạo giờ công của nhân viên.

## FG-036 — Tra cứu và xuất CSV sự kiện

**Tài khoản** OWNER/SECURITY → Sự kiện.

1. Lọc thời gian, cửa, kết quả và tìm sự kiện FG-027/FG-035.
2. Xuất CSV và mở bằng Excel.
3. Đối chiếu vài dòng, tiếng Việt và mốc thời gian.

**Đạt khi** CSV đúng hợp đồng bộ lọc thời gian/cửa/kết quả. Ghi riêng nếu bộ lọc chi tiết trên màn hình chưa được hỗ trợ cho xuất CSV.

## FG-037 — Báo cáo chấm hộ

**Tài khoản** SECURITY/OWNER → Sự kiện → Báo cáo chấm hộ.

1. Lọc khoảng thời gian chứa FG-027.
2. Đối chiếu số lượt, người thực hiện và số nhân viên khác nhau với danh sách sự kiện.
3. Nếu một nhân viên có nhiều lượt, kiểm số nhân viên duy nhất.

**Đạt khi** số lượt và số người được tính đúng định nghĩa, dữ liệu nằm trong quyền tài khoản.

## FG-038 — Mô hình và ngưỡng nhận dạng

**Tài khoản** OWNER → Cấu hình nhận dạng.

1. Ghi mô hình đang chọn, trạng thái xác minh, ngưỡng và các thông số hiện tại.
2. Thử dữ liệu ngoài giới hạn bằng form, kiểm thông báo.
3. Nếu muốn thử lưu hợp lệ, ghi cấu hình gốc, đổi một thông số hợp lệ trên phiên test, mở lại kiểm rồi phục hồi giá trị gốc.

**Đạt khi** chỉ người có quyền sửa được, giá trị sai bị chặn và giá trị hợp lệ lưu đúng. Mọi thay đổi cần ghi trong kết quả để các ca sau đối chiếu đúng ngưỡng.

## FG-039 — Nhật ký kiểm toán

**Tài khoản** OWNER → Nhật ký.

1. Lọc thời gian của các thao tác vừa làm.
2. Tìm tạo/sửa nhân viên, sửa công hoặc thao tác quản trị có ghi audit.
3. Đối chiếu hành động, đối tượng, người thực hiện và thời gian.

**Đạt khi** nhật ký đúng thao tác đã thực hiện và tài khoản ngoài quyền bị chặn. Audit demo chỉ ghi các trường theo đặc tả hiện có.

## FG-040 — Trang nhân viên hôm nay

**Tài khoản** EMPLOYEE → Hôm nay.

1. Kiểm tên nhân viên, ngày công ty và ca đang áp dụng.
2. Đối chiếu IN/OUT với Bảng công quản trị cùng người/ngày.
3. Làm mới dữ liệu và kiểm trạng thái.

**Đạt khi** dữ liệu khớp. Trước chốt, chưa vào có thể là “Chưa đến — tạm thời”, có vào là “Đang làm việc — tạm thời” theo ca hiện hành.

## FG-041 — Bảng công tháng và chi tiết ngày

**Tài khoản** EMPLOYEE → Bảng công.

1. Chọn tháng có dữ liệu, chuyển trước/sau rồi quay lại.
2. Mở một ngày đã chốt và một ngày đang diễn ra.
3. Đối chiếu ca, giờ, nguồn, phút và sự kiện với quản trị.

**Đạt khi** tháng/ngày đúng, thống kê và chi tiết khớp nhau, dữ liệu chỉ thuộc nhân viên đang đăng nhập.

## FG-042 — Gửi giải trình

**Tài khoản** EMPLOYEE → chi tiết một ngày đã qua, đủ điều kiện, chưa có PENDING.

1. Bấm Gửi giải trình, thử thiếu trường bắt buộc.
2. Chọn Đi công tác, nhập giờ phù hợp với ngày/ca thực tế và lý do “TEST-1811-A FG042”.
3. Gửi một lần, kiểm danh sách Chờ duyệt.
4. Thử tạo yêu cầu chờ thứ hai cùng ngày.

**Đạt khi** yêu cầu đúng ngày/giờ/loại/lý do, trùng PENDING bị chặn. Ví dụ ngày có ca 08:30–17:30 và grace 10 phút, giờ 08:41–17:30 sau duyệt và chốt tương ứng 11 phút muộn.

## FG-043 — Theo dõi và hủy giải trình

**Tài khoản** EMPLOYEE.

1. Tạo yêu cầu chờ trên ngày thử khác FG-042.
2. Bấm Hủy rồi chọn giữ, kiểm yêu cầu còn chờ.
3. Hủy và xác nhận, kiểm tab Đã xử lý. Mở hàng chờ ở phía quản lý.

**Đạt khi** yêu cầu thành CANCELLED, mất khỏi hàng chờ và không áp giờ đề nghị vào công.

## FG-044 — Trạng thái mặt và rút đồng ý

**Tài khoản** nhân viên demo có mẫu ACTIVE dành riêng cho ca này.

1. Trang cá nhân → Khuôn mặt, kiểm trạng thái và thông tin consent.
2. Bấm Rút đồng ý rồi Hủy, đối chiếu trạng thái.
3. Thực hiện lại và xác nhận. OWNER mở hồ sơ nhân viên đối chiếu.
4. Khi Kiosk sẵn sàng, kiểm người này hết hiệu lực nhận dạng từ mẫu đã rút.

**Đạt khi** consent được gỡ, mẫu bị xóa, phương thức MANUAL và lịch sử công/sự kiện còn. Muốn dùng mặt lại cần đăng ký, đồng ý và duyệt lại.

## FG-045 — Bố cục Chrome Android

**Tài khoản** EMPLOYEE trên Chrome điện thoại dọc.

1. Mở Hôm nay, Bảng công, Giải trình, Khuôn mặt.
2. Mở chi tiết ngày, form giải trình và bàn phím.
3. Cuộn, chuyển tab, đóng form, kiểm các nút cuối màn hình.

**Đạt khi** thao tác được, chữ/nút rõ và không tràn ngang hoặc bị bàn phím che thao tác chính. Thử viewport 390×844 trên máy tính ghi là kiểm responsive. Phần Chrome Android thật cần thiết bị và mạng truy cập Hub.

## FG-046 — Ghép Kiosk bằng QR và nhập mã

**Tài khoản** OWNER trên Web, Kiosk ở màn Ghép thiết bị.

1. Nhập mã sai/hết hạn với địa chỉ Hub đúng, kiểm lỗi.
2. Tạo mã hợp lệ, ghép bằng nhập tay.
3. Dùng thiết bị thử khác hoặc ghép lại sau thu hồi để kiểm QR.

**Đạt khi** mã lỗi bị từ chối, mỗi phương thức hợp lệ ghép đúng Hub/cửa. Khởi động lại app để kiểm lưu token.

## FG-047 — Quyền và vòng đời camera

**Thiết bị** Android chạy Kiosk.

1. Kiểm tình huống camera chưa có quyền và thông báo hướng dẫn.
2. Bạn cấp quyền camera qua hộp thoại/cài đặt của Android, kiểm preview.
3. Đưa app nền rồi quay lại. Nếu đang thử từ chối quyền, kiểm chức năng nhập mã tay và đường dẫn cấp lại quyền.

**Đạt khi** app hướng dẫn đúng và camera phục hồi, tránh treo/đen màn hình sau quay lại.

## FG-048 — Mở đăng ký bằng PIN

**Điều kiện** có người đăng ký được cấp PIN tại FG-013.

1. Từ Kiosk mở luồng đăng ký, chọn đúng người phụ trách.
2. Thử PIN sai một lần, sau đó PIN đúng.
3. Kiểm chỉ phiên hợp lệ mở được danh sách nhân viên.

**Đạt khi** lỗi PIN rõ, PIN đúng đi tiếp. Kiểm khóa 5 lần sai bằng tài khoản thử riêng nếu muốn kiểm nhánh khóa, ghi thời gian/điều kiện phục hồi theo giao diện.

## FG-049 — Chọn người và ghi đồng ý

1. Trong phiên đăng ký hợp lệ, tìm nhân viên thử và kiểm mã/tên.
2. Ở màn đồng ý, thử tiếp tục khi chưa chọn Đồng ý.
3. Người được đăng ký đọc nội dung và tự xác nhận đồng ý dùng khuôn mặt.

**Đạt khi** đúng nhân viên, consent được ghi theo thao tác thật và đủ điều kiện đi tiếp. Ghi nhận nhánh từ chối nếu thực hiện trên hồ sơ thử riêng.

## FG-050 — Thu 5 tư thế và gửi hồ sơ

**Điều kiện** FG-049 hoàn tất, camera/model và phiên thu mẫu hoạt động.

1. Làm lần lượt tư thế theo hướng dẫn Kiosk, quan sát tiến độ và lý do khung bị từ chối.
2. Gửi khi đủ mẫu, kiểm màn gửi thành công.
3. OWNER/HR mở Xác nhận khuôn mặt, đối chiếu đúng hồ sơ PENDING.

**Đạt khi** tiến độ phản ánh mẫu hợp lệ, hồ sơ đúng người xuất hiện chờ duyệt. Kiosk chỉ hiện preview trực tiếp theo luồng, ảnh mẫu nằm trong giao diện quản trị có quyền.

## FG-051 — Nhận diện ở cửa chấm công

**Điều kiện** hồ sơ ACTIVE đã duyệt, thiết bị ghép cửa ATTENDANCE_ACCESS, đang trong cửa sổ ca.

1. Người thử đứng trước Kiosk, ghi kết quả IN và giờ nhận được.
2. Rời khung rồi quét lặp trong thời gian gần, kiểm ALREADY/cooldown theo cấu hình.
3. Sau khoảng tối thiểu hợp lệ để có OUT, mặc định 30 phút từ IN, quét lại.
4. Đối chiếu Web Hôm nay/Bảng công/Sự kiện.

**Đạt khi** IN/OUT khớp lượt thật, quét gần nhau được xử lý đúng. Trong lúc chờ OUT có thể làm các ca kế tiếp rồi quay lại hoàn tất mục này.

## FG-052 — Nhận diện ở cửa chỉ ra vào

**Điều kiện** thiết bị thử ghép cửa ACCESS_ONLY.

1. Ghi ngày công trước lượt quét.
2. Người có mẫu và quyền qua cửa đứng trước Kiosk.
3. Kiểm sự kiện và ngày công sau lượt quét.

**Đạt khi** ghi đúng sự kiện qua cửa, ngày công không thay đổi do lượt ở cửa ACCESS_ONLY.

## FG-053 — Từ chối theo chính sách

1. Với cửa giới hạn phòng ban, người ngoài phòng thử quét.
2. OWNER tạm khóa một hồ sơ thử có mẫu, người đó thử quét.
3. Đối chiếu kết quả và bảng công, sau đó mở khóa hồ sơ thử nếu còn sử dụng.

**Đạt khi** mỗi lý do từ chối được phản ánh đúng, lượt bị từ chối không tính công. Ghi riêng kết quả hai nhánh.

## FG-054 — Người lạ và gallery trống

1. Khi gallery có mẫu hợp lệ, người tự nguyện chưa đăng ký thử quét, đối chiếu UNKNOWN.
2. Trên môi trường test có gallery trống đã chuẩn bị, thử quét và đối chiếu NO_GALLERY.
3. Kiểm danh sách cảnh báo sau lượt gallery trống.

**Đạt khi** phân biệt UNKNOWN và NO_GALLERY. Gallery trống phải báo chưa có dữ liệu và không tạo cảnh báo người lạ. Nếu chưa có môi trường trống riêng, để phần này Thiếu điều kiện.

## FG-055 — Hướng dẫn trong khung hình

1. Để khung trống, sau đó thử hai người tự nguyện cùng vào khung.
2. Thử mặt quá xa, quay lệch và ánh sáng kém bằng điều kiện có thể kiểm soát.
3. Trở về tư thế hợp lệ và quan sát phục hồi.

**Đạt khi** hướng dẫn tương ứng điều kiện, khung thiếu chất lượng không bị báo nhận diện thành công sai.

## FG-056 — Hiển thị kết quả và âm thanh

1. Tạo một lượt nhận dạng thành công và một lượt từ chối thật.
2. Ghi nội dung/màu/thời gian hiển thị và âm thanh.
3. Kiểm Kiosk tự trở về màn quét và hạn chế gửi khung trong lúc hiện kết quả.

**Đạt khi** tên/mã và thông báo đúng kết quả Hub, âm thanh phù hợp và luồng quét phục hồi. Nếu thiết bị tắt âm, ghi tình trạng và thử lại với âm lượng nghe được.

## FG-057 — Mất mạng, nối lại và thu hồi

1. Tạm ngắt kết nối Kiosk với Hub, quan sát màn Offline.
2. Khôi phục mạng, kiểm tự nối lại và thử một lượt quét mới.
3. Thu hồi thiết bị thử từ Web, kiểm trở về Ghép thiết bị. Ghép lại nếu tiếp tục test.

**Đạt khi** offline/nối lại phản ánh đúng trạng thái, thiết bị bị thu hồi dừng dùng token cũ. Lượt trong thời gian offline cần được ghi nhận đúng khả năng hiện tại của hệ thống.

## FG-058 — Kiểm thử tự động Kiosk Socket

**Người chạy** Codex hoặc người thao tác terminal.

1. Mở PowerShell tại 03-app/kiosk.
2. Chạy lệnh bên dưới, lưu output có ngày giờ.
3. Ghi tổng tests/pass/fail/skipped của lượt mới vào FG-058.

~~~powershell
Set-Location 'D:/WorkSpace/DATN/datn-facegate-app/03-app/kiosk'
node --experimental-strip-types --test src/ws/KioskSocket.test.ts
~~~

**Đạt khi** lệnh trả mã 0 và toàn bộ ca đạt. Lần chạy 16/11 có 14/14 đạt, cần ghi riêng lượt chạy hiện tại.

## FG-059 — Tính công và chốt ngày

**Tài khoản** OWNER/HR, đối chiếu EMPLOYEE. Cần lịch sử thật hoặc bộ test nghiệp vụ.

1. Chọn các ngày có đủ lượt, đi muộn, thiếu OUT, nghỉ, ngày lễ và ngoài cửa sổ ca.
2. Đối chiếu ca, giờ, phút và trạng thái trước/sau chốt.
3. Kiểm dữ liệu đã sửa tay hoặc ghi nghỉ sau tải lại/recompute qua luồng hợp lệ.
4. Phần biên thời gian chưa có dữ liệu thật chuyển kiểm bằng test tự động nghiệp vụ.

**Đạt khi** theo cấu hình thực tế. Với mặc định trong đặc tả, cửa sổ nhận lượt từ start−3h đến end+4h, OUT cách IN ít nhất 30 phút và chốt tại end+4h. Ca 08:30–17:30 nghỉ 12:00–13:00 tối đa tính 480 phút trong ca. Grace 10 phút, 08:40 là 0 phút muộn, 08:41 là 11 phút. Trạng thái thiếu OUT có ưu tiên riêng. Phần “ca qua đêm” trong checklist cũ được đọc là kiểm cửa sổ ca vắt qua ngày, vì bản hiện tại chỉ nhận ca cùng ngày.

## FG-060 — Nạp mô hình và sức khỏe Hub

1. Mở /api/v1/health và Cấu hình nhận dạng, ghi status/db/gpu/model_verified/gallery_size.
2. Đối chiếu log khởi động với mô hình và gallery thực tế.
3. Khi có cấu hình lỗi được chuẩn bị trong môi trường kiểm riêng, kiểm trạng thái degraded và khả năng chặn nhận dạng.

**Đạt khi** thông tin sức khỏe đúng thực trạng. Để xác nhận nhận dạng hoạt động cần model_verified=true và runtime/gallery hợp lệ. Nếu model_verified=false, ghi lỗi khởi động cụ thể và để các ca nhận dạng Thiếu điều kiện.

## FG-061 — Đăng ký và cập nhật gallery

1. Đăng ký hồ sơ mới bằng Kiosk, trước duyệt kiểm chưa có hiệu lực.
2. Duyệt rồi thử nhận dạng.
3. Dùng hồ sơ riêng để thử thay mẫu hoặc xóa/rút đồng ý, kiểm nhận dạng sau mỗi thao tác.

**Đạt khi** gallery chỉ dùng hồ sơ đang hiệu lực. Đăng ký thay thế thất bại cần giữ trạng thái hồ sơ cũ theo quy tắc, xóa/rút làm mất hiệu lực mẫu đã xóa.

## FG-062 — Bộ quyết định và worker

**Người chạy** Codex hỗ trợ bằng test Hub và log, kết hợp Kiosk thật.

1. Đối chiếu một lượt MATCH, nhánh chưa đủ khung xác nhận, cooldown và lỗi chất lượng.
2. Chạy các test decision/worker/mutation đang có, ghi tên ca và output.
3. Nhánh quá tải/khung lỗi cần kết quả test hoặc lượt thử có log tương ứng.

**Đạt khi** quyết định đúng ngưỡng/cửa sổ xác nhận/cooldown và trạng thái lỗi đúng giao thức. Một lượt quét thành công chỉ xác minh được phần luồng đã chạy.

## FG-063 — Trạng thái Liveness trên Web

**Tài khoản** OWNER → Cấu hình nhận dạng.

1. Ghi trạng thái bật/tắt chống giả mạo và thông tin ngưỡng/phê duyệt hiện có.
2. Đối chiếu trạng thái runtime/log tương ứng.
3. Kiểm cách hiển thị khi chưa hiệu chỉnh hoặc thiếu phê duyệt.

**Đạt khi** giao diện phản ánh đúng khả năng hiện tại. Nếu đang tắt/chưa hiệu chỉnh, ghi đúng trạng thái đó.

## FG-064 — Hiệu chỉnh và kiểm mặt thật/giả

**Điều kiện** đủ dữ liệu video thật và quy trình T13, người tham gia đồng ý.

1. Làm theo RUN-T13.md trong thư mục báo cáo T13, chuẩn bị đủ nhóm video yêu cầu.
2. Chạy hiệu chỉnh/đánh giá và xem báo cáo trước khi chọn ngưỡng L.
3. Khi có ngưỡng được duyệt và bật hợp lệ, kiểm mặt thật cùng ảnh in/màn hình theo kịch bản, đối chiếu SPOOF trên Web.

**Đạt khi** có dữ liệu, số đo và kết quả thực tế theo tiêu chí T13. Thiếu dữ liệu/phê duyệt thì ghi Thiếu điều kiện và nêu phần còn thiếu.

## FG-065 — Web và Kiosk dùng chung Hub

1. Ghi địa chỉ Web và địa chỉ Hub Kiosk, đối chiếu chúng trỏ cùng máy/cổng dịch vụ.
2. Từ Web tạo mã ghép thiết bị, ghép trên Kiosk.
3. Thực hiện một lượt thật, tìm trên Giám sát/Sự kiện và Trang cá nhân.

**Đạt khi** cùng thiết bị/cửa/người/thời điểm/kết quả xuất hiện xuyên hệ thống. Ghi rõ IP LAN, loopback USB hoặc 10.0.2.2 của máy ảo đang dùng.

## FG-066 — Đo CPU, GPU và độ trễ

**Người chạy** Codex hỗ trợ theo T02/T08/T14.

1. Chạy preflight phần cứng, ghi CPU/GPU/PyTorch/CUDA thực tế.
2. Đo pipeline theo RUN-T14.md trên cấu hình phù hợp, gồm 1 và 3 Kiosk.
3. Thu đủ video/lượt người đứng vào để tính độ trễ UI theo công cụ hiện có.

**Đạt khi** đạt tiêu chí đo của plan với bằng chứng lưu được. GPU T14 cần CUDA và tối thiểu 300 khung cho mỗi Kiosk mỗi cấu hình theo hướng dẫn. Phép đo đứng vào cần tối thiểu 20 lượt thật. Kết quả CPU ghi đúng CPU và phần GPU còn chờ nếu thiếu thiết bị.

## FG-067 — Toàn luồng demo

1. Tạo/chọn hồ sơ thử, đồng ý và đăng ký Kiosk.
2. OWNER/HR duyệt, người thử quét cửa chấm công, xem sự kiện và Trang cá nhân.
3. Gửi một giải trình cho ngày đủ điều kiện, người khác đúng quyền duyệt.
4. Đối chiếu bảng công quản trị/nhân viên, xuất Excel và kiểm cùng ngày.
5. Kiểm thêm lượt cửa giới hạn phòng và cảnh báo thật nếu đã đủ điều kiện các mục liên quan.

**Đạt khi** cùng dữ liệu nối được toàn bộ các bước. Ghi video/ảnh từng đoạn và thời điểm. Phần OUT cần giữ khoảng thời gian hợp lệ như FG-051.

## FG-068 — Kiểm tra kiểu TypeScript

**Người chạy** Codex hoặc người thao tác terminal.

~~~powershell
Set-Location 'D:/WorkSpace/DATN/datn-facegate-app/03-app/web'
node node_modules/typescript/bin/tsc --noEmit
Set-Location 'D:/WorkSpace/DATN/datn-facegate-app/03-app/kiosk'
node node_modules/typescript/bin/tsc --noEmit
~~~

**Đạt khi** cả hai lệnh trả mã 0. Ghi kết quả riêng Web/Kiosk. Ca này kiểm kiểu mã nguồn.

## FG-069 — Bộ kiểm thử pytest Hub

**Người chạy** Codex hỗ trợ môi trường DB kiểm riêng.

1. Kiểm cấu hình DB test theo hướng dẫn các test hiện có. Nhóm test tích hợp cần T03_TEST_DATABASE_URL trỏ đúng DB kiểm.
2. Chạy pytest và lưu đầy đủ phần summary, failures, skips.
3. Ghi từng lý do skip/lỗi môi trường và phân biệt với lỗi nghiệp vụ đã tái hiện.

~~~powershell
Set-Location 'D:/WorkSpace/DATN/datn-facegate-app/03-app/hub'
./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
~~~

**Đạt khi** các test cần thiết đã chạy đủ và qua. Nếu thiếu DB test, LFW hoặc ảnh thử, ghi Thiếu điều kiện cho phần bị bỏ qua. Phiên 16/11 có lỗi kết nối DB trong môi trường chạy cũ, cần lấy kết quả lượt mới.

## FG-070 — Playwright đăng nhập, phiên và nhân viên

**Người chạy** Codex hoặc người thao tác terminal.

1. Tại thư mục Web, chạy cấu hình Playwright mặc định.
2. Xem summary, trace/ảnh lỗi nếu có.
3. Ghi số ca đạt/lỗi và tên từng ca lỗi để xử lý.

~~~powershell
Set-Location 'D:/WorkSpace/DATN/datn-facegate-app/03-app/web'
node node_modules/@playwright/test/cli.js test
~~~

**Đạt khi** máy chủ test khởi động và toàn bộ ca cấu hình mặc định chạy đạt. Cấu hình này chọn auth.spec.ts, employees.spec.ts, session.spec.ts và dùng API giả lập trong các ca tương ứng. Các luồng với Hub/DB thật tiếp tục đối chiếu bằng các ca thủ công phía trên.

## Sau khi đi hết bảng

1. Lọc Lỗi, ghi đủ cách tái hiện và bằng chứng.
2. Lọc Thiếu điều kiện, bổ sung Kiosk/model/dữ liệu/phần cứng tương ứng và quay lại đúng mã ca.
3. Hoàn tất phần OUT của FG-051 khi đủ thời gian, cùng các mục duyệt/xóa đã chờ dữ liệu.
4. Ghi đợt chạy, ngày giờ, phiên bản đang test và người test để lần kiểm lại truy vết được.

## Nguồn đối chiếu

- Bản checklist 70 dòng đã tải lên Drive, đối chiếu nội dung gốc từ builder của phiên tạo bảng. Bảng được tải lên ngày 18/11 có kết quả tự động từ ngày 16/11.
- 03-app/KICH-BAN-TEST-WEB.md cho tài khoản demo, quy trình Web và dữ liệu ví dụ.
- 03-app/dac-ta-app.md phiên bản 1.4.5, đặc biệt §0a, §5.5–5.9 và §6.
- 03-app/web/src/admin/AdminArea.tsx và src/me/MeArea.tsx cho tên menu và phạm vi màn hình.
- 03-app/web/src/admin/schedules/SchedulesPage.tsx cùng hub/app/api/schedule.py cho giới hạn ca trong ngày.
- 03-app/ket-qua-kiem-thu/2026-11-16_T13/RUN-T13.md và 2026-11-16_T14/RUN-T14.md cho hiệu chỉnh/đo thiết bị.
- Mã nguồn và test hiện có của Hub/Web/Kiosk. Hướng dẫn này chưa xác nhận kết quả của đợt test mới.
