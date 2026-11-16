# T13 — Quay và hiệu chỉnh chống giả mạo

**Đã có mã tích hợp; chưa có dữ liệu thật 4 nhóm, chưa có L được chốt, chưa bật chống giả mạo.** Bộ quay trống đã được tạo tại:

`D:\WorkSpace\DATN\facegate-private\T13-20261116`

Ảnh/video người tham gia chỉ ở thư mục này ngoài repo. Không dùng bộ chân dung U03/U04 làm nhãn mặt thật/giả cho T13; chúng chỉ được dùng trước đó để kiểm pipeline nhận dạng.

## 1. Chuẩn bị bộ quay (khoảng 20 lượt/người)

1. Mở `metadata.json` trong thư mục trên; điền `conditions.camera`, `lighting`, `distance` bằng điều kiện thực tế. Policy mặc định đang khớp seed: cạnh 640/JPEG80/mặt80/yaw0.35, 4fps, W5/MATCH3/UNKNOWN4/SPOOF3. Nếu Hub khác, xuất/đối chiếu cấu hình và sửa policy trước khi quay.
2. Dùng mã ẩn danh U01. Chỉ đổi `participants.U01.consent` sang true **sau khi người tham gia đồng ý thử/quay**. Thêm U02 tương tự nếu có người thứ hai; không ghi tên/số điện thoại vào repo.
3. Dùng **chính camera dự định chạy kiosk**, cùng khoảng cách/ánh sáng. Nếu camera qua AVD khác webcam trực tiếp, phải thu qua đúng đường camera đó hoặc ghi rõ đây mới là tiền kiểm webcam; không dùng kết quả khác camera để kết luận kiosk đạt.
4. Mỗi người: mỗi nhóm 3 lượt calibration + 2 lượt validation = 20 video độc lập, khoảng 3 giây/video. Validation quay lại thật, không copy/đổi tên video calibration. Nếu muốn tăng N, tăng số người/lượt; đây vẫn là kiểm thử chức năng nội bộ.

| Nhóm | Cách tạo lượt |
|---|---|
| live | Người thật đứng trước camera, mặt rõ/tư thế hợp lệ. |
| print | Đưa bản ảnh **in trên giấy** vào camera; không dùng file ảnh gốc thay video quay giấy. |
| phone | Camera quay **ảnh tĩnh hiển thị trên điện thoại**. |
| replay | Camera quay **video khuôn mặt phát lại trên màn hình**, khác nhóm ảnh tĩnh. |

Tại `D:\WorkSpace\DATN\datn-facegate-app\03-app\hub`, ví dụ quay nhóm mặt thật:

```powershell
& .venv/Scripts/python.exe scripts/collect_liveness.py capture --data D:/WorkSpace/DATN/facegate-private/T13-20261116 --participant U01 --group live --split calibration --trials 3 --seconds 3 --camera 0 --consent
& .venv/Scripts/python.exe scripts/collect_liveness.py capture --data D:/WorkSpace/DATN/facegate-private/T13-20261116 --participant U01 --group live --split validation --trials 2 --seconds 3 --camera 0 --consent
```

Preview hiện nhóm/split. **Space** bắt đầu từng lượt, **Esc** dừng. Chuẩn bị giấy/điện thoại/video đúng nhóm rồi lặp hai lệnh với `--group print`, `phone`, `replay`. Không tự gán cùng một bản quay cho nhiều nhóm. Manifest trials.csv được ghi khi lượt quay hoàn tất; lượt bị ngắt không được tính.

Nếu dùng camera khác đường truyền app, thu video ngoài repo bằng đường camera kiosk thật và thêm manifest theo header `participant,group,split,trial,path`; path tương đối trong bộ quay. Ghi mã lượt độc lập/nhóm đúng thực tế.

## 2. Hiệu chỉnh và xem báo cáo

```powershell
& .venv/Scripts/python.exe scripts/calibrate_liveness.py --data D:/WorkSpace/DATN/facegate-private/T13-20261116 --output ../ket-qua-kiem-thu/2026-11-16_T13/calibration-real.json --device cpu
```

Chỉ dùng `--device cuda` khi phần cứng/runtime đã có CUDA. Script lấy khung theo max_fps, resize/JPEG giống Hub, kiểm đúng một mặt, YuNet/tư thế, crop 2.7/4.0 80×80 và ensemble thật. Lượt quá ít khung hợp lệ, nhóm thiếu, video trùng hoặc thiếu consent bị từ chối; không tạo tỷ lệ 0% cho nhóm rỗng.

Báo cáo chỉ chứa số người/lượt/khung, điều kiện, phân vị p_live và tỷ lệ chặn/cho qua theo L ở hai split. **Tỷ lệ tính theo khung hợp lệ; các khung cùng video tương quan**, không được trình bày thành lượt độc lập hay kết quả nghiên cứu. Chưa có khoảng tin cậy/chứng nhận PAD. Mức đề xuất chỉ dùng calibration (live accept≥90%, mỗi nhóm attack accept≤5%); nếu không có mức đạt thì trả null, cần xem dữ liệu/cấu hình/mô hình thay vì bịa L. Validation là đối chiếu độc lập; cuối cùng người dùng chọn L.

## 3. Người dùng chốt L, rồi mới bật

Đọc cả hai split trước. Codex chưa chọn L thay bạn. Với Hub demo T14:

```powershell
$reviewContext = Get-Content "$env:LOCALAPPDATA/FaceGate/T14-review-context.json" -Raw | ConvertFrom-Json
$chosenL = [double](Read-Host 'Ngưỡng L bạn chốt sau khi xem báo cáo thật')
& .venv/Scripts/python.exe scripts/approve_liveness.py --report ../ket-qua-kiem-thu/2026-11-16_T13/calibration-real.json --data-dir $reviewContext.data_dir --threshold $chosenL --approved-by NMinH
```

CLI ghi marker trong **HUB_DATA_DIR của đúng Hub**, không tự thay DB. OWNER vào **Cấu hình nhận dạng → Chống giả mạo**, nhập đúng L đã chốt, bật và lưu. HR chỉ xem. Hub kiểm marker, bundle/hash, policy và L; không đúng trả 422 và giữ nguyên toàn bộ cấu hình. Đổi W/fps/crop/JPEG/ngưỡng khung sau phê duyệt cần hiệu chỉnh/chốt lại. Không copy marker test trong thư mục pytest sang triển khai.

Nếu dùng phiên web review 8012 thì context là `T12-test-context.json`; không nhầm với `T14-review-context.json`. Quét và web phải cùng Hub/DB. Để demo chính thức, dùng launcher và URL trong RUN-T14.

## 4. Nghiệm thu thật còn lại

- Quay lại mặt thật/ảnh in/ảnh điện thoại/video replay trên **app/kiosk thật**, đủ số lượt và ghi kết quả OK/DENY/SPOOF thực tế.
- Với mẫu giả bị chặn: kiosk hiển thị DENY/SPOOF, cửa không mở, không công; W10 có SPOOF và p_live_min. Không gọi file ảnh được replay trực tiếp là bằng chứng camera chống giả mạo.
- Khi tắt cờ: xác nhận luồng nhận dạng còn hoạt động. Mã đã có regression tự động, nhưng video app thật vẫn cần quay.
- Lưu video riêng ngoài Git; chỉ thêm số liệu tổng hợp/metadata được phép vào báo cáo. Chỉ sau khi có báo cáo, L chốt và video mới đánh dấu T13 đạt/archived.
