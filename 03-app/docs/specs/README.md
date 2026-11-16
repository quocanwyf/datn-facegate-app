# Specs tính năng FaceGate — bản demo

Tài liệu dẫn xuất từ đặc tả v1.4.4 ngày 14/11/2026 để quản lý theo tính năng. Trạng thái triển khai/nghiệm thu được ghi theo từng spec và báo cáo Txx; không suy diễn hoàn thành từ thiết kế.

## Cách đọc

1. Chọn mã trong danh mục dưới để mở spec.
2. Xem quyền, dữ liệu, luồng, bất biến, API, nhánh lỗi và tiêu chí `FG-…-ACxx`.
3. Đối chiếu [quy tắc chung](QUY-UOC-CHUNG.md), [13 quyết định đã chốt](CAN-CHOT.md), [API](MA-TRAN-API.md), [màn hình](MA-TRAN-MAN-HINH.md).

## Trạng thái và thư mục

| Thư mục | Trạng thái | Điều kiện |
|---|---|---|
| [01.draft](01.draft/README.md) | DRAFT | Spec mới, chưa review/approved hoặc đang sửa sau review |
| [02.approved](02.approved/README.md) | APPROVED | Đã review và được approved, đủ căn cứ triển khai |
| [03.archived](03.archived/README.md) | ARCHIVED | Đã triển khai xong và nghiệm thu, có bằng chứng hoàn thành |

