# Báo cáo T00 — Môi trường dev, skill ngoài, cơ sở dữ liệu

- Trạng thái: **XONG** — DB, công cụ, AVD và preview webcam thật đã kiểm tra.
- Commit: ghi hash triển khai sau khi tạo commit T00; không commit .env/checkpoint/ảnh webcam.
- Máy: Windows 11; Python 3.13.13, Node v24.15.0, pnpm 11.25.0, PostgreSQL 16.16 (`versions-current.log`).
- Ngày bắt đầu: 14/11/2026 (Asia/Bangkok).
- Báo cáo cũ được giữ ở `bao-cao-lan-dau.md`. Vướng mắc .env đã gỡ theo xác nhận của người dùng; checkpoint đã nhận và khớp manifest.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Phiên bản Python, Node, pnpm, psql, Android Studio/AVD | Python 3.13.13, Node v24.15.0, pnpm 11.25.0, psql 16.16; Android Studio 2025.3.4 build AI-253.32098.37.2534.15336583 có sẵn, emulator 36.5.11, adb 37.0.0; AVD Android API 34 | versions-current.log, studio-version.log, sdk-installed-after.log, adb-version.log, avd-boot.log | Đạt |
| 2 | schema.sql + seed.sql chạy không lỗi; employee=24 | Cụm PostgreSQL 16 riêng tại 127.0.0.1:5433; facegate_dev owner facegate; schema/seed thành công, đếm 24 nhân viên | schema.log, seed.log, seed-counts.log | Đạt |
| 3 | test_constraints.sql cuối 44/44 | 44 ca ĐẠT; 44\|44; ROLLBACK. Sau kiểm thử employee/event/attendance_day/face_profile = 24\|0\|0\|0 | test-constraints.log, seed-counts.log | Đạt |
| 4 | Mỗi skill đã cài hoặc ghi lý do bỏ qua | Cài các nguồn FastAPI/Supabase/Vercel/GSAP/Expo/Software Mansion bằng skill-installer, pin commit; bỏ openai/skills vì upstream deprecated theo hướng dẫn, không tìm thay thế | .agents/skills/NGUON.md, skill-sources.json, skill-install-results.json, install-*.log, openai-skills-readme.txt | Đạt |
| 5 | Máy ảo hiện hình webcam | AVD FaceGate_PixelTablet_API34 boot_completed=1, API34, 2560x1600; camera trước webcam0 USB NV12. Đã mở app Camera, chuyển Front camera và xem ảnh preview thật sau khi người dùng mở nắp che. Ảnh có khuôn mặt lưu ngoài repo: C:/Users/NMinH/AppData/Local/FaceGate/evidence/T00-camera-front.png | avd-boot.log, avd-config.log, emulator-webcams.log, camera-front-dumpsys.log, camera-evidence-local.log (hash ảnh) | Đạt; ảnh chỉ giữ local |
| 6 | Checker sạch; .env không tracked | .env từ template, mật khẩu DB/JWT ngẫu nhiên, không in ra log; checker SẠCH; env-tracked.log rỗng, Git bỏ qua .env | checker-with-env.log, env-tracked.log, env-ignored.log | Đạt tại lần kiểm |

## Đã làm

