# Báo cáo T08 — Kiosk App Android

- Trạng thái: **XONG MỘT PHẦN** — APK native chạy thật; ghép → PIN → consent → 5 mẫu → web duyệt → OK/ALREADY, người khác DENY, mất Hub và tự nối lại đã kiểm bằng camera phát lại ảnh được đồng ý. Còn thiếu video liền luồng và 10 lượt người thật.
- Commit: chưa commit/push T08; chưa chuyển spec sang archived.
- Máy chạy: Windows, CPU; phiên bản thật trong `environment.log`.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Số đo / kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | `tsc --noEmit` sạch; test `KioskSocket` pass | TypeScript không lỗi; 14 test, 14 pass, 0 fail | `typecheck-final.log`, `socket-tests-final.log` | Đạt |
| 2 | Video ghép → 5 mẫu → web duyệt → OK → người khác DENY → tắt/bật Hub | Luồng chức năng đã chạy trên AVD và Hub thật bằng U03/U04 phát lại; có video từng đoạn, thiếu video đầy đủ ghép→5 mẫu | `gradle-build-short-paths.log`, `apk-signature.log`, `adb-install-ready.log` | Chưa đạt |
| 3 | 10 lượt người thật vào khung → kết quả trên CPU | Chưa đo; không suy diễn từ unit test, ảnh phát lại hoặc log JPEG | — | Chưa đạt |
| 4 | Không màn nào hiện ảnh khuôn mặt, ngoại trừ preview camera trực tiếp | Code dùng preview và JPEG trong RAM, không có màn ảnh chân dung; còn cần kiểm bằng video native | Source `src/camera`, `src/screens` | Đã kiểm màn result/offline; còn thiếu video toàn bộ màn |
| Q | Disconnect 3s / im lặng 15s / backoff / NO_GALLERY / unavailable | Đã kiểm bằng đồng hồ và WS giả; 14 test gồm hồi phục trước mốc 3s, stop-and-wait, hold kết quả, token bị thu hồi | `socket-tests-final.log` | Đạt ở mức unit; native còn kiểm |
| Q | Hủy enroll giữ hồ sơ cũ | App không gọi API rút đồng ý khi hủy; bỏ khung đang xử lý của scope cũ | Source `App.tsx`, `CameraFeed.tsx` | Chưa quay lại luồng native |

## Đã làm

- Expo dev build, React Native/TypeScript strict; camera trước VisionCamera, quét QR, font Inter, SecureStore, cleartext LAN và âm thanh có nguồn.
- Các màn K-01/02/04/05/06/07/08/09/11; chọn tài khoản có PIN, tìm nhân viên, consent, 5 mẫu và trạng thái chờ duyệt; phân biệt hủy chụp với rút đồng ý.
- `KioskSocket`: auth đầu kết nối, header/JPEG liền nhau, stop-and-wait theo seq, max_fps, BUSY, hold kết quả, heartbeat, watchdog, backoff, phục hồi gallery và thu hồi token.
- Sửa heartbeat khi có frame giữa hai nhịp: lập lịch theo thời điểm gửi cuối, tránh chờ tới 20s rồi bị timeout Hub 15s. Có regression test riêng.
- Bundle Android bằng Metro thành công (`metro-export.log`). Đây chưa phải APK/build native thành công.
- APK native: **BUILD SUCCESSFUL**, 755 tác vụ (723 thực thi, 32 đã cập nhật), 34 phút 1 giây; `gradle-build-short-paths.log`. APK 107.677.797 byte, hash và đường dẫn ở `apk-artifact.json` / `apk-sha256.json`; xác minh chữ ký v2 thành công (`apk-signature.log`). APK nằm trong thư mục build bị Git bỏ qua, không commit.
- Đã cài APK vào AVD (`adb-install-ready.log`: Success). Lần cài đầu gọi quá sớm khi Android chưa khởi động xong; giữ log thất bại riêng, lần sau kiểm dịch vụ package/boot rồi cài lại.
- Script DB nghiệm thu mới từ schema/seed chính thức; `--resume` giữ nguyên DB và dữ liệu khi tắt/bật Hub. Đã khởi động thật, health báo DB/model hợp lệ, gallery rỗng (`hub-first-start.log`, `hub-health.json`).
- Kịch bản review: `REVIEW-T08.md`. Ảnh U03/U04 chỉ dùng ở thư mục riêng ngoài Git. Video từ ảnh thật ghi rõ **camera replay**, không thay kiểm thử người thật hoặc chống giả mạo T13.

## File đã tạo / sửa

`03-app/kiosk/`: cấu hình Expo/TS, package/lock, `App.tsx`, `index.ts`, camera, màn hình, theme sao chép token, controls, WS/types/tests, REST client, SecureStore, âm thanh và script nghiệm thu.

## Vấn đề gặp + cách xử lý