Hiện có 28 specs trong `02.approved`, 4 specs FG-AI-003/FG-AUTH-001/FG-ORG-001/FG-AI-004 trong `03.archived`, không có feature draft. Toàn bộ được duyệt ngày 14/11/2026; FG-AI-003 nghiệm thu ngày 15/11/2026 sau T04/T05. Xem [lịch sử duyệt](LICH-SU-DUYET.md#approved-2026-11-14).

Tài liệu dùng chung (mục lục, quy tắc, câu hỏi, ma trận) nằm ở gốc `specs/`. 32 specs đã được duyệt và 13/13 quyết định đã chốt trong `CAN-CHOT.md`. Nguồn chuẩn đã đồng bộ ngày 14/11/2026; tiến độ nghiệm thu theo từng spec và báo cáo task.

### Quy trình chuyển trạng thái

1. Spec mới luôn tạo tại `01.draft`, trạng thái `DRAFT`. Giữ nguyên mã tính năng và tên file khi chuyển thư mục.
2. Review còn yêu cầu sửa hoặc chưa approved: giữ `01.draft`. Khi đã review và approved, ghi người review/người approved, ngày, căn cứ xác nhận và kết quả xử lý các câu hỏi ảnh hưởng; đổi metadata thành `APPROVED`, chuyển sang `02.approved`.
3. Khi triển khai và nghiệm thu hoàn tất, ghi commit triển khai cùng liên kết báo cáo/log nghiệm thu; đổi metadata thành `ARCHIVED`, chuyển sang `03.archived`. Không coi việc viết xong spec hoặc viết xong code là đã hoàn thành nghiệm thu.
4. Nếu spec approved cần thay đổi yêu cầu, đưa về `01.draft` để review/approved lại và ghi lịch sử thay đổi. Tính năng đã archived cần thay đổi thì tạo spec thay đổi với mã mới, liên kết mã cũ; giữ hồ sơ hoàn thành cũ.
5. Mỗi mã feature chỉ có một file trong ba thư mục. Khi chuyển, cập nhật liên kết trong mục lục, ma trận và mọi spec tham chiếu. Không sao chép để giữ đồng thời nhiều bản cùng mã.

Không tự đánh dấu approved khi chưa có xác nhận. Quy trình này quản lý tài liệu; quyền sửa nguồn chuẩn và điều kiện nghiệm thu Txx vẫn theo hướng dẫn repo.

## Kết quả review

- **32/32 specs APPROVED**, **13/13 quyết định Q-001 đến Q-013 đã chốt** ngày 14/11/2026.
- Xem [quyết định và nguồn đã đồng bộ](CAN-CHOT.md), [lịch sử xác nhận](LICH-SU-DUYET.md).
- Đã đồng bộ nguồn chuẩn; chưa triển khai code/nghiệm thu app, các specs chưa chuyển archived.

## Quy tắc mã

`FG-{NHÓM}-{NNN}`: AUTH=xác thực/quyền; ORG=tổ chức; EMP=nhân viên; GATE=cửa; DEV=thiết bị; KIOSK=đầu cuối; FACE=khuôn mặt; AI=nhận dạng; ACCESS=ra vào; ATT=chấm công; REQ=giải trình; ME=cá nhân; DASH=tổng quan; MON=giám sát; EVENT=sự kiện; AUDIT=nhật ký; SYS=vận hành.

Giữ mã khi đổi tiêu đề, không tái sử dụng mã đã bỏ. W/E/K là **màn hình**, F-02/F-03 là **luồng cũ**, Txx là **task**: giữ nguyên để đối chiếu, không đổi thành mã feature. Một feature có thể trải qua nhiều màn/task. Đây chỉ là quy ước tổ chức tài liệu mới.

## Danh mục

| Mã | Tính năng | Màn hình/luồng | Task liên quan | Quyết định / đồng bộ nguồn |
|---|---|---|---|---|
| [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | Đăng nhập, đổi mật khẩu và quản lý phiên | W-01, E-01; menu tài khoản | T03, T07, T12 | — |
| [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | Tài khoản, vai trò, mật khẩu tạm và PIN | W-05 tab Tài khoản; W-03 tạo kèm | T03, T06, T07 | Q-011 đã chốt (đã đồng bộ) |
| [FG-ORG-001](03.archived/FG-ORG-001-phong-ban.md) | Quản lý phòng ban | W-05 tab Phòng ban | T03, T06, T07 | — |
| [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | Hồ sơ và vòng đời nhân viên | W-03, W-04 | T03, T06, T07 | Q-002 đã chốt (đã đồng bộ) |
| [FG-GATE-001](02.approved/FG-GATE-001-cua-chinh-sach.md) | Cửa, chính sách ra vào và ngưỡng từng cửa | W-07 | T06, T07, T11 | Q-001 đã chốt (đã đồng bộ) |
| [FG-DEV-001](02.approved/FG-DEV-001-thiet-bi-ghep-thu-hoi.md) | Tạo, ghép và thu hồi thiết bị Kiosk | W-07, K-01 | T05, T06, T07, T08 | — |
| [FG-KIOSK-001](02.approved/FG-KIOSK-001-camera-ket-noi.md) | Camera, WebSocket và phục hồi kết nối | K-02, K-04, K-11 | T05, T08, T14 | Q-003 đã chốt (đã đồng bộ); Q-006 đã chốt (đã đồng bộ) |
| [FG-KIOSK-002](02.approved/FG-KIOSK-002-phien-dang-ky-pin.md) | Phiên đăng ký bằng PIN HR | K-05, K-06 | T05, T08 | Q-004 đã chốt (đã đồng bộ) |
| [FG-FACE-001](02.approved/FG-FACE-001-dong-y-sinh-trac.md) | Đồng ý hoặc từ chối dùng khuôn mặt | K-07; W-04/E-08 đọc trạng thái | T05, T08, T12 | Q-005 đã chốt (đã đồng bộ) |
| [FG-FACE-002](02.approved/FG-FACE-002-thu-mau-dang-ky.md) | Thu mẫu và tạo hồ sơ chờ duyệt | K-08, K-09; F-02 | T04, T05, T08 | Q-004 đã chốt (đã đồng bộ), Q-006 đã chốt (đã đồng bộ) |
| [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | Duyệt hồ sơ và cập nhật gallery | W-08; W-04 xem mẫu | T04, T05, T07 | Q-002 đã chốt (đã đồng bộ), Q-006 đã chốt (đã đồng bộ) |
| [FG-FACE-004](02.approved/FG-FACE-004-xoa-rut-dong-y.md) | Xóa sinh trắc và rút đồng ý | W-04, E-08; W-03 nghỉ việc | T05, T06, T07, T12 | Q-005 đã chốt (đã đồng bộ), Q-006 đã chốt (đã đồng bộ) |
| [FG-AI-001](02.approved/FG-AI-001-cong-kiem-mo-hinh.md) | Nạp mô hình đã xác minh | W-14; K-11 khi chưa sẵn sàng | T01, T02, T04 | Q-008 đã chốt (đã đồng bộ) |
| [FG-AI-002](02.approved/FG-AI-002-pipeline-feature.md) | Pipeline khung và trích đặc trưng | K-02, K-08 | T01, T02, T04 | Q-006 đã chốt (đã đồng bộ) |
| [FG-AI-003](03.archived/FG-AI-003-bo-quyet-dinh.md) | Bộ quyết định đa khung và cooldown | K-02, K-04; F-03 | T04, T05, T14 | — |
| [FG-AI-004](03.archived/FG-AI-004-settings-nguong.md) | Cấu hình nhận dạng và nguồn ngưỡng | W-14, W-07 | T02, T04, T06, T07 | Q-001 đã chốt (đã đồng bộ), Q-007 đã chốt (đã đồng bộ) |
| [FG-AI-005](02.approved/FG-AI-005-mini-fas-net.md) | Chống giả mạo MiniFASNet và hiệu chỉnh L | W-14, K-04 DENY/SPOOF | T13 | Q-007 đã chốt (đã đồng bộ) |
| [FG-ACCESS-001](02.approved/FG-ACCESS-001-quyet-dinh-ra-vao.md) | Cho phép hoặc từ chối ra vào | K-04; F-03 | T04, T05, T11 | Q-002 đã chốt (đã đồng bộ) |
| [FG-ACCESS-002](02.approved/FG-ACCESS-002-mo-cua-thu-cong.md) | Mở cửa thủ công mô phỏng | W-10 Thao tác nhanh | T06, T11 | — |
| [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | Ca, phân ca và ngày lễ | W-06; W-04 tab Ca; E-02 | T06, T07, T09 | — |
| [FG-ATT-002](03.archived/FG-ATT-002-tinh-chot-cong.md) | Tính lại và chốt ngày công | W-09; E-02/E-03/E-04; K-04 | T09, T10, T12 | Q-008 đã chốt (đã đồng bộ), Q-009 đã chốt (đã đồng bộ), Q-010 đã chốt (đã đồng bộ) |
| [FG-ATT-003](02.approved/FG-ATT-003-bang-cong-sua-nghi.md) | Bảng công, sửa ngày công và đánh dấu nghỉ | W-09, W-04 tab Công | T06, T09, T10 | Q-009 đã chốt (đã đồng bộ) |
| [FG-ATT-004](02.approved/FG-ATT-004-cham-cong-ho.md) | Chấm công hộ hiện tại | W-10 | T06, T09, T11 | — |
| [FG-REQ-001](02.approved/FG-REQ-001-tao-huy-giai-trinh.md) | Gửi, xem và hủy giải trình cá nhân | E-04, E-05, E-06 | T06, T09, T12 | — |
| [FG-REQ-002](02.approved/FG-REQ-002-duyet-giai-trinh.md) | Duyệt hoặc từ chối giải trình | W-12, E-10 | T06, T09, T10, T12 | Q-011 đã chốt (đã đồng bộ) |
| [FG-ATT-005](03.archived/FG-ATT-005-excel-thang.md) | Xuất Excel bảng công tháng | W-09 | T06, T09, T10 | Q-001 đã chốt (đã đồng bộ), Q-010 đã chốt (đã đồng bộ) |
| [FG-ME-001](02.approved/FG-ME-001-cong-ca-ca-nhan.md) | Hôm nay, công tháng và chi tiết cá nhân | E-02, E-03, E-04; shell /me | T06, T12 | — |
| [FG-DASH-001](02.approved/FG-DASH-001-tong-quan.md) | Tổng quan hôm nay và điều hướng quản trị | W-02; shell /admin | T06, T07, T11 | Q-012 đã chốt (đã đồng bộ) |
| [FG-MON-001](02.approved/FG-MON-001-giam-sat-canh-bao.md) | Giám sát realtime và xử lý cảnh báo | W-10; W-02/W-07 nhận WS | T05, T07, T11 | — |
| [FG-EVENT-001](02.approved/FG-EVENT-001-su-kien-csv-bao-cao.md) | Tra cứu sự kiện, CSV và báo cáo chấm hộ | W-11; W-04 tab Sự kiện | T06, T07, T11 | — |
| [FG-AUDIT-001](02.approved/FG-AUDIT-001-nhat-ky.md) | Nhật ký thao tác | W-16 | T03, T06, T07 | — |
| [FG-SYS-001](02.approved/FG-SYS-001-suc-khoe-van-hanh.md) | Sức khỏe Hub, phiên bản và giới hạn vận hành | Header /admin, W-14, K-11 | T03, T14 | Q-008 đã chốt (đã đồng bộ), Q-013 đã chốt phạm vi |

## Ngoài phạm vi demo

- Không so sánh/chọn nhiều model, W-15/K-12 hoặc `/compare`.
- Không quản trị phiên bản điều khoản/W-17, log đọc ảnh, audit before/after chi tiết, retention job, refresh device token.
- Không K-03 thử thách, K-10 cài đặt, E-07 thông báo, E-09 đã bỏ. W-13 gộp W-05.
- Không ca qua đêm, tăng ca, đơn xin nghỉ riêng, khóa kỳ, relay cửa thật, đa công ty/chi nhánh hoặc ra vào theo khung giờ.
- Vẫn có **đánh dấu nghỉ LEAVE** bởi OWNER/HR; không có đơn xin nghỉ riêng không loại bỏ thao tác này.
- `/me` web responsive, không bắt buộc PWA. Demo HTTP/WS LAN, không tính TLS/BitLocker/pháp lý là tính năng app.

## Giới hạn sử dụng

Nguồn chính thức vẫn là đặc tả (§0a ưu tiên), DB, OpenAPI/WS và UI. Không dùng bộ specs để tự thêm endpoint/cột DB hoặc nới điều kiện dừng Txx. Câu hỏi chưa chốt không được coi là quyết định thay An. Bộ specs không thay hướng dẫn cài môi trường T00, benchmark T02/T14 hay tư liệu quyển T15.
