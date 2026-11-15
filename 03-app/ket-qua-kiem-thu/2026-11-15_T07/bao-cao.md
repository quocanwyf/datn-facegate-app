# Báo cáo T07 — Web nền và quản trị lõi

- Trạng thái: **XONG phạm vi T07**; các phần ca/công/event/realtime theo task T09–T12 ghi rõ bên dưới.
- Commit code: `eb13891`.
- Máy: Windows, CPU. Môi trường chuyển sang `D:/WorkSpace/DATN/datn-facegate-app`; Node 24.15.0, pnpm 11.25.0, Python 3.13.13, torch 2.11.0+cpu, FastAPI 0.163.0. Runtime thật trong `real-hub-final.log`, build trong `build.log`.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log/bằng chứng | Đạt? |
|---|---|---|---|---|
| 1 | pnpm typecheck, pnpm lint sạch | Hai lệnh exit 0; build exit 0 | typecheck.log, lint.log, build.log | Đạt |
| 2 | Playwright pass, ảnh mọi màn | **33/33 fixture + 10/10 Hub thật**, 28 PNG | playwright-regression-final.log, playwright-real-final.log, screens/ | Đạt |
| 3 | Font tiếng Việt có dấu | Kiểm document.fonts Inter/Be Vietnam Pro và ảnh chữ có dấu trên desktop/360/390/430 px; menu mở rộng có Bảng công/Giải trình | tests/auth.spec.ts, tests/admin-real.spec.ts, screens/ | Đạt |
| 4 | Không hex ngoài theme | rg rỗng | hex-scan.log | Đạt |
| 5 | Rà web-design-guidelines | Đã rà/sửa focus, nhãn, Link, ảnh, trạng thái, reduced motion, chờ animation khi chụp | WEB-DESIGN-REVIEW.md | Đạt |
| Q001 | HR W07 policy/departments, W14 chỉ xem | PATCH HR chỉ có default_policy, PUT departments thành công, form owner-only khóa, W14 không có Lưu, HR không sửa OWNER | playwright-real-final.log | Đạt |
| Q007 | Cấu hình nguyên khối, W/counts/L | 7 request sai nhận 422 và giữ nguyên toàn bộ; mặc định 5/3/4/3; OWNER lưu và Kiosk thật nhận WS config | real-final-checks.json, playwright-real-final.log | Đạt |
| Q012 | KPI timezone, events page=1/size=10 | Dùng date và KPI từ API đã kiểm T06; events client gửi đúng page=1&size=10. API event chờ T11, hiện nhánh lỗi/thử lại | src/admin/dashboard/DashboardPage.tsx, T06 dashboard tests | Đạt phần client T07; event end-to-end ở T11 |

## Đã làm

Theme Canopy, shell theo quyền, PageHero/StatusPill/KpiTile, font Vietnamese, GSAP theo nguồn. Đăng nhập/đổi mật khẩu/chọn không gian/refresh một lượt cho request đồng thời/logout; phiên chỉ trong bộ nhớ tab, tải lại cần login.

W03 quản lý nhân viên; W04 thông tin và sinh trắc; W05 phòng ban/tài khoản/vai trò nhiều phạm vi/PIN/reset; W07 cửa, policy, ngưỡng có nguồn, QR và countdown; W08 duyệt 5 ảnh có xác thực; W14 cấu hình với nhãn nguồn và đánh đổi BLUFR; W16 nhật ký/lọc/phân trang/detail. Các thao tác chỉ báo thành công sau API thành công, không che 409/503.

Bộ thật tạo DB mới và hồ sơ qua pipeline từ ảnh U03 đã được người dùng cấp. Duyệt làm gallery từ 0 thành 1. Không seed hồ sơ/mặt/event/ngày công. Tên seed NV006 chỉ là nhãn demo, không xác nhận người thật trong ảnh. DB/thư mục dữ liệu nằm ngoài Git; private-inputs.json chỉ chứa đường dẫn và ID. Không lưu token vào báo cáo. QR trong ảnh đã được thu hồi sau chụp.

## Vấn đề và xử lý

- Giữ log lần đầu bị lỗi, không thay bằng kết quả đạt: pool asyncpg dùng qua hai loop được dispose trước chuyển TestClient→Uvicorn; CPU chậm cần heartbeat WS, harness đã gửi ping đúng giao thức và giới hạn OMP/MKL 2 thread khi kiểm. Không nới timeout/chất lượng nhận mẫu trên Hub.
- Hai lỗi fixture cũ do tải chậm khi thiếu RAM; chuyển ổ D, dừng AVD chưa dùng, timeout UI rõ ràng; bộ cuối 33/33. Lỗi đọc body request qua stream đã sửa giữ buffer cho retry token.
- Chụp lúc GSAP đang chạy tạo hàng mờ: chờ style ổn định rồi chụp lại. Các PNG khuôn mặt dùng mask trình duyệt ngay khi chụp; đã xem trực tiếp.
- Đổi tên thư mục mã màn thành face-review để không đụng tên `faces/` được checker dành cho dữ liệu sinh trắc.
- Build còn cảnh báo chunk >500 kB; lazy đã tách admin khỏi login. Không phải lỗi typecheck/lint.

## Giới hạn theo chuỗi task / đề xuất nguồn

Chưa làm backend ca/công/giải trình (T09), UI công (T10), event/giám sát/realtime (T11), nội dung /me (T12). Các tab Ca/Công/Event W04 hiện điều hướng tới màn tương ứng, sẽ hoàn thiện bảng nhúng khi endpoint sẵn sàng. Dashboard không tạo sự kiện giả để lấp vùng events trước T11. Không archive FG-EMP/FG-DASH/FG-GATE/FG-FACE chỉ vì đã có màn.

Employee DTO chưa trả người ghi consent và ca hiện tại; W04 hiện thời điểm consent và người đăng ký thật từ hồ sơ, không gán nhầm người đăng ký thành người ghi consent. Đề xuất session thiết kế bổ sung trường nguồn nếu cần hiển thị riêng đúng như admin.md. Không tự sửa OpenAPI/UI/DB.

## File tạo/sửa

web/src/{admin,components,shared,theme}, App/main/CSS; web configs, tests, README; api/client/result tích hợp refresh; báo cáo/log/28 ảnh; không sửa thuật toán/vendor/hợp đồng API hoặc nguồn UI.

## Review và Cần An làm

Xem REVIEW-T07.md: lệnh PowerShell thủ công, tài khoản và 10 bước đối chiếu. Không cần An ngồi chung; không chờ review để chuyển T08 theo chỉ đạo người dùng. T02 GPU vẫn bàn giao bất đồng bộ như RUN-T02.md.

## Chuyển archived

FG-AUTH-001, FG-ORG-001, FG-AI-004 đủ bằng chứng AC từ T03/T05/T06/T07, đã chuyển archived. Các spec còn phụ thuộc màn/ca/công/giải trình/sự kiện hoặc nhánh sinh trắc chưa đủ AC vẫn giữ approved.