- Bộ công cụ native lần đầu cần Gradle 9.4.1, platform Android 37.0 và JDK 17 toolchain. Java tải artifact lớn rất chậm; dùng tải chính thức bằng curl và đối chiếu SHA-256 cho Gradle/JDK, không thay bằng bản không rõ nguồn. Xem `gradle-download-check.log`, `jdk-download-check.log`, các log build giữ nguyên.
- JDK chạy Gradle là JBR 21; toolchain biên dịch plugin là Temurin 17. Cấu hình máy nằm ngoài repo trong `D:\.gradle-facegate`.
- Lượt `gradle-build-jdk17.log` đã biên dịch plugin nhưng dừng với CXX1101: NDK 27.1 được tải dở, thiếu `source.properties`. Đang cài lại đúng NDK bằng công cụ Android chính thức (`ndk-install.log`), chưa tuyên bố APK build thành công.
- Đã cài lại NDK thành công. Lượt native tiếp theo chạy 440 tác vụ (408 thực thi, 32 đã cập nhật), dừng ở Ninja 1.10.2: đường dẫn Nitro Modules quá dài và lỗi manifest lặp. Ninja có [hỗ trợ đường dẫn Windows dài từ 1.12](https://github.com/ninja-build/ninja/releases); helper `kiosk/tests/prepare_windows_build.ps1` tải [1.13.2 chính thức](https://github.com/ninja-build/ninja/releases/tag/v1.13.2), kiểm SHA-256, giữ bản gốc và cập nhật công cụ SDK. `ninja-setup.log` là output thật; đang build lại trong `gradle-build-ninja113.log`. Không sửa nguồn Nitro/Expo/React Native.
- Ninja mới vượt lỗi C++, nhưng Windows không khởi chạy được `prefab_command.bat` của thư viện QR ở đường dẫn dài 262 ký tự. Đặt `virtualStoreDirMaxLength: 40` trong workspace Kiosk theo [cấu hình pnpm chính thức](https://pnpm.io/settings), cài lại offline với frozen lockfile (`pnpm-short-paths-install.log`), giữ cache cũ ngoài repo. Lượt `gradle-build-short-paths.log` đã thành công.
- `kiosk/tests/build_android.ps1` dùng jobserver Windows của Ninja và 1 worker Gradle để giới hạn compiler còn 2. Mẫu kiểm tra thật ở `build-memory-sample.json`; không chạy AVD/Hub đồng thời trong bước build nặng. Helper nhắm `:app:assembleDebug` để những lần sau không đóng gói AAR không cần thiết.
- Đã kiểm camera phát lại ảnh thật bằng app Camera có sẵn trong AVD; bằng chứng gốc nằm ngoài Git, hash/path ở `private-camera-evidence.json`. Camera2 có sẵn bị lỗi khi tắt hẳn camera sau, nên giữ camera sau emulated như hướng dẫn dự án. AVD dùng `-lowram -memory 2048 -skin 1280x800`, `wm density 160`, SwiftShader và tắt Vulkan; RAM thật khoảng 2 GB. Profile tablet gốc tự nâng RAM lên 4 GB gây ANR. AI Hub vẫn chạy CPU. Video ngắn hết sẽ rơi về hình camera mẫu: đã tạo video ảnh thật dài 17–18 phút để không dùng hình mẫu ấy trong phép thử nhận dạng.
- OpenAPI generator hiện yêu cầu TypeScript 5, app SDK dùng TypeScript 6: tách generator qua pnpm dlx, không đổi hợp đồng hoặc file schema sinh ra. Xem log generator/peer dependencies.
- Máy có khoảng 8 GB RAM; không chạy đồng thời Gradle, Hub và AVD khi build nặng. Hub nghiệm thu đầu tiên đã dừng để nhường RAM; khởi động lại bằng `--resume`.

## Đề xuất cho thiết kế

Chưa có thay đổi đặc tả. Chưa công bố đạt T08 hoặc archive chức năng khi thiếu video/số đo.

## Cần An làm

Chưa cần thao tác từ An ở bước build này. Phần T13/T14 vẫn theo lịch ngồi chung đã thống nhất. Kịch bản người thật 10 lượt ở T08 còn chưa được thực hiện; không đánh dấu đạt bằng dữ liệu phát lại.

## Kết quả native bổ sung

- Ghép 200, tạo phiên PIN 201, consent 200 trên Android; JPEG được gửi từ snapshot RAM của VisionCamera. Hub loại POSE/TOO_SIMILAR, nhận đủ 5 mẫu và K09 hiển thị sent (log Metro).
- `native-web-approval.json`: duyệt bằng UI web thật, 5 mẫu của NV006, HTTP 200, gallery_size=1. Ảnh W08 đã che toàn bộ mẫu trước khi lưu vào repo.
- `native-evidence.json`: ghi số đo JPEG→result thực tế và hash video riêng. Đây là dữ liệu camera phát lại, không phải 10 lượt người bước vào webcam. Có OK/ALREADY cho U03, DENY cho U04; xem ảnh K04 không có ảnh chân dung.
- Tắt tiến trình Hub: K11 hiện mất kết nối, tự retry. `hub-recovery.log` khởi động lại cùng DB, WS được chấp nhận; Metro ghi offline→scan→DENY, không ghép lại.
- Sửa lỗi thực tế: K01 theo AppState và xử lý lỗi camera; PIN giữ dữ liệu đồng bộ để tránh mất chữ số khi bấm nhanh; tăng bề rộng nút tránh xuống dòng Không đồng ý; hiệu ứng fade K01 dùng shared value thay layout entering; native Button dùng màu token; import từng icon để giảm bundle.
- Helper ADB kiểm đúng app/vùng hiển thị trước khi chạm; không gọi React handler. Không chạy hai lệnh UI dump đồng thời (Android chỉ cho một UiAutomationService).
- Deep import Phosphor 3.0.6 làm TypeScript kiểm cả nguồn thư viện: thêm khai báo metadata SVG className tùy chọn; không tắt strict hay sửa node_modules. TypeScript sạch, 14 test socket pass sau sửa.
- Chưa archive spec Kiosk vì chưa đủ bằng chứng nghiệm thu. Không có yêu cầu người dùng ngồi chung ở giai đoạn này; tiếp tục các task phần mềm độc lập trong kế hoạch.
