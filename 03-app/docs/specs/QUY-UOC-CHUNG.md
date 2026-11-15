# Quy tắc chung và nguồn

- Ngày lập: 14/11/2026. Trạng thái: tài liệu dẫn xuất.
- Chỉ bổ sung specs, không sửa đặc tả/DB/UI/OpenAPI/plan hoặc code triển khai.

## 1. Nguồn chính thức và ưu tiên

| Nguồn | Nội dung |
|---|---|
| [Đặc tả v1.4.3](../../dac-ta-app.md) | Phạm vi, nghiệp vụ; **§0a thắng các nội dung cũ đã bỏ** |
| [Thiết kế DB](../../db/thiet-ke-db.md), [schema](../../db/schema.sql) | DB demo, bảng/cột/ràng buộc; thiết kế DB thắng §7 khi lệch |
| [Seed](../../db/seed.sql) | Nguồn duy nhất cho dữ liệu demo; không tạo giả nhận dạng/công/mặt |
| [OpenAPI](../../openapi/openapi.yaml) | REST, operationId, x-roles, schema, HTTP |
| [WebSocket](../../openapi/ws-protocol.md) | Kiosk/monitor, message và xác thực |
| [Design system](../../ui/design-system.md), [status.json](../../ui/tokens/status.json) | Token, nhãn, màu và trạng thái |
| [Admin](../../ui/man-hinh/admin.md), [Kiosk](../../ui/man-hinh/kiosk.md), [Me](../../ui/man-hinh/me.md) | Layout, điều hướng, tương tác từng màn |
| [Plan](../../plan-codex/README.md) | Task, nghiệm thu và mẫu báo cáo |
| [api-contract](../../../.agents/skills/api-contract/SKILL.md), [cham-cong-vn](../../../.agents/skills/cham-cong-vn/SKILL.md) | Quy ước API và nghiệp vụ đã có |

Nếu nguồn mâu thuẫn mà không được quy tắc ưu tiên giải quyết: ghi mã Q trong [CAN-CHOT](CAN-CHOT.md), không tự sửa nguồn hoặc triển khai phần chưa chốt. Công việc tài liệu này ghi nhận, không quyết định thay nguồn.

## 2. Hợp đồng và dữ liệu

- Mọi REST trong OpenAPI có prefix `/api/v1`, gồm `/health` và `/version` khi ghép server URL. Một số mô tả UI dùng đường dẫn rút gọn, không dùng để tạo endpoint khác.
- `x-roles`: public=không cần đăng nhập, any=đã đăng nhập, device=Kiosk; các vai trò OWNER/HR/MANAGER/SECURITY/EMPLOYEE giữ nguyên.
- Kiểm quyền và lọc phạm vi ở server: company, team theo `scope_department_id`, bản thân theo employee liên kết tài khoản. Không tin client. Nhiều vai trò và chuyển cấp giải trình xem Q-011.
- Lỗi `{error:{code,message,details?}}`: code máy đọc, message tiếng Việt. Không dùng specs này để tự thêm mã lỗi.
- Phân trang `page>=1`, `size<=100`, response `{items,total,page,size}`. Query/enum/required/bounds cụ thể tra schema gốc.
- UUID/FK/tính duy nhất theo DB. Vector `real[]` 512 phần tử; không thêm pgvector cho demo.
- Timestamp `timestamptz`, API ISO-8601 có offset; ngày công theo timezone company, mặc định `Asia/Ho_Chi_Minh`. UI `dd/MM/yyyy`, `HH:mm`.
- `recognition_event` chỉ thêm; ngoại lệ xóa `snapshot_path` về NULL, không đổi điểm/kết quả hoặc xóa event. Xử lý cảnh báo lưu bảng riêng.
- Frame camera không lưu DB; ảnh mẫu/crop ở `HUB_DATA_DIR` ngoài repo. MATCH không ảnh, UNKNOWN/SPOOF có crop theo nguồn. Không ghi token/PIN/mật khẩu vào tài liệu/log.

## 3. Giao diện và trải nghiệm

- Tiếng Việt; Web teal Canopy, Kiosk lime Fresh Bloom. Nhãn/token lấy từ nguồn, không thêm màn ngoài §9.
- Preview camera trực tiếp được phép trên Kiosk; không hiện ảnh mẫu/crop/kết quả khuôn mặt hoặc nhận ảnh trả về.
- Admin ưu tiên desktop >=1280 px; dưới 1024 px Sider thành Drawer, bảng cuộn ngang. `/me` 360–430 px, max480 ở desktop. Kiosk tablet ngang tương đương 1280× 800 dp.
- Trạng thái tải/rỗng/lỗi/không quyền theo UI nguồn. Đề xuất UX: khóa nút khi đang gửi để tránh gửi lặp, cho thử lại khi lỗi mạng nhưng không tự replay thao tác ghi. Đây là đề xuất, không bổ sung idempotency vào hợp đồng.
- Chuyển động ở vị trí design system cho phép, tôn trọng giảm chuyển động. Kết quả Kiosk đọc từ 1–2 m, chữ >=48 px, tương phản >=4,5:1 là yêu cầu thiết kế, chưa xác nhận kết quả render.

## 4. Nghiệm thu và trạng thái

- AC trong từng file là **dự kiến kiểm**, chưa chạy/chưa đạt. Đây không phải báo cáo hoàn thành phần mềm.
- Kiểm hợp đồng/quyền/trạng thái/biên theo Txx; lưu log thật trong `ket-qua-kiem-thu`, dữ liệu sinh trắc ngoài repo.
- Số BLUFR dẫn lại nghiên cứu cũ, không phải số đo app. Mục tiêu hiệu năng chưa có log vẫn là mục tiêu.
- Tham số [khởi đầu] nằm trong cấu hình, không biến thành hằng số bất biến. Ngưỡng L chưa hiệu chỉnh không tự đặt giá trị.
- Phụ thuộc trong spec thể hiện tính năng dùng chung/liên quan, có thể có tham chiếu hai chiều; thứ tự triển khai luôn theo plan Txx.
