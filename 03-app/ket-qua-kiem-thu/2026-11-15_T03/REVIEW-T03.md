# Kịch bản review T03 — Hub và phiên đăng nhập

T03 là backend. Trang nhân viên/quản trị hoàn chỉnh sẽ nối trong T06–T12. Mở PowerShell tại repo. Nếu Hub chưa chạy, dùng một cửa sổ riêng:

```powershell
Set-Location 03-app/hub
$env:PYTHONUTF8 = '1'
& .venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Trong cửa sổ khác, chạy lần lượt. Không chia sẻ nội dung biến chứa token.

```powershell
$Hub = 'http://127.0.0.1:8000/api/v1'
Invoke-RestMethod "$Hub/health"
# Mong đợi db=True; degraded, model_verified=False khi pipeline chưa bật.
$Pair = Invoke-RestMethod "$Hub/auth/login" -Method Post -ContentType 'application/json' -Body (@{email='nv001@demo.local';password='Demo@123'} | ConvertTo-Json)
$Pair.user
# Mong đợi NV001, OWNER + EMPLOYEE. expires_in = 900.
$Headers = @{Authorization=('Bearer ' + $Pair.access_token)}
Invoke-RestMethod "$Hub/me" -Headers $Headers
$Next = Invoke-RestMethod "$Hub/auth/refresh" -Method Post -ContentType 'application/json' -Body (@{refresh_token=$Pair.refresh_token} | ConvertTo-Json)
# Token cũ: lệnh sau phải báo HTTP 401.
Invoke-RestMethod "$Hub/auth/refresh" -Method Post -ContentType 'application/json' -Body (@{refresh_token=$Pair.refresh_token} | ConvertTo-Json)
```

Tiếp tục đăng xuất và kiểm token đã thu hồi:

```powershell
$Headers = @{Authorization=('Bearer ' + $Next.access_token)}
Invoke-RestMethod "$Hub/auth/logout" -Method Post -Headers $Headers -ContentType 'application/json' -Body (@{refresh_token=$Next.refresh_token} | ConvertTo-Json)
# Logout 204 không nội dung; refresh sau phải 401.
Invoke-RestMethod "$Hub/auth/refresh" -Method Post -ContentType 'application/json' -Body (@{refresh_token=$Next.refresh_token} | ConvertTo-Json)
```

Test tự động còn kiểm đổi mật khẩu, thu hồi tất cả phiên, thiếu quyền của từng vai trò, thay quyền/khóa tài khoản có hiệu lực với access token đang giữ, phạm vi MANAGER và WAITING_IN. Kết quả ở pytest.log; test dùng DB riêng và rollback, không đổi mật khẩu DB demo.
