# FaceGate — kịch bản demo 5–7 phút (T14)

**Chưa nghiệm thu T14.** Kịch bản có thể diễn tập bằng CPU; cấu hình chính thức theo plan cần CUDA, T13 đã chốt L và bằng chứng camera. Không dùng số đo CPU, replay ảnh mẫu hoặc fixture DB để thay các mốc này.

## Chuẩn bị trước buổi demo

- Cùng một Hub/DB T14 cho cả web và app. Build web: tại `03-app/web`, chạy `& "$env:APPDATA/npm/pnpm.cmd" build`.
- Tại `03-app/hub`: `.venv/Scripts/python.exe scripts/start_demo.py --resume --device cpu` để review chung CPU tại `http://127.0.0.1:8000/login`; app máy ảo trỏ `http://10.0.2.2:8000`. Đây không phải phiên review riêng port 5173/8012.
- Khi CUDA và T13 đã sẵn sàng: dùng `--device cuda --require-liveness`. Khác máy: `--host 0.0.0.0 --public-url http://<IP-LAN-Hub>:8000`, cùng Wi-Fi; tự cấu hình tường lửa theo máy demo, không công khai Internet.
- Không có context T14 thì bỏ `--resume` để tạo clone mới từ T08. Clone cũ và review T12 giữ nguyên. Không chạy hai Hub cùng port.
- OWNER `nv001@demo.local`, HR `nv002@demo.local`, MANAGER `nv005@demo.local`, EMPLOYEE `nv006@demo.local`, SECURITY `nv020@demo.local`; demo password `Demo@123`. Dùng cửa sổ riêng/đăng xuất khi đổi vai trò.
- Tối thiểu hai người đồng ý thử: một thuộc Kỹ thuật, một thuộc phòng khác; hồ sơ phải đăng ký/duyệt thật trên Hub demo. Người chưa có hồ sơ dùng luồng đăng ký trước, không thay vector cho cùng người thành hai danh tính.
- Cửa Chấm công: ATTENDANCE_ACCESS. Cửa Phòng máy chủ: RESTRICTED_DEPARTMENTS, chỉ Kỹ thuật. NV MANUAL dùng NV022. Ghép app bằng mã/QR tạo từ **Hub demo**, không dùng QR của Hub review khác.
- Chuẩn bị ngày công/lượt vào-ra thật trước buổi diễn: hai lượt cách nhau ít nhất 30 phút trong cửa sổ ca; ca đi muộn/quên ra cần ngày đã chốt. Không thể làm trôi 30 phút hoặc cả ca trong demo 7 phút. Không đổi đồng hồ, chèn event hoặc sửa timestamp để giả lượt quét. Nếu dùng sửa tay/giải trình, chỉ rõ nguồn Sửa tay/Đã giải trình.
- T13: quay đủ 4 nhóm/holdout, người dùng chốt L, ghi marker vào đúng HUB_DATA_DIR T14 rồi bật trên web cấu hình. Chưa xong thì nói rõ lớp chống giả mạo chưa nghiệm thu và bỏ phần kết luận bảo vệ của cảnh ảnh in.
- Mở sẵn W10/W09 và tab nhân viên; chuẩn bị một yêu cầu giải trình pending hợp lệ. Quay chứng cứ có đồng ý, giữ video/ảnh thật ngoài repo.

## Trình tự trình bày

