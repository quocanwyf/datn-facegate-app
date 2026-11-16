# T14 — Chạy demo chung và đo thật

**Chưa đạt nghiệm thu T14.** Máy hiện báo Intel UHD, PyTorch 2.11.0+cpu, CUDA false; chưa có bộ quay T13 và 20 lượt kiosk thật. Không cài CUDA/NVIDIA driver thay cho một GPU NVIDIA chưa phát hiện.

Tất cả lệnh dưới chạy từ `D:\WorkSpace\DATN\datn-facegate-app\03-app\hub`, trừ bước build web.

## Demo chung web + app

1. Tại thư mục web: `& "$env:APPDATA/npm/pnpm.cmd" build`.
2. Tại hub: `.venv/Scripts/python.exe scripts/start_demo.py --resume --device cpu`.
3. Web **http://127.0.0.1:8000/login**; app AVD dùng **http://10.0.2.2:8000**, ghép mã/QR từ Cửa & thiết bị của chính web này. Cả hai dùng một Hub/DB T14. Web cũ 5173/Hub8012 là review riêng, không đổi dữ liệu của phiên đó.
4. Khi có CUDA và T13 đã bật hợp lệ: thêm `--require-liveness`, chọn `--device cuda`. Launcher không tự hạ sang CPU.
5. Nếu chưa có context T14 thì bỏ `--resume` để tạo bản sao T08 mới; nguồn T08 và các clone cũ giữ nguyên. Nếu cần máy khác: `--host 0.0.0.0 --public-url http://<IP-LAN-Hub>:8000`; chỉ mở cổng LAN theo máy demo khi thực hiện cấu hình mạng. Codex chưa tự đổi tường lửa.

Kịch bản 5–7 phút: [kich-ban-demo.md](../../kich-ban-demo.md). Cần chuẩn bị lượt vào/ra trước buổi demo, cách nhau ≥30 phút; không đổi giờ hoặc chèn event giả để rút một ca còn vài phút.

## Cổng GPU

```powershell
& .venv/Scripts/python.exe scripts/preflight_t14.py --output ../ket-qua-kiem-thu/2026-11-16_T14/hardware.json
```

Chỉ tiếp tục bảng đo GPU khi cuda_available/gpu_gate_passed true và mô hình qua bốn bước xác minh. Nếu chỉ có Intel UHD, chọn chạy review CPU hoặc dùng máy NVIDIA phù hợp; không đánh dấu tiêu chí CUDA đạt.

## Pipeline p50/p95 với 1 và 3 kiosk

Benchmark tự khởi động Hub riêng port8014, tạo cửa/thiết bị bằng API thật trên DB clone T14; kiosk_sim đọc ảnh ngoài repo, nhận diện và ghi event theo luồng thật. Không chèn trực tiếp event/vector/ngày công. Thiết bị thử được revoke khi xong. Đo stage opt-in trong worker, sync CUDA để không tính mỗi thời gian enqueue.

Sau khi T13 có báo cáo, phê duyệt và L trên đúng clone T14:

```powershell
$chosenL = [double](Read-Host 'L đã được bạn chốt ở T13')
& .venv/Scripts/python.exe scripts/benchmark_t14.py --resume --images D:/WorkSpace/DATN/U03 --device cuda --clients 1 3 --frames 300 --threshold $chosenL --demo --output ../ket-qua-kiem-thu/2026-11-16_T14/gpu-benchmark-real.json
```

`--images` là bộ ảnh đã được đồng ý dùng để benchmark nhận dạng; đo tấn công chống giả mạo cần dữ liệu camera T13 riêng. `--demo` chỉ dùng tài khoản demo trên clone T14 được script kiểm prefix; không đưa mật khẩu thật vào command line. Cũng có thể dùng biến FACEGATE_REVIEW_PASSWORD hoặc nhập kín.

Script cần ≥300 khung **mỗi kiosk** ở cả cấu hình 1/3, trừ warmup. Báo cáo n riêng cho decode/YuNet/liveness/embed/top1/decision: khung không hợp lệ hoặc không đi hết pipeline không được biến thành 0 ms. RTT gồm WS/queue/DB, khác thời gian worker. RAM là peak process; VRAM là peak allocated/reserved của PyTorch, không phải VRAM toàn hệ thống. Không diễn giải 300 khung có nhiều lần giữ trạng thái như 300 phép embed độc lập.

Tiền kiểm CPU đã chạy 20 khung với 1 kiosk và 60 khung với 3 kiosk, liveness tắt; xem cpu-smoke.json. Mẫu nhỏ/chạy cùng các ứng dụng và test khác nên **không phải benchmark hiệu năng được kiểm soát**, không thay phép đo GPU. `gpu_benchmark_criteria_met=false` được ghi rõ.

## 20 lượt đứng vào → kết quả trên kiosk thật

Thư mục riêng đã chuẩn bị: `D:\WorkSpace\DATN\facegate-private\T14`, có CSV trống `kiosk-trials.csv`:

```text
trial_id,video,enter_sec,result_sec,result
```

Quay màn hình kiosk và cảnh người đi vào đủ thấy mốc, có đồng ý; giữ video ngoài repo. Mỗi hàng một lượt độc lập, video tương đối trong thư mục T14, enter_sec khi mặt vào vùng quét, result_sec khi kết quả đầu tiên đọc được trên UI. result là OK/ALREADY/DENY đúng video, không điền số minh họa. Hai lượt không chồng nhau trong cùng video. Ghi sai số theo fps/người đánh dấu.

```powershell
& .venv/Scripts/python.exe scripts/measure_kiosk_trials.py --data D:/WorkSpace/DATN/facegate-private/T14 --csv D:/WorkSpace/DATN/facegate-private/T14/kiosk-trials.csv --conditions 'Điền kiosk/camera/ánh sáng thật' --output ../ket-qua-kiem-thu/2026-11-16_T14/kiosk-20-real.json
```

Script kiểm đủ ≥20 lượt, video thật tồn tại/đọc được, mốc trong thời lượng, không trùng/chồng; chỉ xuất tổng hợp và digest nguồn, không video/ảnh. Đây là đo bằng đánh dấu thủ công, không giả định RTT = độ trễ đứng vào.

## Chốt nghiệm thu

Chạy đủ từng cảnh trong kich-ban-demo.md, ghi PASS/FAIL/CHƯA CHẠY cùng thời điểm/build và đường dẫn video riêng. Hoàn tất T02/T08 còn thiếu, T13 báo cáo/L/video, cổng CUDA, ≥300 khung mỗi cấu hình, 20 lượt kiosk thật và kiểm quyền cuối. Chưa có bằng chứng thì để pending; không archive spec tích hợp/chống giả mạo chỉ vì script đã xong.
