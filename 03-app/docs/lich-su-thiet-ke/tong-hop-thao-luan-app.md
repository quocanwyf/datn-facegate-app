# TỔNG HỢP THẢO LUẬN — PHẦN APP (14/11/2026)
> Session thiết kế app. Tài liệu chi tiết: `03-app/docs/lich-su-thiet-ke/de-xuat-tong-the.md` (GĐ1–2, v2), `03-app/docs/lich-su-thiet-ke/thiet-ke-gd3.md` (GĐ3), `03-app/so-do/` (8 hình).
> Trạng thái: An đã đồng ý đề xuất v2; thiết kế GĐ3 **chờ duyệt** + **chờ review chéo** (prompt: `03-app/docs/lich-su-thiet-ke/prompt-review-cheo.md`).

## A. Đã chốt
| # | Quyết định | Lý do / nguồn |
|---|---|---|
| A1 | Lĩnh vực: **chấm công + ra vào cho văn phòng doanh nghiệp vừa và nhỏ (10–200 NV)**. Trường học, gym, chuỗi cửa hàng chỉ là hướng mở rộng | Chấm công gắn với lương nên có người trả tiền; điểm danh và ra vào cùng một cửa; chỉ đi một hướng nghiệp vụ (yêu cầu của An) |
| A2 | Triển khai **on-premise**: Hub (máy chủ tại văn phòng, demo = laptop) + Kiosk ở cửa | Không tốn server; ảnh khuôn mặt không rời công ty |
| A3 | Hệ sinh thái 4 thành phần: **Kiosk App, Employee App, Web Admin, Hub** | — |
| A4 | Vai trò: **Chủ DN, HR, Quản lý, Lễ tân/Bảo vệ, Nhân viên** + thiết bị Kiosk | Ma trận quyền: `thiet-ke-gd3.md` mục 2 |
| A5 | Pipeline: **YuNet (phát hiện + 5 điểm mốc) → căn chỉnh `norm_crop` → MiniFASNet (chống giả mạo) → UniFace+V1 (embedding, flip-cộng, L2) → cosine 1:N + ngưỡng** | V1 chỉ thay ở bước trích embedding; các bước khác là thành phần có sẵn |
| A6 | **Chống giả mạo có trong app** (MiniFASNet thụ động + thử thách quay đầu khi điểm không chắc), là thành phần ứng dụng, KHÔNG phải đóng góp nghiên cứu | An yêu cầu; đề cương mục 2 chỉ loại anti-spoofing khỏi trọng tâm nghiên cứu. Cần báo GVHD |
| A7 | Checkpoint triển khai: **UniFace+V1 seed 3 best.pt (epoch 18)**; đối chứng: **UniFace seed 3 best.pt** | Quy tắc: val TAR@FAR=1e-3 cao nhất (s1 0,78011 · s2 0,77741 · s3 0,78023); s1 và s3 gần như bằng nhau. Nguồn: `02-thuc-nghiem/results/V1-s*/phien-1/session_*.md` |
| A8 | BLUFR đã dùng **flip-cộng** và **YuNet 2023mar** để căn chỉnh LFW, trùng với pipeline app | `results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json`: `quy_uoc_feature`, `toan_ven_du_lieu.lfw.align_summary.detector` |
| A9 | **Ngưỡng mặc định ≈ 0,466** (FPIR 1e-2 trên BLUFR, TB 10 trial V1 s3); mức Cân bằng ≈ 0,401 (FPIR 1e-1). **Không dùng t = b̃/s** làm mặc định | t = b̃/s ≈ 0,374 cho FPIR TB 10 trial 22,1% (s1 23,6%, s2 30,0%; sửa theo review R-01). Nguồn: `thr_DIR@…` và `blufr.CH2_tai_nguong_co_dinh["t=b/s"].FPIR.TB` trong cùng file JSON. **Đã đổi sau review → xem `xu-ly-review.md` Q1** |
| A10 | Stack: **FastAPI + PyTorch CUDA, PostgreSQL + SQLAlchemy/Alembic, APScheduler, JWT/RBAC; Web: React + Vite + TS + Ant Design; Mobile: React Native (Expo) + vision-camera, 1 codebase 2 app** | Hợp phần cứng; An mạnh React |
| A11 | Phân công: **An = Hub + Web Admin; bạn cùng nhóm = Kiosk App + Employee App**; An viết hợp đồng API (OpenAPI) trước | — |
| A12 | Mô hình train trên CASIA-WebFace **chỉ dùng cho demo/DATN**; thương mại cần train lại bằng dữ liệu có giấy phép. Kiến trúc có model registry để thay mô hình | CASIA: phát hành cho nghiên cứu và giáo dục. Không dùng model pretrained của insightface (phi thương mại) |
| A13 | Phạm vi MVP và lộ trình tách theo bảng `de-xuat-tong-the.md` mục 7 | Tránh ôm đồm |

