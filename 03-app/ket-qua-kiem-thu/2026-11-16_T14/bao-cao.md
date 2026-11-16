# T14 — Tích hợp và demo

**Trạng thái: đã có launcher, công cụ đo, kịch bản và tiền kiểm; chưa nghiệm thu/không archived.** Chưa đủ T02/T08/T12 Android/T13 và các bằng chứng vật lý/GPU cuối.

## Đã làm và bằng chứng

| Phần | Kết quả thực tế |
|---|---|
| Web/app cùng backend | start_demo.py phục vụ web build và API cùng port8000, DB/kho T14 clone riêng. Web200, DBtrue, modelverified true/gallery1; unauth employees401 và unknown API404. [shared-demo-check.json](shared-demo-check.json). App cần ghép đúng Hub này; chưa quay toàn luồng app mới ở T14. |
| Hardware/GPU | [hardware.json](hardware.json): Windows11, Intel UHD Graphics, torch2.11.0+cpu, CUDAfalse/không NVIDIA được phát hiện. Cổng benchmark CUDA dừng rõ ràng, [gpu-gate.log](gpu-gate.log); không tự chuyển CPU để báo GPU đạt. |
| Pipeline/WS tiền kiểm | [cpu-smoke.json](cpu-smoke.json): 1 kiosk 20 khung, 3 kiosk 60 khung, 0 lỗi WS; ảnh U03 đã đồng ý ngoài repo, mô hình/DB/WS thật, liveness tắt. [cpu-policy-smoke.json](cpu-policy-smoke.json): chạy lại đường commit sau bảo vệ policy, 5 khung đo/0 lỗi. |
| Tính chất số đo | Mẫu ngắn CPU, chạy cùng ứng dụng/test khác, có ảnh không hợp lệ/khung giữ trạng thái; không là benchmark hiệu năng được kiểm soát. N mỗi stage khác nhau và được báo riêng. gpu_benchmark_criteria_met=false; không thay GPU≥300 khung/cấu hình. |
| 20 lượt kiosk | Có measure_kiosk_trials.py và CSV trống ngoài repo tại facegate-private/T14. Dữ liệu thiếu bị chặn, không tạo kiosk-20-real.json. **Chưa có phép đo người đứng vào thật**. |
| Demo5–7phút | [kich-ban-demo.md](../../kich-ban-demo.md): thứ tự, người làm, câu nói, chuẩn bị lượt vào/ra ≥30 phút, xử lý lỗi và các cảnh còn cần quay. Chưa có bằng chứng toàn bộ cảnh đã chạy. |
| Security review | [SECURITY-REVIEW.md](SECURITY-REVIEW.md), inventory/caller report, các guard và regression. Rà soát tập trung của cùng Codex, không audit độc lập. |

## Đối chiếu AC còn lại

1. **Bảng GPU p50/p95 ≥300 khung cho 1/3 kiosk + RAM/VRAM:** chưa đạt, CUDA chưa sẵn sàng; script đã có. Đọc số đo CPU đúng nhãn, không nhập số mô phỏng vào bảng GPU.
2. **Mọi kịch bản đầu-cuối có ảnh/video:** chưa đủ. Cần T13 quay thực, 20 lượt UI kiosk thật, đăng ký/duyệt/chấm công/quyền cửa/nghỉ việc trên cùng Hub demo. Dữ liệu event trước đó T08/T11 hoặc fixture API không thay video tích hợp T14.
3. **Kịch bản demo:** đã viết; chưa diễn tập có ghi hình.
4. **Lỗi/giới hạn:** danh sách dưới; chưa tuyên bố app hoàn tất.

## Vấn đề / ảnh hưởng demo

| Vấn đề | Ảnh hưởng / cách tiếp tục |
|---|---|
| Không phát hiện CUDA/NVIDIA, chỉ Intel UHD | Chặn nghiệm thu cấu hình GPU theo plan. Review CPU được; muốn giữ tiêu chí CUDA cần phần cứng/runtime phù hợp hoặc người dùng chốt thay đổi plan riêng. Chưa tự đổi mục tiêu. |
| Chưa quay 4 nhóm, chưa L/video SPOOF | Chặn kết luận chống giả mạo. Giữ cờ tắt; quay theo RUN-T13, xem report và người dùng chốt L. |
| Chưa20lượt/khungGPU300 | Chưa có số đo p50/p95 UI kiosk và GPU chính thức. Không coi RTT/pipeline CPU là độ trễ người đứng vào. |
| T02 parity riêng/T08video+CPU thiết bị/T12ảnhAndroid còn chờ | Cần bổ sung trước khi chốt hệ thống. Giữ báo cáo từng task, không archive sớm. |
| Vite chunk >500kB, vendor deprecation warnings | Build chạy được; chưa đo startup/jank/mạng điện thoại. Không sửa vendor frozen để xóa warning. |
| Liveness nhạy camera/ánh sáng, demo upstream khác detector | Phải hiệu chỉnh trên đường camera thật của kiosk; số liệu webcam khác chỉ tiền kiểm. Không chứng nhận PAD hoặc dùng thương mại. |

Hướng dẫn chạy chung, phép đo và dữ liệu cần quay: **[RUN-T14.md](RUN-T14.md)**. Web review 5173/8012 và dữ liệu gốc T08 được giữ riêng; dùng URL8000/QR8000 để thử tích hợp T14.
