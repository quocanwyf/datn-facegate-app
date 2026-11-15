# Kịch bản review T07 — Web quản trị

## Mở thủ công trên máy Hy bằng DB kiểm thử riêng

Không cần pnpm có trong PATH. Terminal 1, PowerShell:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app
$env:PYTHONUTF8 = '1'
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
& .\03-app\hub\.venv\Scripts\python.exe .\03-app\web\tests\start_real_hub.py D:/WorkSpace/DATN/U03
```

Script tạo DB mới, chạy migration + seed, dùng ảnh JPG thật để đăng ký hồ sơ NV006 rồi mở Hub tại port 8007. Chờ `T07_READY`. Script cần PostgreSQL 16 của T00, `.env` cục bộ và file mật khẩu quản trị PostgreSQL trong AppData. Không thay DB `facegate_dev`. Nếu port 8007 đang chạy lượt cũ: Ctrl+C ở terminal đó trước khi mở lượt mới. Giữ terminal này mở.

Terminal 2:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app\03-app\web
$env:FACEGATE_HUB_URL = 'http://127.0.0.1:8007'
& "$env:APPDATA/npm/pnpm.cmd" dev --port 5177
```

Mở http://127.0.0.1:5177/login. Đây là dữ liệu demo tách riêng: tên/mã theo seed, ảnh U03 được gắn NV006 chỉ để kiểm luồng, không phải xác nhận danh tính của người trong ảnh.

## Tài khoản demo

Mật khẩu chung do seed: `Demo@123`.

| Vai trò | Email | Cần thấy |
|---|---|---|
| OWNER | nv001@demo.local | Đủ mục quản trị, có Nhật ký |
| HR | nv002@demo.local | Không có Nhật ký; cấu hình chỉ xem; cửa chỉ sửa policy/phòng ban |
| SECURITY | nv020@demo.local | Giám sát, Sự kiện |
| MANAGER | nv005@demo.local | Nhân viên team, Bảng công, Giải trình, Sự kiện; không có thao tác ghi NV |
| EMPLOYEE | nv008@demo.local | `/me`; vào URL quản trị bị 403 |

Đăng xuất qua menu góc phải để đổi tài khoản. Tải lại trang sẽ yêu cầu đăng nhập lại; phiên đang mở có refresh tự động.

## Các bước review và kết quả mong đợi

1. **Đăng nhập:** bỏ trống/sai định dạng → lỗi ngay tại ô; mật khẩu sai → lỗi Hub; đăng nhập đúng → chọn không gian hoặc vào `/me`. Dùng Tab/Enter được; hiện/ẩn mật khẩu không gửi form.
2. **Nhân viên:** xem 20 người/trang, tìm tên/mã, kết hợp bộ lọc. Thêm nhân viên mới, chọn tạo tài khoản: mật khẩu tạm hiện một lần. Sửa không thay mã. Tạm khoá/mở khoá cập nhật pill. Hủy nghỉ việc không đổi dữ liệu; xác nhận mới xóa sinh trắc.
3. **Chi tiết NV006:** kiểm thông tin, đồng ý sử dụng khuôn mặt và 5 ảnh thật ở tab Khuôn mặt. Chưa xóa ở bước này để còn review duyệt.
4. **Phòng ban:** thêm, đổi tên, thử nhập tên đã có → 409, hộp thoại giữ dữ liệu để sửa. Tab Tài khoản: thêm/sửa vai trò; MANAGER bắt buộc phòng ban; có thể thêm nhiều dòng phạm vi. HR không có nút sửa OWNER. Đặt PIN đúng 4 số cho OWNER/HR; đặt lại mật khẩu có xác nhận và chỉ hiện mật khẩu tạm một lần.
5. **Đổi mật khẩu lần đầu:** dùng tài khoản vừa tạo ở bước 2 hoặc 4 → buộc đổi trước khi vào trang nghiệp vụ; nhập lại không khớp bị chặn; đổi xong đăng nhập lại bằng mật khẩu mới.
6. **Cửa & thiết bị:** OWNER tạo/sửa cửa, đổi mức mặc định/nghiêm ngặt/tùy chỉnh, thấy số cos và nguồn. Thêm thiết bị → có QR, mã 6 số, Hub, đếm ngược 10 phút; đóng không làm lộ device token. Thu hồi thiết bị cần xác nhận. HR chỉ đổi chính sách/phòng ban, không có thao tác thiết bị hoặc ngưỡng.
7. **Xác nhận khuôn mặt:** chọn NV006, xem 5 mẫu và điểm phát hiện/độ nghiêng. Từ chối phải có ghi chú; hồ sơ nghi trùng cần ghi chú khi xác nhận. Xác nhận thành công → hàng chờ hết hồ sơ, gallery tăng. Tab khác xử lý cùng hồ sơ nhận 409; không tự báo thành công khi Hub trả 503.
8. **Cấu hình nhận dạng:** thấy nhãn validation/test, bảng FPIR/FNIR và ghi chú chưa đo tại văn phòng. Đặt W nhỏ hơn ngưỡng đếm → không cho gửi. Lưu giá trị hợp lệ cần xác nhận; Kiosk đang kết nối nhận config. Liveness/L bị khóa tới T13. HR không có nút Lưu.
9. **Nhật ký:** OWNER xem/lọc hành động, người thực hiện và thời gian, phân trang và mở detail. Tài khoản khác không có menu, vào URL trực tiếp bị 403.
10. **Xóa sinh trắc:** sau review duyệt, mở NV006 → Khuôn mặt → Xóa → xác nhận. Sau API thành công: MANUAL, không còn mẫu/template trong gallery; lịch sử vẫn giữ. Nếu lỗi phải hiện lỗi và cho thử lại.

## Phạm vi các task tiếp theo

Ca/lịch/bảng công/giải trình ở T09–T10; giám sát/sự kiện và event realtime ở T11; nội dung `/me` ở T12. W04 hiện dẫn đến các mục này, chưa phải nghiệm thu các bảng lịch sử đó. Dashboard chưa có REST events trước T11 nên vùng 10 sự kiện có nhánh tải lỗi/thử lại; không đưa event giả vào để lấp màn hình.

## Chạy tự động với Hub thật

Giữ Terminal 1 ở trạng thái mới, chưa bấm duyệt hay tạo dữ liệu review. Dừng Vite Terminal 2 vì Playwright tự mở port 5177, rồi chạy:

```powershell
& "$env:APPDATA/npm/pnpm.cmd" exec playwright test --config playwright.real.config.ts
```

Mỗi lượt đầy đủ dùng DB mới vì các test tạo phòng ban/duyệt hồ sơ có trạng thái. Ảnh chụp lưu tại `screens/`, che khuôn mặt bằng mask của trình duyệt. Không đưa ảnh gốc, template, token, trace hoặc video vào Git.
