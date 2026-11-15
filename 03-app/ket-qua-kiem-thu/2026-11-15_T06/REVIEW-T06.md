# Kịch bản review T06

T06 là API quản trị; các trang web tương ứng làm ở T07. Có thể xem log trước, không cần chạy lại để tiếp tục.

1. Mở `pytest-full.log`: 87 test đạt; một test màu T02 skip vì chưa có LFW.
2. Mở `contract-tests.log`: 48 operation cài thật, 29 operation chấm công/sự kiện để T09/T11, có danh sách đầy đủ.
3. Mở `real-run-03/summary.json`: OWNER/HR xem 5 ảnh có quyền; hai request duyệt đồng thời trả một 200/một 409; lỗi xóa vẫn rút consent; retry sạch file/dòng; terminate gallery 1→0; NV tự rút consent chỉ ảnh hưởng mình.
4. Mở `SECURITY-REVIEW.md`: hai race đã sửa. `concurrent_suspend_waits_for_real_match_commit=true` là ca ảnh thật, không dùng event giả.

Kiểm client sau khi pull, PowerShell tại repo:

```powershell
Set-Location 03-app/web
pnpm install
pnpm gen:api
pnpm typecheck:api
Set-Location ../kiosk
pnpm install
pnpm gen:api
pnpm typecheck
```

Nếu terminal cũ chưa nhận pnpm, dùng `& "$env:APPDATA/npm/pnpm.cmd"` thay `pnpm`, hoặc mở terminal mới. T06 mới tạo client kiosk, chưa có màn Expo để mở.

Để chạy lại kiểm sinh trắc **tại máy Hy đã setup T00**, mở PowerShell trong repo:

```powershell
Set-Location 03-app/hub
$env:PYTHONUTF8 = '1'
$Output = '../ket-qua-kiem-thu/' + (Get-Date -Format 'yyyy-MM-dd') + '_T06/review-' + (Get-Date -Format 'HHmmss')
& .venv/Scripts/python.exe scripts/review_t06.py D:/WorkSpace/DATN/U03 $Output
```

Script tạo DB thử và HUB_DATA_DIR riêng ngoài repo, dùng ảnh thật đã cung cấp; không reset DB demo, không ghi ảnh/token vào log. Chỉ chạy khi PostgreSQL 16 cổng 5433 và file quản trị local của T00 còn sẵn. Không chia sẻ thư mục ảnh/biometrics hoặc `.env` lên Git.