- Sửa checker theo quyền người dùng cấp: chỉ chấp nhận .env gốc/checkpoint chuẩn local khi Git xác nhận ignored và untracked. File force-added vẫn chặn; tracked file trong thư mục thường bỏ qua vẫn được kiểm. Không bỏ chặn bí mật/trọng số khác. **10/10** ca hồi quy bằng repo Git tạm đạt trên Python 3.13 (`checker-tests.log`), không dùng bí mật thật.
- Cài Python 3.13 bằng uv; cài pnpm cho user và thêm thư mục npm user vào PATH để terminal mới dùng được.
- Máy không có quyền admin. Dùng PostgreSQL 16 native ZIP từ EDB, cluster riêng trong LOCALAPPDATA/FaceGate/postgresql16, listen 127.0.0.1:5433. Không sửa/xóa/dừng PostgreSQL 18 đang có. Script `setup-postgres16.ps1` giữ mật khẩu admin ngoài repo; .env dùng CPU và DB riêng.
- Chạy nguyên bản schema/seed/test_constraints, không sửa nguồn DB; giữ hash tại `db-source-hashes.log`.
- Android Studio/SDK có ở đường dẫn khác mặc định: C:/Program Files/Android/Android Studio và C:/Developer/Tools/Android/SDK. Đã dừng tải IDE mới sau khi phát hiện, dọn tiến trình/archive tải dở do task tạo; không xóa bộ cài của người dùng.
- Tải command-line tools 22.0, kiểm SHA256 công bố và CRC; giải nén cạnh tools 20.0 sẵn có, không ghi đè. SDK licenses đã được chấp nhận trong phạm vi cài môi trường.
- System image Android 34 default x86_64 đã tải đủ byte, SHA1 khớp metadata SDK, CRC ZIP hợp lệ; SHA256 thực tế trong system-image-download.log. Đã giải nén vào đúng SDK và được sdkmanager nhận. Tools 22.0 nằm cạnh latest 20.0 trong SDK; cấu hình Pixel Tablet ngang, 2GB RAM, camera front webcam0/back emulated, WHPX và SwiftShader.
- Đã mở Camera trên AVD, tắt gắn vị trí ảnh cho thiết bị thử, chuyển đúng Front camera. Ban đầu preview tối vì nắp che; người dùng xác nhận mở nắp, ảnh kiểm lại đã có hình thật. Không dùng ảnh preview cho seed/gallery hoặc nhận dạng và không đưa ảnh vào Git.

## File tạo/sửa

`03-app/tools/kiem-bi-mat.py`, `test_kiem_bi_mat.py` (phạm vi người dùng bổ sung); các skill ngoài mới và `.agents/skills/NGUON.md`; .env local ignored; log/script trong thư mục kết quả T00. PostgreSQL/Python/pnpm/Android setup nằm ngoài repo. Không sửa nguồn chuẩn hoặc 4 skill dự án đang có thay đổi của người dùng.

## Vấn đề và xử lý

- Không dùng PostgreSQL 18 thay 16; cài 16 riêng tránh cổng 5432 và quyền admin.
- pg_ctl gọi qua pipeline giữ handle tiến trình nền; script chuyển sang Start-Process Hidden, chờ riêng pg_ctl thay vì toàn bộ cây server. DB đã kết nối/chạy SQL được.
- OpenAI skills upstream deprecated nên bỏ theo SKILLS-NGOAI.md; skill mới sẽ được khám phá ở lượt Codex tiếp theo, có thể đọc SKILL.md trực tiếp khi cần trước đó. Không coi việc cài là đã áp dụng skill.
- Tải Android trực tiếp chậm; helper HTTP Range kiểm đủ byte/checksum/CRC trước dùng. Không chạy archive chưa kiểm được.
- avdmanager không tìm được image khi tools nằm ngoài SDK: đặt tools 22.0 vào cmdline-tools/22.0 đúng bố cục SDK, không ghi đè bản latest. Cảnh báo devices.xml không ngăn tạo/boot Pixel Tablet; kiểm thực tế xác nhận API34, 2560x1600, camera USB hoạt động.

## Nguồn cài đặt

PostgreSQL ZIP từ [nguồn Windows chính thức](https://www.postgresql.org/download/windows/) và [EDB binaries](https://www.enterprisedb.com/download-postgresql-binaries); hash tại postgresql16-download.log. Android từ [Android Studio](https://developer.android.com/studio), [SDK manager](https://developer.android.com/tools/sdkmanager) và metadata Google trong system-image-source.json.

## Cần An làm

Không còn thao tác bắt buộc cho T00. Camera đã được kiểm sau khi người dùng mở nắp che. Ảnh kiểm chứng không push vì có khuôn mặt, có đường dẫn local và hash để kiểm tra. Khi mở PowerShell mới, pnpm của user đã nằm trong PATH.

## Các task tiếp theo

Giữ yêu cầu mới: T02 bàn giao script + RUN-T02.md rồi push, tiếp tục T03–T12 không chờ log GPU; không ghi parity đạt trước khi có log. Chỉ T13/T14 cần phối hợp trực tiếp theo chỉ dẫn người dùng. Spec chỉ archived khi toàn bộ chức năng và nghiệm thu đạt, có commit/log; các UI mô phỏng hiện tại chưa đủ để archive FG-AUTH-001/FG-EMP-001.
