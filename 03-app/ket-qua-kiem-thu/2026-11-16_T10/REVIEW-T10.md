# Kịch bản review T10

## Mở thủ công

Nếu Hub review 8010 đang chạy, dùng lại. Để mở một phiên review mới, Terminal 1 tại thư mục gốc:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app
$env:PYTHONUTF8 = '1'
& .\03-app\hub\.venv\Scripts\python.exe .\03-app\web\tests\start_t10_hub.py
```

Script tạo DB riêng từ seed, không sửa DB demo. Lần sau dùng `--resume` để giữ dữ liệu review. PostgreSQL cần đang chạy và cấu hình `.env` local hợp lệ.

Terminal 2:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app\03-app\web
$env:FACEGATE_HUB_URL = 'http://127.0.0.1:8010'
& "$env:APPDATA\npm\pnpm.cmd" dev --port 5181
```

Mở http://127.0.0.1:5181/login. Owner `nv001@demo.local`, HR `nv002@demo.local`, Manager `nv005@demo.local`; mật khẩu demo `Demo@123`. Chọn **Trang quản trị**. Scheduler quét bù công từ phân ca seed, không thêm event nhận dạng.

## Review từng chức năng

1. **Ca & lịch → Ca:** thêm ca 08:30–17:30, nghỉ 12:00–13:00, grace 10 phút; lưu, sửa. Thử 22:00–06:00 hoặc dài hơn 17h: không lưu, form giữ dữ liệu/lỗi.
2. **Phân ca:** chọn Nhân viên NV009, chọn thứ và khoảng hiệu lực, thêm một ca. Kiểm chip đúng cột thứ, đúng khoảng ngày. Tạo lần nữa cùng thứ/khoảng: thông báo phân ca trùng tiếng Việt, modal vẫn mở. Hủy rồi xóa chip đã tạo. Ca cá nhân có ưu tiên hơn phòng ban ở backend.
3. **Ngày lễ:** thêm một ngày ở năm khác, kỳ vọng danh sách tự sang đúng năm. Xóa lại ngày vừa tạo.
4. **Bảng công:** chọn tháng/phòng ban, tìm NV. Ký hiệu C là “Chưa đến — tạm thời”, … là “Đang làm việc — tạm thời”; trước chốt không hiện Vắng. Rê ô xem nhãn đầy đủ; bấm ô xem Drawer. Giờ trống là —. Cuộn ngang để xem ngày cuối và tổng.
5. **Tự bảo vệ:** Owner mở ô NV001 của mình: không có nút Sửa. Mở ô NV006: có Sửa, bắt buộc lý do. Manager không có Sửa hoặc Đánh dấu nghỉ. API cũng chặn quyền, không chỉ giao diện.
6. **Nghỉ phép:** Owner/HR chọn NV và một/nhiều ngày, nhập lý do, lưu. Lưới đổi theo kết quả API; event hoặc job tính lại không ghi đè nghỉ đã đánh dấu.
7. **Excel:** tải file, kiểm tên `bang-cong-YYYY-MM.xlsx`, hai sheet Tổng hợp/Chi tiết, ngày/giờ đọc được. Manager không chọn phòng ban vẫn chỉ xuất team; thử sửa department_id ngoài quyền bị server chặn.
8. **Giải trình:** với dữ liệu tạo qua trang nhân viên ở T12 hoặc API `/me/requests`, xem chờ/đã xử lý. Chỉ người đúng cấp thấy Duyệt/Từ chối. Tự gửi không có nút tự duyệt. Từ chối thiếu lý do không gửi; duyệt xong có thông báo và công được tính lại. Pending chưa có người đúng cấp không tự được duyệt.
9. **Đường dẫn tiếp theo:** Lịch sử sự kiện trong Drawer dẫn sang W11 (T11); trang cá nhân và E10 hoàn thiện ở T12.

## Chạy test có sẵn

Ở `03-app/web`:

```powershell
& "$env:APPDATA\npm\pnpm.cmd" exec playwright test --config playwright.attendance.config.ts
# Cần Hub review 8010 chạy trước:
& "$env:APPDATA\npm\pnpm.cmd" exec playwright test --config playwright.attendance-real.config.ts
& "$env:APPDATA\npm\pnpm.cmd" build
& "$env:APPDATA\npm\pnpm.cmd" lint
```

Fixture test chỉ kiểm UI, không là bằng chứng nhận dạng hay công thật. Bài Hub thật tạo dữ liệu review qua API/UI trong DB riêng; các phân ca/ngày lễ được xóa lại sau khi kiểm.