| Thời gian | Ai / thao tác | Lời giải thích và bằng chứng |
|---|---|---|
| 0:00–0:30 | Người trình bày mở cấu hình/health, giới thiệu web + app cùng Hub | “Đây là bản trình diễn nghiên cứu; mọi dữ liệu đi qua Hub và PostgreSQL.” Nêu CPU/CUDA đúng runtime, trạng thái T13. |
| 0:30–1:25 | Nhân viên mới tại kiosk → người có PIN mở đăng ký → consent → 5 tư thế; OWNER duyệt W08 | “Ảnh mẫu chỉ vào gallery sau duyệt.” Không show ảnh mặt trong video repo; dùng bản quay riêng đã đồng ý. Nếu chưa đủ tư thế, không bấm duyệt giả. |
| 1:25–2:10 | NV đã duyệt đứng trước kiosk tại cửa chấm công; web W10 nhận event | Kiểm OK/IN hoặc ALREADY theo lượt thực, cửa/giờ/nhân viên; mở hôm nay để thấy công tạm thời. Trình bày lượt OUT thật đã quay trước ≥30 phút sau IN, không gọi quét lặp ngay là OUT. |
| 2:10–3:05 | Nhân viên mở ngày đi muộn/quên ra đã chốt → gửi giải trình; MANAGER khác người gửi duyệt | Đối chiếu giờ gốc/đề nghị, trạng thái pending→approved, nguồn Đã giải trình. Yêu cầu của quản lý chính phòng do HR duyệt; không tự duyệt. |
| 3:05–3:40 | OWNER/HR mở bảng công + Excel | Hai sheet Tổng hợp/Chi tiết; số ngày duy nhất, phút muộn, nguồn điều chỉnh; lịch sử event vẫn còn nguyên. |
| 3:40–4:25 | Người chưa đăng ký đứng trước kiosk → UNKNOWN; SECURITY xử lý cảnh báo | Crop chỉ có quyền mới đọc; IS_EMPLOYEE cần chọn NV, không thêm crop vào mẫu. Nếu gallery rỗng thì NO_GALLERY, không dựng người lạ. |
| 4:25–5:05 | SECURITY chấm hộ NV022 + mở cửa mô phỏng có lý do; mở báo cáo chấm hộ | “Chỉ NV MANUAL, khác người chấm, dùng giờ hiện tại; lượt/người khác nhau có thể đối chiếu.” Mở tay không tạo ngày công. |
| 5:05–5:40 | NV phòng khác thử Phòng máy chủ → DENY/RULE; NV Kỹ thuật được qua | Event DENIED_RULE và door DENY; không tính công từ lượt bị từ chối. Không thay tên phòng trên UI để giả điều kiện. |
| 5:40–6:15 | Với người đã được báo trước trong DB demo: OWNER xác nhận nghỉ việc | Hồ sơ/mẫu bị xóa, consent NULL/MANUAL; lịch sử công/event còn. Dùng người demo đã hoàn tất các cảnh trước, không xóa dữ liệu cần diễn tiếp. |
| 6:15–6:50 | Chỉ khi T13 đã chốt: đưa ảnh in lên camera kiosk → DENY/SPOOF | Quay cùng điều kiện đã hiệu chỉnh, mặt thật thử trước/sau; W10 có SPOOF. Không dùng ảnh noise hay message giả làm bằng chứng. |

Mỗi cảnh ghi **PASS / FAIL / CHƯA CHẠY**, đường dẫn video riêng, thời điểm và build commit trong báo cáo T14. Kịch bản trên là hướng dẫn, không phải bằng chứng các cảnh đã chạy xong.

## Khi có lỗi

- Mất Hub: kiosk báo kết nối lại; kiểm Hub/URL/DB, không bù offline bằng event giả.
- Không nhận diện: kiểm gallery được duyệt/consent/nhân viên ACTIVE, ánh sáng/tư thế; không hạ ngưỡng để ép qua trong demo.
- Liveness chưa phê duyệt/cấu hình khác: giữ tắt hoặc trả chưa sẵn sàng; quay lại/hiệu chỉnh đúng camera rồi chốt L. Không tạo marker mẫu để bỏ cổng kiểm.
- CUDA không có: nói rõ demo CPU, giữ kết quả tiền kiểm riêng; không điền bảng GPU.
- Thiếu ngày công đã chốt: dùng ngày thật khác đủ điều kiện hoặc ghi chưa chạy; không đổi giờ hệ thống.

Đo hiệu năng bằng `hub/scripts/benchmark_t14.py`; quay 20 lượt và tổng hợp bằng `measure_kiosk_trials.py`. Lệnh chi tiết/bước còn lại ở [RUN-T14](ket-qua-kiem-thu/2026-11-16_T14/RUN-T14.md).