## B. Thiết kế GĐ3 — chờ An duyệt (`thiet-ke-gd3.md` mục 11)
1. Toàn bộ AI ở Hub; Kiosk gửi khung kiểu dừng-và-chờ; một hàng đợi GPU.
2. `recognition_event` append-only; `attendance_day` là dữ liệu dẫn xuất (`recompute_day`).
3. Tham số [khởi đầu]: k = 3, k_unknown = 6, L_low/L_high = 0,5/0,9, cooldown 60 s, quy tắc chấm công (cửa sổ ca, check-out cách check-in ≥ 30 phút).
4. Xử lý cảnh báo "Là nhân viên" không tự thêm ảnh vào hồ sơ (chống đầu độc gallery).
5. Lưu embedding cho cả hai mô hình (phục vụ trang So sánh mô hình W-15).
6. MVP dùng HTTP trong LAN; HTTPS là lộ trình, ghi là hạn chế.

## C. Chưa xác minh / rủi ro mở
- Giấy phép **MiniFASNet**: mới thấy một repo phái sinh ghi Apache-2.0; **chưa đọc LICENSE của repo gốc và điều khoản trọng số**.
- Văn bản pháp lý Việt Nam về bảo vệ dữ liệu cá nhân (dữ liệu sinh trắc học): **chưa tra**.
- Ngưỡng liveness 0,5/0,9 và ngưỡng quay đầu ±0,25: giá trị đặt tay, **phải hiệu chỉnh**.
- Mục tiêu hiệu năng (< 150 ms/khung, < 2 s/lượt): **mục tiêu, chưa đo**.
- Khác biệt nhỏ: `align_lfw.py` chọn **mặt gần tâm ảnh**, app chọn **mặt lớn nhất**. Không đổi cách căn chỉnh, nhưng cần ghi rõ.
- DIR rank-1 ở FPIR 1e-2 của V1 s3 ≈ 83,7% trên BLUFR (1 ảnh mẫu/người): khoảng 16% lượt người đã đăng ký bị từ chối trong điều kiện đó; điều kiện văn phòng phải đo tại chỗ.
- Ngưỡng vận hành lấy từ log **test** BLUFR sau khi đã báo cáo kết quả: không dùng cho so sánh nghiên cứu nào, nhưng cần nói rõ trong quyển.

## D. Việc tiếp theo
1. An duyệt mục B.
2. Chạy review chéo bằng `03-app/docs/lich-su-thiet-ke/prompt-review-cheo.md` → báo cáo ở `03-app/review/`.
3. Sửa theo review → GĐ4: đặc tả `03-app/dac-ta-app.md` (API chi tiết, cấu trúc monorepo, tiêu chí nghiệm thu M0–M7).
4. An báo GVHD việc thêm chống giả mạo như thành phần ứng dụng; cập nhật `00-quan-ly/nhat-ky.md`.
