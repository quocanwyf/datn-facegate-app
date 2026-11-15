# Kịch bản review T05

T05 kiểm backend bằng Kiosk giả lập; UI Kiosk/duyệt hồ sơ hoàn chỉnh ở T07/T08. Các log nghiệm thu đã có, không cần chạy lại để tiếp tục T06.

## 1. Xem kết quả đã chạy

- `real-run-03/summary.json`: 5 mẫu, 17 phản hồi NO_GALLERY, 1 OK, 2 ALREADY, 1 DENY/UNKNOWN; chỉ 2 event.
- `real-run-03/events.json`: MATCH có score/model/ngưỡng/3 khung, không snapshot; UNKNOWN 5 khung có crop.
- `real-run-03/resilience-summary.json`: ngắt 4 mẫu/lỗi ghi giữ hồ sơ cũ, SUSPENDED không mở cửa, xóa lỗi vẫn thu hồi consent, retry hoàn tất.
- `pytest-full.log`: 66 test đạt, chỉ skip màu T02 chưa có LFW. Không có ảnh/token trong log.

## 2. Tự chạy lại tại máy Hy

PowerShell mở tại repo, PostgreSQL 16 cổng 5433 đang chạy như T00. Script tạo **DB thử mới** và thư mục dữ liệu ngoài repo mỗi lần, không reset DB demo.

```powershell
Set-Location 03-app/hub
$env:PYTHONUTF8 = '1'
$ReviewOutput = '../ket-qua-kiem-thu/' + (Get-Date -Format 'yyyy-MM-dd') + '_T05/review-' + (Get-Date -Format 'HHmmss')
& .venv/Scripts/python.exe scripts/review_t05.py --known-dir D:/WorkSpace/DATN/U03 --unknown-dir D:/WorkSpace/DATN/U04 --output $ReviewOutput
```

Mong đợi: mẫu nghiêng quá bị POSE, accepted không tăng; đủ 5 mẫu mới enroll_done/PENDING. Script duyệt tạm trong DB bằng HR khác người đăng ký (đúng bước T05), restart để nạp gallery, gửi lại ảnh ra OK/ALREADY. Ảnh U04 ra UNKNOWN, không OK. Script đọc HEIF/JPG thành JPEG trong RAM, không chép ảnh vào repo.

Để kiểm thêm lỗi/đăng ký lại/xóa, Codex đã chạy `review_t05_resilience.py` với môi trường DB và HUB_DATA_DIR của lượt tương ứng; log có sẵn. Không chạy trực tiếp script đó với `.env` DB demo.

## 3. Review thủ công khóa IP

Mở Hub bằng lệnh dưới nếu chưa có instance ở cổng 8000:

```powershell
& .venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers
```

Tạo thiết bị qua POST /api/v1/devices bằng tài khoản OWNER để nhận mã 6 số. Gửi mã không đúng từ cùng IP: 4 lần đầu PAIRING_INVALID/404, lần 5 PAIRING_LOCKED/429. Trong 10 phút IP đó bị khóa cả khi nhập đúng; IP khác vẫn thử được. Đúng hạn 10 phút cho thử lại. Mã vẫn tự hết hạn sau 10 phút từ lúc cấp nên có thể cần tạo mã mới. Thông báo nói khóa lượt thử từ máy này, không nói mã bị khóa.

PIN HR/OWNER là luồng riêng: 5 sai khóa 15 phút, bộ đếm ở DB. Mã ghép/token/PIN không đưa vào log chia sẻ. Hub demo chạy một tiến trình; bộ đếm IP ở RAM, khởi động lại sẽ reset lượt thử IP.
