# T13 — Chống giả mạo và hiệu chỉnh L

**Trạng thái: đã triển khai phần mềm, chưa đủ nghiệm thu/không archived.** Người dùng xác nhận chưa có bộ dữ liệu 4 nhóm; máy Codex là máy dự định dùng GPU. Máy thực tế hiện chỉ báo Intel UHD/PyTorch CPU, xem báo cáo T14.

## Đã làm

- Lấy Silent-Face từ nguồn chính thức, ghim b6d5f04ad78778917853b25c778acef6d5626d15; LICENSE Apache-2.0 gốc, hai trọng số và SHA-256 riêng. [Đối chiếu nguồn](../../hub/vendor/silentface/NGUON.md). Giữ nguyên 33 file vendor T01 và checkpoint nhận dạng.
- Crop 2.7/4.0→80×80, BGR CHW float32 0–255 theo mã upstream, ensemble softmax lấy class1. Parity độc lập dùng tensor/crop/network gốc; ảnh test tổng hợp chỉ kiểm phép tính, không phải ground truth PAD.
- Nối p_live vào quyết định và mẫu đăng ký; nonlive không embed/nhận mẫu, SPOOF có ưu tiên và crop cảnh báo theo giao thức cũ. Tắt cờ giữ luồng cũ, gallery rỗng vẫn NO_GALLERY.
- Chủ DN bật qua API/web chỉ khi marker phê duyệt riêng khớp L, bundle và policy. Marker chưa tồn tại cho triển khai này; không tự chốt L hoặc bật cờ. HR chỉ xem.
- Cổng commit kiểm policy hiện hành + khóa Company; đổi policy bỏ bộ gom mẫu cũ. Header JPEG được kiểm kích thước trước giải mã pixel. [Security review](../2026-11-16_T14/SECURITY-REVIEW.md).
- Script collect/calibrate/approve; bộ quay trống bên ngoài repo đã tạo tại D:\WorkSpace\DATN\facegate-private\T13-20261116. Consent mặc định false, không tự mở webcam/quay người.

## Đối chiếu AC

| AC | Kết quả |
|---|---|
| 1. LICENSE/nguồn | Đạt phần nguồn/byte-check/parity. |
| 2. Phân phối p_live/tỷ lệ 4 nhóm và L | **Chưa có dữ liệu thật**, chưa có bảng tỷ lệ/chưa đề xuất hay chốt L. CLI không tạo calibration-real.json khi metadata/dữ liệu thiếu; empty-data-gate.log. |
| 3. Cờ tắt hoạt động | Đạt regression và CPU WS smoke với 1/3 kiosk trên DB clone riêng. |
| 4. Video kiosk DENY/SPOOF | **Chưa quay**. Test kiểm đường điều khiển không thay video camera thật. |

Kiểm backend cuối **150 passed, 2 skipped, 1 warning / 108,48 giây** trong **pytest-full.log** (DB T13 riêng), web cấu hình **2/2** (browser-settings.log), production build và ESLint đạt. Hai skip LFW/webcam riêng của bộ cũ, warning Starlette/httpx; Vite còn cảnh báo chunk >500kB. Log lần vướng inventory vendor cũ và fixture dashboard được giữ riêng; định dạng 0.70 đã được sửa trong test, không sửa format sản phẩm để chiều fixture sai.

Không có ảnh/video tình nguyện viên trong repo. Chưa chạy thành công toàn bộ calibrate/approve với dataset camera thật; marker ở pytest chỉ là fixture tmp_path, không sao chép sang Hub. Đường tiếp tục và lệnh quay/hiệu chỉnh/chốt: **[RUN-T13.md](RUN-T13.md)**.
