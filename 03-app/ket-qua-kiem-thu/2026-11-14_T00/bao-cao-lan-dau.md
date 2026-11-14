# Báo cáo T00 — Môi trường dev, skill ngoài, cơ sở dữ liệu

> Kiểm tra lại theo yêu cầu tiếp tục T00–T12: xem [báo cáo tiếp tục kế hoạch](tiep-tuc-ke-hoach.md) và `tiep-tuc-plan.log`. Mâu thuẫn `.env` chưa được sửa; thiếu checkpoint cho bước T01. Ngoại lệ mới của người dùng cho T02 đã được ghi nhận trong báo cáo tiếp tục.

- Trạng thái: **DỪNG** — yêu cầu tạo `.env` trong repo ở bước 4 của T00 mâu thuẫn với bộ kiểm bí mật bắt buộc ở bước 7. Áp dụng `AGENTS.md:19`: “Nếu đặc tả và code mâu thuẫn, hoặc task thiếu thông tin: dừng, ghi câu hỏi vào báo cáo, không tự đoán thiết kế.”
- Commit: chưa commit/push vì chưa đạt toàn bộ tiêu chí; HEAD khi kiểm tra là `692ebda201733cb5a6bc942bf4481ac6fe71bc9b`, nhánh `main`.
- Ngày thực hiện: 14/11/2026, múi giờ Asia/Bangkok.
- Máy chạy: Windows 11 Home Single Language, `10.0.26200`, 64-bit; CPU `12th Gen Intel(R) Core(TM) i5-12500H`. Output thật trong `kiem-tra-ban-dau.log` và `bang-chung-dung.log`.

## Tiêu chí nghiệm thu

| # | Tiêu chí (copy từ task) | Số đo / kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Phiên bản Python, Node, pnpm, psql, Android Studio/AVD ghi trong báo cáo | `Python 3.14.6`; `node v24.15.0`; `pnpm 11.25.0`; `psql (PostgreSQL) 18.6`. Python launcher còn liệt kê CPython 3.11.15. Chưa có bằng chứng Python 3.13 hoặc PostgreSQL 16. Chưa lấy được phiên bản Android Studio/AVD từ các đường dẫn mặc định đã kiểm tra. | `kiem-tra-ban-dau.log` | Chưa đạt |
| 2 | `schema.sql` + `seed.sql` chạy không lỗi; `select count(*) from employee` = 24 | Chưa tạo role/DB, chưa chạy schema/seed hoặc truy vấn đếm vì đã dừng. Dịch vụ hiện có là `postgresql-x64-18`, trạng thái Running; không dùng bản 18 thay cho yêu cầu bản 16. | `kiem-tra-ban-dau.log` | Chưa chạy |
| 3 | `test_constraints.sql` cho dòng cuối **`44 \| 44`** | Chưa chạy; không có kết quả 44/44 để nghiệm thu. | Không có log psql | Chưa chạy |
| 4 | Mỗi skill trong `SKILLS-NGOAI.md`: đã cài (đường dẫn) hoặc ghi rõ lý do bỏ qua | Đã đọc danh sách; chưa tra cứu nguồn/cài skill ngoài, chưa tạo `NGUON.md` do dừng trước khi triển khai. Không kết luận nguồn nào đã ngừng hoạt động hay thiếu skill. | Không có log cài skill | Chưa thực hiện |
| 5 | Máy ảo hiện hình webcam | Chưa khởi động/tạo AVD, chưa kiểm webcam và chưa có ảnh chụp màn. Không tìm thấy emulator tại `%LOCALAPPDATA%/Android/Sdk/emulator/emulator.exe`; điều này chưa đủ kết luận máy không có SDK hoặc webcam. | `kiem-tra-ban-dau.log` | Chưa kiểm chứng |
| 6 | `kiem-bi-mat.py` báo sạch; `.env` không bị git theo dõi | Lần đầu checker lỗi mã hoá stdout `cp1252`. Chạy lại bằng `$env:PYTHONUTF8 = '1'; python 03-app/tools/kiem-bi-mat.py` cho `SẠCH`, exit code 0 trên trạng thái **chưa tạo `.env`**. `git ls-files -- .env` không có output; `git check-ignore -v -- .env` trả `.gitignore:2:.env`. Chưa nghiệm thu cấu hình `.env` hoàn chỉnh. | `kiem-tra-ban-dau.log`, `bang-chung-dung.log`, `kiem-tra-cuoi.log` | Chưa đạt toàn bộ |

## Đã làm (ngắn)

