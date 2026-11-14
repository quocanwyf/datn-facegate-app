# Tiếp tục kế hoạch T00–T12 — 14/11/2026

> Hồ sơ lịch sử trước khi được phép sửa checker. Mâu thuẫn .env đã được gỡ; T00 đã kiểm DB 44/44 và webcam thật. Trạng thái hiện hành xem `bao-cao.md`; không dùng dòng DỪNG bên dưới để suy ra còn đang bị chặn.

> Cập nhật sau khi nhận file người dùng: đã nhận `C:/Users/NMinH/Downloads/best.pt`, đối chiếu SHA-256 trước khi sao chép và đặt đúng đường dẫn checkpoint. `kiem-checkpoint.py` trả OK, khớp manifest, epoch mong đợi 18; xem `checkpoint-da-nhan.log`. Checkpoint bị Git bỏ qua bởi `*.pt` và chưa được theo dõi. Vướng mắc thiếu checkpoint ở các mục kiểm tra cũ dưới đây đã được gỡ; chưa nghiệm thu cổng nạp mô hình T01. T00 vẫn dừng do bộ kiểm bí mật.

- Trạng thái: **DỪNG tại T00** — mâu thuẫn cấu hình local và bộ kiểm bí mật chưa được giải quyết.
- Commit: chưa commit/push.
- Căn cứ người dùng: tiếp tục theo plan lần lượt; riêng T02 được bàn giao script + RUN-T02.md rồi push và tiếp tục, không chờ log GPU. Ngoại lệ này không tự xác nhận parity đạt hoặc bỏ các điều kiện dừng khác.
- Bằng chứng kiểm tra lại: `tiep-tuc-plan.log`. Lệnh git pull --ff-only trước kiểm tra trả Already up to date.

## Kết quả kiểm tra lại

1. T00 bước 4 yêu cầu tạo `.env`; bước 7 yêu cầu checker sạch. `kiem-bi-mat.py` vẫn chặn `.env` dù đã bị Git bỏ qua. `.env` hiện chưa tồn tại, không có file này được Git theo dõi. Chưa tạo hoặc in giá trị bí mật.
2. `python 03-app/tools/kiem-checkpoint.py` trả exit=1, THIẾU checkpoint. T01 vẫn yêu cầu có checkpoint trước khi bắt đầu; chưa khởi động T01.
3. Chưa cài thêm phần mềm, chưa thay đổi DB hoặc bộ kiểm bí mật, chưa tự bỏ phụ thuộc của các task.

## Phương án cụ thể cần chốt

Cho phép sửa `03-app/tools/kiem-bi-mat.py` ngoài phạm vi ghi hiện tại của T00 để xử lý đúng cấu hình local:

- Chỉ cho phép đúng `.env` ở gốc repo nếu `git check-ignore` xác nhận bị bỏ qua và `git ls-files` xác nhận chưa bị theo dõi.
- `.env` đã được Git theo dõi vẫn lỗi, kể cả bị thêm force; các file `.env.*` thật và mọi quy tắc chặn checkpoint/dữ liệu/khóa khác giữ nguyên.
- Khi không xác định được trạng thái Git, tiếp tục chặn `.env`.

Sau khi nhận checkpoint, cần chốt thêm xử lý đúng file checkpoint local tại đường dẫn chuẩn đã được Git bỏ qua và chưa tracked: bộ kiểm hiện cũng chặn `.pt` local dù task cần file này. Không được sửa checker theo cách cho phép checkpoint đã tracked, không dùng kết quả hash đúng để cho phép commit trọng số. Chưa sửa checker; chỉ ghi nhận phạm vi liên quan để tránh gỡ `.env` rồi vướng lại cùng kiểu kiểm file local ở T01.
- Kiểm tra bằng repo Git tạm: `.env` local ignored được chấp nhận, `.env` tracked bị chặn, `.env` untracked nhưng không ignored bị chặn, file bí mật khác vẫn bị chặn. Chỉ dùng chuỗi kiểm thử, không dùng bí mật thật.

Chưa áp dụng phương án này vì AGENTS.md yêu cầu dừng khi nguồn và code mâu thuẫn; phạm vi T00 hiện không cho ghi tools.

## Quy trình sau khi gỡ chặn

- Hoàn tất T00 với log thật, sau đó T01. Không thay PostgreSQL 16 bằng bản khác hoặc đổi số kiểm constraint để lấy kết quả đạt.
- Đến T02: viết script và RUN-T02.md, kiểm phần chạy được trên máy này, bàn giao/push phần script theo ngoại lệ người dùng; ghi rõ chờ GPU, không ghi parity đạt khi chưa có log.
- Tiếp tục T03–T12 trong phạm vi các điều kiện và dữ liệu cần thiết đã đủ. Dùng specs approved cùng đặc tả/DB/UI/OpenAPI hiện hành.
- Spec chỉ chuyển archived khi toàn bộ phạm vi và nghiệm thu tương ứng đã đạt, có commit/log; cập nhật metadata và các liên kết. Các giao diện review bằng API mô phỏng hiện tại chưa đủ để archive FG-AUTH-001/FG-EMP-001.

## Cần An làm

> An ơi, nhờ xác nhận cho sửa `03-app/tools/kiem-bi-mat.py` theo phương án ở báo cáo này để `.env` local đã ignored/untracked không chặn T00, nhưng `.env` tracked vẫn bị chặn. Đồng thời cần gửi checkpoint `best.pt`, đặt đúng `02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt`, rồi chạy `python 03-app/tools/kiem-checkpoint.py` và báo lại output. Không commit checkpoint. Ngoại lệ T02 đã ghi nhận: bàn giao script + RUN-T02.md và tiếp tục, kết quả GPU gửi sau.
