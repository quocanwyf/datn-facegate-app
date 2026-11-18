# PROMPT REVIEW CHÉO — THIẾT KẾ APP ĐATN
> Dán toàn bộ khối dưới đây cho một AI khác **có quyền đọc thư mục dự án** (vd. một session Claude Code / Claude desktop mới, mở thư mục `datn-cv-facerecognition`). Không dùng lại session đã viết thiết kế, để người review không chấm bài của chính mình.

---

Bạn là **người review độc lập** cho phần App của đồ án tốt nghiệp (ĐATN) "Mobile App tích hợp tối ưu AI cho hệ thống điểm danh và kiểm soát ra vào bằng nhận dạng khuôn mặt" (Nguyễn Quốc An, PTIT). Bạn KHÔNG phải người viết thiết kế. Nhiệm vụ: kiểm tra lại toàn bộ đề xuất và thiết kế app, phát hiện sai sót, mâu thuẫn, số liệu không có nguồn, rủi ro, rồi viết báo cáo. Trao đổi bằng tiếng Việt, giữ thuật ngữ kỹ thuật tiếng Anh.

## Đọc trước (theo thứ tự)
1. `CLAUDE.md` (quy ước thư mục; tuân thủ tuyệt đối).
2. `00-quan-ly/de-cuong.md` (phạm vi, ràng buộc, quyết định đã chốt của phần nghiên cứu).
3. `03-app/docs/lich-su-thiet-ke/tong-hop-thao-luan-app.md` (tóm tắt quyết định).
4. `03-app/docs/lich-su-thiet-ke/de-xuat-tong-the.md` (GĐ1–2) và `03-app/docs/lich-su-thiet-ke/thiet-ke-gd3.md` (GĐ3); hình ở `03-app/so-do/`.
5. Nguồn số liệu để đối chiếu:
   - `02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json`
   - `02-thuc-nghiem/results/V1-s1-Ngan/`, `V1-s2-Hy/`, `V1-s3-Hy/` (file `session_*.md` trong `phien-1/`)
   - `02-thuc-nghiem/code/fr/` (đặc biệt `fr/align/`, `fr/eval/verification.py`), `02-thuc-nghiem/code/tools/align_lfw.py`

## Ràng buộc khi review
- **Chỉ đọc** mọi file hiện có. KHÔNG sửa `de-xuat-tong-the.md`, `thiet-ke-gd3.md`, `de-cuong.md`, `nhat-ky.md`, KHÔNG ghi gì vào `02-thuc-nghiem/`.
- Chỉ tạo file báo cáo: `03-app/review/<YYYY-MM-DD>_review-thiet-ke-app.md`.
- Không bịa nguồn. Mọi kết luận "đúng/sai" về số liệu phải chỉ ra **file + trường JSON / dòng** đã đối chiếu, kèm lệnh/đoạn code đã chạy để đọc số. Thông tin giấy phép/pháp lý tra trên web phải có link; chưa xác minh được thì ghi "(chưa xác minh)".
- Không đề xuất đổi các quyết định nghiên cứu đã chốt trong `de-cuong.md` (mô hình, dữ liệu, cách trích feature). Được phép chỉ ra nếu thiết kế app **vi phạm** chúng.
- Ràng buộc liêm chính của đề tài: app phải dùng đúng mô hình đã train, không giả lập kết quả nhận dạng, không đổi cách trích feature (112×112, (x/255−0,5)/0,5, flip-cộng, L2-normalize, cosine).

## Việc cần kiểm tra
**1. Đối chiếu số liệu (bắt buộc, tự chạy script đọc file — không chép số từ tài liệu thiết kế):**
- a) Val TAR@FAR=1e-3 và epoch của best.pt cho V1 s1/s2/s3 → quy tắc "val cao nhất" có ra **seed 3** không?
- b) `ket_qua_blufr_lfw.json`: `quy_uoc_feature` có đúng là flip-cộng? Detector căn chỉnh LFW có phải `face_detection_yunet_2023mar.onnx`?
- c) Với `r18_uniface_v1_lam0.6_m0.45_s3_e28:best`: trung bình 10 trial của `thr_DIR@0.01` (thiết kế ghi ≈ 0,466) và `thr_DIR@0.1` (≈ 0,401); `t_eq30` (≈ 0,374) và FPIR tại t = b̃/s (thiết kế ghi ≈ 21%; s1 ≈ 22%, s2 ≈ 29%); DIR rank-1 @FAR 1% (thiết kế ghi ≈ 83,7%).
- d) SHA-256 checkpoint trong `meta` của s3 best để dùng cho kiểm thử M0.
- e) Tên/chữ ký hàm thật trong `fr/align` (YuNetDetector, norm_crop, pick_center_face) và `extract_embeddings` — thiết kế có gọi đúng tên, đúng tham số (vd. `score_threshold=0.6`) không?

