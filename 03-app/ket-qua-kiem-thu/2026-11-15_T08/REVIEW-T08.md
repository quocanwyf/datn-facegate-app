# Kịch bản review T08 — Kiosk Android

Đã kiểm chức năng bằng Android native và Hub thật với camera phát lại U03/U04. Còn thiếu video liền luồng và 10 lượt người thật; xem `bao-cao.md` và `native-evidence.json`.

## Chuẩn bị

Mở PowerShell tại `D:\WorkSpace\DATN\datn-facegate-app`. Máy cần PostgreSQL đang chạy, checkpoint đã kiểm tra và AVD `FaceGate_PixelTablet_API34` (camera trước `webcam0`). Không dùng Expo Go. Tắt các tiến trình Hub cũ trên cổng 8000 trước khi chạy Hub nghiệm thu.

Nếu cần build lần đầu, làm bước build Terminal 3 trước khi mở Hub/AVD để đủ RAM. Với APK đã có, mở các terminal dưới đây.

Terminal 1 — tạo DB nghiệm thu mới từ schema/seed chính thức, chạy Hub CPU; không thay DB đang dùng:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app
$env:PYTHONUTF8 = '1'
& .\03-app\hub\.venv\Scripts\python.exe .\03-app\kiosk\tests\start_real_hub.py
```

Terminal 2 — web quản trị, dùng proxy mặc định tới Hub 8000:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app\03-app\web
& "$env:APPDATA\npm\pnpm.cmd" dev --host 127.0.0.1
```

Terminal 3 — Kiosk dev build; lần đầu cần SDK Android và tải công cụ native:

```powershell
Set-Location D:\WorkSpace\DATN\datn-facegate-app\03-app\kiosk
$env:ANDROID_HOME = 'C:\Developer\Tools\Android\SDK'
$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'
$env:GRADLE_USER_HOME = 'D:\.gradle-facegate'
$env:Path = "$env:JAVA_HOME\bin;C:\Program Files\nodejs;$env:APPDATA\npm;$env:Path"
& "$env:APPDATA\npm\pnpm.cmd" install --frozen-lockfile
& 'C:\Program Files\nodejs\npx.cmd' --yes @expo/agent-cli@latest prebuild --platform android --no-install
& .\tests\prepare_windows_build.ps1 -Sdk $env:ANDROID_HOME
& .\tests\build_android.ps1 -Sdk $env:ANDROID_HOME
& 'C:\Program Files\nodejs\npx.cmd' --yes @expo/agent-cli@latest run:android --binary .\android\app\build\outputs\apk\debug\app-debug.apk --device FaceGate_PixelTablet_API34
```

Script chuẩn bị Windows tải Ninja 1.13.2 từ bản phát hành chính thức, kiểm SHA-256 rồi cập nhật Ninja của CMake 3.22.1; giữ bản gốc ở `D:\.gradle-facegate\tools\ninja-sdk-3.22.1-original.exe`. Bước này xử lý đường dẫn C++ dài của pnpm trên Windows. Nếu đã cài dev build, chỉ cần mở AVD rồi chạy `npx --yes @expo/agent-cli@latest start --dev-client`; mở FaceGate và chọn Metro của máy dev. Nếu cài SDK ở nơi khác thì thay `ANDROID_HOME`. Lỗi công cụ build phải được xử lý trước khi review giao diện.

Mở AVD bằng helper (RAM 2 GB, SwiftShader, không snapshot). Chạy ở thư mục gốc repo:

```powershell
& .\03-app\kiosk\tests\start_avd.ps1
$adb = 'C:\Developer\Tools\Android\SDK\platform-tools\adb.exe'
& $adb -s emulator-5556 wait-for-device
# Chờ getprop trả 1 trước khi mở app; boot thường mất 30–90 giây.
& $adb -s emulator-5556 shell getprop sys.boot_completed
& $adb -s emulator-5556 shell wm density 160
& $adb -s emulator-5556 shell 'input keyevent KEYCODE_WAKEUP; wm dismiss-keyguard; svc power stayon true'
```

Trong Terminal 3, nếu APK đã được cài:

```powershell
npx.cmd --yes @expo/agent-cli@latest start --dev-client --localhost --port 8081 --max-workers 1 --no-agent-skills --no-followups
```

Mở app bằng terminal khác:

```powershell
& $adb -s emulator-5556 shell "am start -a android.intent.action.VIEW -d 'facegate://?__expo_url=http%3A%2F%2F10.0.2.2%3A8081&__expo_disable_onboarding=1&__expo_disable_fab=1&__expo_disable_auto_launch=1' -p vn.ptit.facegate.kiosk"
```

K01 trên tablet thấp cần cuộn **trong thẻ trắng** để thấy nút Ghép thiết bị; không chạm thanh tác vụ Android. Nếu bàn phím che nút, đóng bàn phím rồi cuộn. PIN bấm lần lượt và kiểm tra đủ 4 chấm.

