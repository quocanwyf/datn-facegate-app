# Rà Web Interface Guidelines — T07

- Nguồn đã lấy lại ngày 15/11/2026: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
- Skill: `.agents/skills/web-design-guidelines/SKILL.md`; kết hợp React Best Practices, gsap-core, gsap-react của repo. Playwright skill từ openai/skills đã được bỏ theo quyết định T00; E2E dùng thư viện Playwright đã cài, không nhận đã chạy skill đó.
- Phạm vi: `web/src/App.tsx`, `admin/**`, `components/**`, `shared/**`, CSS, theme; ảnh render thật của W01/W03/W04/W05/W07/W08/W14/W16.

## Các điểm đã sửa/kiểm

- `src/admin/AdminArea.tsx` — thêm skip link, main có đích focus; điều hướng bằng React Link, aria-current và tên truy cập; Drawer dưới 1024 px. Không tải lại trang khi bấm điều hướng.
- `src/App.tsx` — nhãn email/mật khẩu, autocomplete đúng mục đích, tắt spellcheck email, lỗi validation cuộn tới trường đầu, chống gửi lặp; có nút hiện/ẩn mật khẩu bằng bàn phím.
- `src/admin/**` — trạng thái tải, trống, lỗi/thử lại và 403; nút ghi bị khóa khi chờ; lỗi Hub giữ biểu mẫu; thao tác nghỉ việc/xóa sinh trắc/thu hồi/reset có xác nhận.
- `src/shared/useFormExitWarning.ts` — cảnh báo đóng/tải lại tab khi form đang có chỉnh sửa chưa lưu; tự gỡ listener khi unmount.
- `src/components/FaceImages.tsx` — ảnh có alt và kích thước 224×224, chỉ đọc qua API đã xác thực; có timeout, abort và thu hồi object URL khi unmount.
- `src/components/AnimatedTable.tsx`, `admin/AdminArea.tsx` — GSAP có scope/cleanup, chỉ transform/opacity, 280 ms chuyển trang và 180 ms/stagger 20 ms tối đa 10 dòng, tôn trọng reduced motion.
- `src/theme/**` — màu lấy từ token, nhãn trạng thái từ status.json; 30 token toàn cục/10 component khớp type AntD đã cài, không cần bỏ token nào. Font Inter/Be Vietnam Pro có Vietnamese + Latin.
- `src/admin.css` — focus-visible, min-width cho nội dung, cuộn ngang bảng, ngắt dòng nội dung dài và overscroll contain cho modal/drawer.
- `src/App.tsx` — tách tải AdminArea bằng lazy/Suspense để đăng nhập không tải toàn bộ giao diện quản trị. Build hiện index 593,45 kB / AdminArea 868,59 kB; vẫn có cảnh báo chunk >500 kB, không che cảnh báo.

## Kiểm render

Đã nhìn trực tiếp W05 phòng ban/tài khoản, W07 cửa, W08 mẫu đã che, W14 cấu hình. Phát hiện ảnh W05 chụp giữa animation làm dòng mờ; đã sửa helper chụp chờ opacity/transform ổn định, chạy lại bộ thật 10/10 và chụp lại. Mask áp từng ảnh mẫu, giữ bố cục 5 ảnh và chú thích; không dùng ảnh giả thay cho mặt thật.

## Phần theo task tiếp

URL bộ lọc/tab chưa đồng bộ toàn bộ query string; sẽ giữ nhất quán khi hoàn thiện các màn T10–T12. Tab Ca/Công/Event W04 và vùng events/realtime Dashboard phụ thuộc T09–T11; không nhận đã nghiệm thu các phần đó trong T07. Không đánh dấu các spec liên quan hoàn thành chỉ vì đã có menu.
