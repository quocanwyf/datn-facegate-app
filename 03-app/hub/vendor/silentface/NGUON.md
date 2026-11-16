# Silent-Face-Anti-Spoofing — nguồn T13

- Upstream: https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- Commit ghim: **b6d5f04ad78778917853b25c778acef6d5626d15**, lấy 16/11/2026.
- License gốc Apache-2.0 được giữ nguyên trong LICENSE. Tree commit có một LICENSE cấp repo, không có giấy phép/NOTICE riêng khác cho hai `.pth` trong tree đã kiểm. Hai trọng số được lấy nguyên từ resources/anti_spoof_models của commit này, không lấy từ nguồn chia sẻ khác.
- Chỉ sao chép các file kê trong manifest.json; mã upstream giữ byte gốc, không sửa code/mô hình nhận dạng thuộc MANIFEST.sha256 T01. Git trên Windows không checkout được tên thư mục log có dấu cách cuối: dùng `git show COMMIT:path` lấy blob đã ghim, không đổi tên/sửa payload nguồn.
- SHA-256 mã, license và trọng số trong manifest.json; verify_bundle kiểm trước import/load. Tệp model dùng `torch.load(weights_only=True)`, strict state_dict, bỏ prefix module. đúng upstream.

## Đối chiếu mã

| Hạng mục | Mã nguồn ghim | Tích hợp |
|---|---|---|
| Crop rộng 2,7 và 4,0, resize 80×80 | [test.py L48–62](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/b6d5f04ad78778917853b25c778acef6d5626d15/test.py#L48), generate_patches.py L15–68 | Dùng nguyên CropImage, cùng xử lý cạnh ảnh và lát cắt có điểm cuối. Không dùng ảnh align 112×112 cho liveness. |
| Kiến trúc | src/model_lib/MiniFASNet.py; anti_spoof_predict.py L72–90; utility.get_kernel | MiniFASNetV2 và MiniFASNetV1SE, conv6_kernel=(5,5); tải một lần trong worker. |
| Đầu vào | [functional.py L37–60](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/b6d5f04ad78778917853b25c778acef6d5626d15/src/data_io/functional.py#L37), anti_spoof_predict.py L98–112 | numpy OpenCV **BGR**, CHW float32 giá trị **0–255**, không /255. Docstring ToTensor nói [0,1] nhưng mã thực thi trả img.float(); parity bám mã chạy. |
| Ensemble/nhãn | test.py L62–69; anti_spoof_predict.py L107–112 | Cộng softmax 3 lớp của hai mô hình, chia 2; lớp **1** là thật. p_live = trung bình xác suất lớp 1, không dùng confidence của nhãn argmax (có thể là fake). |
| Detector | detector.py dự án | Giữ YuNet/bbox lớn nhất theo đặc tả, không mang RetinaFace Caffe upstream sang Hub. Đây là khác biệt cấu hình phải hiệu chỉnh bằng camera thực tế. |

T13 chưa có dữ liệu quay 4 nhóm/chưa chốt L. Không tự bật nhận dạng chống giả mạo. Test parity dùng ảnh nhiễu tổng hợp để so phép tính, không dùng làm hiệu chỉnh hay bằng chứng độ chính xác.

Mã upstream dùng mô hình RGB thụ động, kết quả phụ thuộc camera/ánh sáng/tư thế theo README gốc; không trình bày như chứng nhận chống giả mạo. Chỉ dùng trong bản trình diễn nghiên cứu đã mô tả.