`build_android.ps1` dùng một worker Gradle và jobserver Windows để giới hạn Ninja còn 2 compiler, phù hợp máy dev khoảng 8 GB RAM. Không chạy Hub/AVD cùng lúc trong lần build native nặng đầu tiên; khi đã có APK, mở lại Hub bằng `--resume` và AVD rồi cài APK. Lần review sau chỉ cần Metro nếu không đổi native dependencies.

## Luồng chính

1. Web: đăng nhập `nv001@demo.local` / `Demo@123`. Để kiểm luồng ra vào của T08 trước T09, tạo cửa `T08 review` có chế độ **Chỉ ra vào (ACCESS_ONLY)**, chính sách cho phép mọi nhân viên đang hoạt động; tạo thiết bị cho cửa đó. Phần kết quả chấm công IN/OUT kiểm tiếp sau T09. Kiosk K-01: cấp quyền camera; nhập Hub `http://10.0.2.2:8000` và mã 6 số hoặc quét QR còn hạn. Kỳ vọng về màn quét, đúng tên cửa, đồng hồ và trạng thái kết nối. Mã hết hạn/sai phải có lỗi; nút khóa khi đang gửi.
2. Giữ góc phải trên màn quét **3 giây**. Chọn Chủ doanh nghiệp, nhập PIN `2468`. Kỳ vọng có danh sách nhân viên đang hoạt động; tìm `NV006`. Thử hủy ở đây: về quét, chưa tạo hồ sơ.
3. Mở lại đăng ký, chọn NV006. Đọc thông báo đồng ý. Chọn **Đồng ý**, chụp đủ 5 tư thế hợp lệ theo hướng dẫn. Mẫu bị loại phải có lý do và không tăng số chấm. Đủ 5 mẫu: hiện “Đã gửi”, sau 5 giây về quét. Chưa được nhận dạng nhân viên này trước khi duyệt.
4. Web: mở hàng chờ khuôn mặt, kiểm tra bộ mẫu của NV006, **duyệt** bằng tài khoản Owner. Trở lại camera: người vừa đăng ký đứng vào khung → K-04 OK, đúng tên/mã và thông tin theo chế độ cửa; không hiện ảnh chân dung. Sau thời gian hiển thị do Hub cấu hình, app tiếp tục quét.
5. Người khác đã đồng ý thử đứng vào khung → DENY/UNKNOWN, không hiện tên của NV006. Không dùng ảnh ngẫu nhiên, dữ liệu sinh hoặc sự kiện seed để thay bước này.
6. Tắt Hub bằng Ctrl+C. Mất kết nối rõ ràng chưa hồi phục sau 3 giây → K-11; app tự thử nối lại. Tại Terminal 1 chạy `& .\03-app\hub\.venv\Scripts\python.exe .\03-app\kiosk\tests\start_real_hub.py --resume` để dùng lại DB/dữ liệu; kỳ vọng tự trở về quét, không bắt ghép lại. Khi WS vẫn mở nhưng không nhận gì, K-11 phải hiện ở mốc 15 giây, không cộng thêm 3 giây; mốc này có kiểm thử đồng hồ giả riêng.
7. Web: thu hồi thiết bị. Kiosk phải xóa token SecureStore, về K-01. Tắt/mở app sau đó vẫn ở K-01.

## Hủy và đăng ký lại

- Tạo một bộ PENDING. Chọn lại nhân viên đó: có xác nhận chụp lại. Chụp 1–4 mẫu rồi **Hủy chụp** hoặc ngắt mạng; web vẫn còn bộ cũ. Chỉ khi bộ mới đủ 5 mẫu và lưu thành công mới thay PENDING.
- **Không đồng ý** là rút đồng ý/xóa dữ liệu sinh trắc theo đặc tả, khác **Hủy chụp**. Chỉ thử với nhân viên thử nghiệm đã chuẩn bị cho thao tác này.
- Hết phiên đăng ký hoặc để màn PIN không thao tác 30 giây: về quét; không báo “Đã gửi”. PIN/mã ghép sai quá số lần quy định phải báo khóa đúng phạm vi.

## Đo và lưu bằng chứng

Quay đủ luồng 1→6; video chứa camera/ảnh thật lưu riêng ngoài repo, bản đưa vào Git phải che vùng khuôn mặt. Ghi rõ thời điểm cắt/che và giữ hash bản gốc. Không đăng ảnh hoặc token thiết bị vào log.

Đo **10 lượt người thật bước vào khung → màn kết quả** bằng video có thời gian. Mỗi lượt chờ camera trở lại trạng thái sẵn sàng; ghi CPU, thời gian bắt đầu/kết thúc, kết quả và độ trễ thực. Chỉ ghi nhận CPU; không suy ra đã đạt mục tiêu GPU <2 giây. Log `FACEGATE_TIMING` là mốc khung JPEG hợp lệ đầu tiên → phản hồi; chỉ hỗ trợ chẩn đoán, không thay phép đo người bước vào khung.

`tests/prepare_camera_replay.py` có thể tạo video camera AVD từ các ảnh người đã đồng ý. Đây là kiểm tra tích hợp bằng **phát lại ảnh thật**, phải ghi đúng loại bằng chứng; không thay nghiệm thu người thật hoặc T13 chống giả mạo.