- Đọc `README-BAN-GIAO.md`, `AGENTS.md`, T00, mẫu báo cáo, `SKILLS-NGOAI.md`, đặc tả (file hiện có là v1.4.3, gồm §0a), thiết kế DB (gồm §7–8), các SQL và `kiosk/AGENTS.md`.
- Đọc hướng dẫn hệ thống `skill-installer` để chuẩn bị cách cài vào `.agents/skills/`; chưa thực hiện cài đặt.
- Kiểm tra trạng thái Git trước khi làm: cây làm việc sạch, nhánh `main`. Chạy `git pull --ff-only`: `Already up to date.`
- Ghi output phiên bản và kiểm tra bộ kiểm bí mật trên trạng thái hiện tại.
- Chỉ tạo báo cáo và log trong thư mục kết quả T00. Chưa cài phần mềm, chưa yêu cầu quyền admin, chưa sửa DB, `.env`, skill hoặc mã nguồn.

## File đã tạo / sửa

- `03-app/ket-qua-kiem-thu/2026-11-14_T00/bao-cao.md`.
- `03-app/ket-qua-kiem-thu/2026-11-14_T00/git-pull.log`.
- `03-app/ket-qua-kiem-thu/2026-11-14_T00/kiem-tra-ban-dau.log`.
- `03-app/ket-qua-kiem-thu/2026-11-14_T00/bang-chung-dung.log`.
- `03-app/ket-qua-kiem-thu/2026-11-14_T00/kiem-tra-cuoi.log`.

## Vấn đề gặp + cách xử lý

1. **Mâu thuẫn chặn nghiệm thu**: `T00-moi-truong.md:18` yêu cầu sao chép `.env.example` thành `.env`; dòng 21 yêu cầu checker sạch. Trong `kiem-bi-mat.py`, dòng 21 nhận diện tên `.env`, dòng 27 quét cây thư mục bằng `os.walk`, dòng 37–38 đánh dấu `.env` là file cấm. Không có bước tra cứu trạng thái Git hoặc loại file `.env` đã được Git bỏ qua. Do đó, giữ `.env` như bước 4 sẽ khiến bước 7 thất bại. Đây là kết luận đọc mã, **chưa chạy thử với `.env` thật** vì dừng ngay khi phát hiện mâu thuẫn. Đã lưu nguyên logic và các dòng yêu cầu trong `bang-chung-dung.log`.
2. **Encoding PowerShell/Python**: lần chạy checker đầu tiên gặp `UnicodeEncodeError` khi in tiếng Việt. Đặt `PYTHONUTF8=1` trong tiến trình lệnh rồi chạy lại thành công; không sửa script hoặc cấu hình hệ thống.
3. Máy đang có PostgreSQL 18, chưa kiểm chứng/cài PostgreSQL 16. Đây **không phải** kết luận “không cài được PostgreSQL 16”; chưa thử cài do đã gặp quy định dừng chung.

## Đề xuất cho thiết kế (KHÔNG tự sửa đặc tả/db/ui/openapi)

Đề nghị An thống nhất cách kiểm bí mật khi có `.env` local đã được Git bỏ qua: ví dụ cho phép checker bỏ qua đúng `.env` local nhưng vẫn chặn `.env` đã bị Git theo dõi. Cần cập nhật hướng dẫn/phạm vi sửa tương ứng trước khi tiếp tục T00. Chưa tự sửa checker vì `03-app/tools/` không nằm trong phạm vi được ghi của task này; chưa di chuyển/xoá tạm `.env` để lấy kết quả sạch.

## Cần An làm — tin nhắn soạn sẵn để Hy gửi

> An ơi, T00 đang DỪNG theo AGENTS.md vì bước 4 yêu cầu tạo `.env` ở gốc repo, nhưng `03-app/tools/kiem-bi-mat.py:37–38` luôn chặn file này, kể cả khi `.gitignore` đã bỏ qua; bước 7 lại bắt buộc checker SẠCH. Nhờ An thống nhất cách xử lý và cập nhật task/phạm vi cho phép sửa checker nếu cần. Gửi lại commit hoặc chỉ dẫn đã thống nhất để mình tiếp tục. Báo cáo và bằng chứng ở `03-app/ket-qua-kiem-thu/2026-11-14_T00/bao-cao.md` và `bang-chung-dung.log`. Hiện chưa cài phần mềm hay tạo DB; PostgreSQL có sẵn là 18.6, chưa thay thế cho yêu cầu 16.

## Câu hỏi cho An (chỉ khi DỪNG)

T00 phải xử lý `.env` local đã được Git bỏ qua thế nào để đồng thời đáp ứng bước 4 và bước 7? Nếu sửa checker, An có cho phép bổ sung `03-app/tools/kiem-bi-mat.py` vào phạm vi T00 và thống nhất hành vi kiểm tra như đề xuất trên không?
