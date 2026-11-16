# Review T12 thủ công

Làm việc tại `D:\WorkSpace\DATN\datn-facegate-app`. Đây là bản review riêng; T08 gốc được giữ nguyên.

## Mở Hub và web

Nếu dịch vụ đang chạy thì chỉ mở trình duyệt. Khi khởi động lại, mở hai cửa sổ PowerShell:

```powershell
cd D:\WorkSpace\DATN\datn-facegate-app\03-app\web\tests
$env:PYTHONUTF8='1'
& ..\..\hub\.venv\Scripts\python.exe .\start_t12_hub.py --resume
```

```powershell
cd D:\WorkSpace\DATN\datn-facegate-app\03-app\web
$env:FACEGATE_HUB_URL='http://127.0.0.1:8012'
& "$env:APPDATA/npm/pnpm.cmd" dev --port 5173
```

Mở `http://127.0.0.1:5173/me`. Tài khoản demo `nv006@demo.local` / `Demo@123`. Phiên nằm trong bộ nhớ: refresh trang sẽ yêu cầu đăng nhập lại.

`--resume` chỉ dùng trên máy đã có context T12. Muốn thử lại xóa từ đầu, dừng Hub T12 và mọi Hub dùng DB T08 rồi chạy helper không có `--resume`: tạo DB/kho T12 mới từ T08, không xóa clone cũ. Không chạy thao tác revoke trên DB T08 gốc. Clone T12 hiện tại đã rút consent NV006 thành công nên sẽ hiện MANUAL/chưa đồng ý.

## Kịch bản từng chức năng

1. **Hôm nay:** kiểm lời chào, ngày, ca, hai ô giờ; WAITING_IN/IN_PROGRESS có nhãn tạm thời. Cửa ACCESS_ONLY ghi không tính công. Nút làm mới/kéo xuống tải lại, không tạo lượt mới.
2. **Bảng công:** chuyển tháng bằng hai nút; mở chú giải, chạm một ngày → đúng ngày đó. Kiểm nguồn công/phút/cờ quên ra; PENDING ẩn nút gửi mới. Tổng tháng không cộng thêm ngày theo số giải trình.
3. **Gửi giải trình:** chọn ngày và loại; FORGOT_IN cần giờ vào, FORGOT_OUT cần giờ ra, lý do bắt buộc. Giờ ra trước giờ vào bị chặn. Gửi thành công về danh sách chờ; gửi trùng pending báo lỗi và giữ lý do.
4. **Giải trình của tôi:** chuyển Chờ duyệt/Đã xử lý; hủy bản pending có xác nhận. Bản đã xử lý không có nút hủy, hiển thị ghi chú người duyệt.
5. **Khuôn mặt:** không có ảnh mẫu. Với clone mới có dữ liệu, xác nhận rút đồng ý; chỉ báo thành công khi xong, sau đó MANUAL/chưa đồng ý. Nếu gặp xóa chưa hoàn tất thì thử lại trong hộp thoại.
6. **Duyệt (MANAGER):** đăng xuất qua avatar → đăng nhập `nv005@demo.local` / `Demo@123`, chọn Trang cá nhân. Có tab thứ năm; không có giải trình chính mình. Duyệt/xem giờ đề nghị và giờ thực tế; từ chối thiếu ghi chú bị chặn. Danh sách có thể trống nếu chưa có người đúng cấp gửi yêu cầu; không seed giả vào dữ liệu review.
7. **Tài khoản:** avatar → Đổi mật khẩu/Đăng xuất; người có quyền quản trị có mục Chọn không gian. Quản trị không gắn employee mở `/me` sẽ về admin.

## Bước Android còn chờ

Trong Chrome của máy ảo Android, mở `http://10.0.2.2:5173/me`, đăng nhập tài khoản demo trên. Chuyển bốn tab, kiểm thanh dưới và form không tràn. Chụp ít nhất Hôm nay và một form; lưu vào thư mục `screens` của báo cáo này, ghi thiết bị/độ phân giải/thời điểm vào báo cáo. Chỉ sau khi xác nhận mới đánh dấu AC5 đạt. Người dùng đã chọn kiểm tra bước này sau; không cần bật chống giả mạo.

## Chạy lại kiểm thử

Tại thư mục web:

```powershell
& "$env:APPDATA/npm/pnpm.cmd" exec playwright test --config playwright.me.config.ts
& .\..\hub\.venv\Scripts\python.exe .\tests\verify_t12_db.py
& "$env:APPDATA/npm/pnpm.cmd" run build
& "$env:APPDATA/npm/pnpm.cmd" run lint
```

Test PostgreSQL cần context DB test từ verify_t11.py và tự rollback. Test `playwright.me-real.config.ts` có thao tác rút consent, cần **clone T12 mới**, chạy `check_t12_revoke.py before` trước; helper after kiểm T08 gốc không đổi. Không chạy lại test xóa trên nguồn T08.
