# Quản lý specs theo trạng thái

Áp dụng cho `03-app/docs/specs/` và các thư mục con, theo yêu cầu quản lý specs của người dùng.

- Spec tính năng mới tạo trong `01.draft/`, trạng thái `DRAFT`, mã `FG-{NHÓM}-{NNN}` không trùng. Không đặt file `FG-*.md` tại gốc.
- `02.approved/`: chỉ chuyển khi đã review và có xác nhận approved. Review còn yêu cầu sửa hoặc chưa có kết luận thì giữ draft. Ghi người/ngày review, người/ngày approved và căn cứ xác nhận; không tự bịa hoặc coi việc tạo spec là approval.
- `03.archived/`: chỉ chuyển khi triển khai và nghiệm thu xong. Ghi commit và liên kết báo cáo/log thật. Không suy diễn hoàn thành từ việc viết xong code/spec.
- Khi chuyển trạng thái: di chuyển file, giữ mã/tên, sửa metadata và mọi liên kết liên quan. Mỗi mã chỉ tồn tại một lần trong ba thư mục.
- Spec approved cần thay đổi yêu cầu: đưa về draft, ghi lịch sử để review lại. Thay đổi tính năng archived: tạo spec thay đổi mã mới, tham chiếu bản archived, giữ hồ sơ hoàn thành cũ.
- README, quy tắc chung, sổ câu hỏi và ma trận dùng chung nằm tại gốc. Cập nhật mục lục/ma trận đúng vị trí hiện tại của feature.
- Specs dẫn xuất không thay thế nguồn chuẩn; không sửa đặc tả/DB/UI/OpenAPI/plan hoặc tự quyết câu hỏi chưa chốt chỉ vì sắp xếp tài liệu.
- Khi kiểm tra: kiểm liên kết tương đối, mã duy nhất, vị trí khớp trạng thái và ma trận bao phủ. Không chạy nghiệm thu app cho thay đổi chỉ tổ chức tài liệu.