**2. Nhất quán với đề cương và liêm chính:**
- Có chỗ nào app làm khác cách trích feature / căn chỉnh so với pipeline đã tạo số liệu test? (Lưu ý đã biết: `align_lfw.py` chọn mặt gần tâm, app chọn mặt lớn nhất — đánh giá mức ảnh hưởng.)
- Việc lấy ngưỡng vận hành từ log **test** BLUFR có gây rò rỉ test vào kết luận nghiên cứu không? Cách trình bày trong quyển nên thế nào?
- Thêm chống giả mạo vào app có mâu thuẫn đề cương mục 2 không?
- Có câu nào trong tài liệu khẳng định hiệu năng/độ chính xác **chưa đo** mà không đánh dấu không?

**3. Pháp lý & giấy phép (tra nguồn chính thức):**
- Giấy phép của repo gốc Silent-Face-Anti-Spoofing (minivision-ai) và **trọng số pretrained** MiniFASNet.
- Giấy phép YuNet (OpenCV Zoo), giấy phép dữ liệu CASIA-WebFace, chính sách model pretrained của insightface.
- Văn bản pháp luật Việt Nam hiện hành về bảo vệ dữ liệu cá nhân áp dụng cho dữ liệu sinh trắc học (tên văn bản, hiệu lực, yêu cầu chính về đồng ý và lưu trữ) → thiết kế consent/xoá/thời hạn lưu đã đủ chưa.

**4. Tính đúng đắn của thiết kế:**
- Thuật toán quyết định (`thiet-ke-gd3.md` mục 4): lỗ hổng logic? (vd. đổi người giữa các khung, nhiều người trước camera, thử thách quay đầu bị qua mặt bằng video quay sẵn, ảnh hưởng khi quay đầu làm giảm điểm cosine.)
- Quy tắc chấm công (mục 5.2): ca trường hợp biên (đi qua cửa nhiều lần, quên quét ra, đến trước ca rất sớm, ngày lễ, nhân viên không có ca).
- Mô hình dữ liệu (mục 6): thiếu khoá/ràng buộc duy nhất, chỉ mục, vấn đề khi đổi mô hình, consent bị rút nhưng event cũ còn employee_id.
- Bảo mật: device token, PIN HR trên kiosk, WebSocket, HTTP trong LAN, phân quyền phạm vi phòng ban.
- Khả thi trên phần cứng (RTX 3050 4GB, Windows, Ryzen 5 5600H, 16GB RAM): một hàng đợi GPU cho YuNet + MiniFASNet + R18 với 3 kiosk.
- Phạm vi MVP có quá lớn cho nhóm 2 người không? Đề xuất cắt gì nếu phải cắt (không đề xuất thời gian cụ thể).
- 8 sơ đồ trong `03-app/so-do/` có khớp nội dung chữ không.

## Định dạng báo cáo (`03-app/review/<ngày>_review-thiet-ke-app.md`)
1. **Tóm tắt** (≤ 10 dòng): đánh giá chung, số vấn đề theo mức.
2. **Bảng đối chiếu số liệu**: mục | giá trị trong thiết kế | giá trị đọc từ nguồn | nguồn (file + trường) | khớp/không.
3. **Danh sách vấn đề**, mỗi vấn đề gồm: Mã (R-01…) · Mức (**Nghiêm trọng** = sai số liệu/vi phạm liêm chính/vi phạm giấy phép; **Cao** = lỗi logic hoặc bảo mật làm sai kết quả; **Trung bình**; **Thấp/Góp ý**) · Vị trí (file + mục) · Mô tả · Bằng chứng · Đề xuất sửa.
4. **Pháp lý & giấy phép**: bảng thành phần | giấy phép | link nguồn | dùng thương mại được? | ghi chú; mục "chưa xác minh được".
5. **Những điểm thiết kế làm tốt** (ngắn).
6. **Câu hỏi cho An** (các điểm cần An quyết, không tự quyết).
7. **Phụ lục**: lệnh/script đã chạy để đọc số liệu.

Không viết lại thiết kế. Chỉ review và đề xuất.
