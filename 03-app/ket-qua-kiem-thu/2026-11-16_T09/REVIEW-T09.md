# Kịch bản review T09

## Chạy kiểm tra độc lập

Mở PowerShell ở thư mục dự án. PostgreSQL và `.env` local cần sẵn sàng. Script tạo DB mới, không sửa DB demo:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app
$env:PYTHONUTF8 = '1'
& .\03-app\hub\.venv\Scripts\python.exe .\03-app\hub\scripts\verify_t09.py --all
```

Kỳ vọng: alembic/seed/pytest exit=0. Xem tên từng test trong `pytest.log`. Nếu muốn chạy lại nhanh riêng T09 trên DB kiểm vừa tạo, dùng `verify_t09.py --resume`.

## Các điểm cần đối chiếu

1. `test_status_grace_rounding_and_break_overlap`: 08:40 trong grace 10 phút → không muộn; 08:41 → 11 phút muộn. Ca 08:30–17:30 nghỉ 12–13h, vào sớm/ra muộn vẫn tối đa 480 phút. Mốc so sánh giữ cả giây.
2. Trước ca chưa vào → NOT_STARTED; từ giờ vào chưa quét → WAITING_IN; đã vào nhưng trước chốt → IN_PROGRESS. Đến 21:30 mới kết luận ABSENT/MISSING_OUT hoặc nhóm đủ giờ.
3. Vào 08:30, ra 12:00 → MISSING_OUT, cờ nghi quên quét; không biến thành về sớm. Ca cá nhân thắng ca phòng ban; event ngoài cửa sổ hoặc MATCH ở ACCESS_ONLY không tính công.
4. Test recompute: hai lần không đổi; giờ ra nhận muộn cập nhật ngày đã chốt nhưng finalized giữ true. Sửa MANUAL/nghỉ LEAVE không bị event hoặc job ghi đè. Thêm lễ rồi bỏ lễ giữ được ý định nghỉ.
5. API quyền: tự sửa/tự chấm hộ/tự duyệt đều bị server chặn; quản lý chỉ xem/xuất team. Chấm hộ phải MANUAL, ACTIVE, cửa chấm công, lý do và giờ hiện tại.
6. Giải trình: tạo PENDING, lần hai bị 409; thiếu giờ/lý do sai bị chặn; duyệt áp giờ và ADJUSTED, từ chối không áp giờ; chỉ hủy PENDING của mình; không xử lý lại. Đối chiếu các test chuyển cấp Q-011, kể cả nhiều vai trò.
7. Mở `bang-cong-2026-11-test.xlsx`: đúng hai sheet Tổng hợp/Chi tiết, cột theo skill, ngày/giờ là kiểu Excel, NV006 có 1 ngày công và 11 phút muộn. Tên `=FORMULA_TEST` là chuỗi kiểm chống công thức, không phải nhân viên thật.
8. Test MATCH → IN/OUT và scheduler: event và công được ghi cùng transaction; job có run_date đúng 21:30 cho ca kết thúc 17:30.

T10 cung cấp giao diện để review các luồng thao tác này bằng trình duyệt; T09 hiện nghiệm thu lớp backend. Không dùng fixture test làm số đo người thật hoặc nhận dạng.
