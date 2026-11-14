# XỬ LÝ REVIEW CHÉO — THIẾT KẾ APP
> Session thiết kế app, 14/11/2026. Trả lời `03-app/review/2026-11-14_review-thiet-ke-app.md` (25 vấn đề).
> Session thiết kế đã **tự chạy lại** các số then chốt reviewer nêu và xác nhận khớp: FPIR tại t = b̃/s TB 10 trial (V1 s3 22,10%; UniFace s3 42,15%), ngưỡng val@FAR=1e-5 = 0,4233 → BLUFR FPIR 5,02% / FNIR 10,56%, `meta.amp = true`, SHA-256 `best.pt` gốc V1 s3 = `120489621a…ef88`, gallery BLUFR = 1000 người/trial.
> Từ giờ, **bản cuối = `03-app/dac-ta-app.md` (GĐ4)**. `de-xuat-tong-the.md` và `thiet-ke-gd3.md` giữ làm lịch sử; chỉ sửa ngay lỗi số liệu (R-01).

## 1. Quyết định cho 11 câu hỏi
| # | Câu hỏi | Quyết định | Lý do |
|---|---|---|---|
| Q1 | Ngưỡng mặc định | **Đổi sang ngưỡng từ validation: τ = 0,4233** (val TAR@FAR=1e-5 của V1 s3 epoch 18). BLUFR là **kiểm chứng độc lập**: FPIR 5,0% ± 0,7, FNIR rank-1 10,6% ± 0,9 (gallery 1000 người). Giữ thêm mức **"Nghiêm ngặt" = 0,4657**, ghi rõ "hiệu chỉnh trên BLUFR-test sau khi đã báo cáo". **Bỏ mức Cân bằng 0,401** (không có nguồn validation tương ứng đủ chặt) | Quy trình sạch: chọn trên validation, kiểm trên test. Ít từ chối nhầm hơn (10,6% so với 16,4%). Mô hình đối chứng UniFace dùng ngưỡng val của chính nó (0,3692) |
| Q2 | HTTPS | **Có, ngay từ MVP**: CA nội bộ bằng mkcert; Uvicorn TLS; app mobile tin CA nội bộ qua network security config (đóng gói CA vào app) | Đ.31 Luật 91/2025; chi phí thấp; nhất quán với điểm bán hàng "ảnh không rời văn phòng" |
| Q3 | Nhân viên nghỉ việc | Tách **`SUSPENDED`** (tạm khoá, giữ dữ liệu) và **`TERMINATED`**. HR xác nhận TERMINATED → **xoá ngay** sample, embedding, template, mọi crop gắn NV; giữ dữ liệu chấm công (không sinh trắc); ghi audit | Đ.25 Luật 91/2025. Xoá ngay đơn giản hơn, không cần job theo hạn |
| Q4 | Người không đồng ý | `employee.attendance_method = FACE / MANUAL`. NV `MANUAL`: Lễ tân/HR **chấm công hộ** trên W-10 (bắt buộc lý do) → event `MANUAL_ATTENDANCE`, audit. PIN cá nhân tại Kiosk: lộ trình | Đồng ý phải tự nguyện; MVP chọn cách ít bị lạm dụng nhất |
| Q5 | CASIA bản Kaggle đã có thỏa thuận CBSR chưa | **Cần An trả lời** (session không biết). Dù câu trả lời là gì: quyển ghi nguồn tải + điều khoản CBSR và insightface; báo GVHD như IJB-C; app hiện nhãn "Bản trình diễn nghiên cứu – không dùng thương mại" | R-12 |
| Q6 | Cắt phạm vi | **Đồng ý cắt:** (1) Employee App → **web responsive cài được (PWA)** trong cùng codebase React, gồm E-02, E-03, E-04, E-05, E-08 và (Quản lý) E-10; (2) quy tắc ra vào → `default_policy` + danh sách phòng ban được phép theo cửa, bỏ khung giờ/ưu tiên; (3) chốt kỳ → chỉ **xuất Excel theo tháng**, bỏ khoá/mở khoá; (4) **thử thách quay đầu → lộ trình**, MVP chỉ MiniFASNet + cờ bật/tắt; (5) notification, biểu đồ W-02, K-10 → lộ trình. **Mobile thật còn lại = Kiosk App** (đúng chữ "Mobile App" trong tên đề tài) | Nhóm 2 người; giữ lõi chứng minh mô hình. Thử thách quay đầu có lỗ hổng R-06; sửa cho đúng tốn công mà không chống được video có chủ đích |
| Q7 | Nạp checkpoint | **`best.pt` gốc trong `results/V1-s3-Hy/...`** → kiểm `source_sha256 = 120489621a…` → trích backbone bằng `evaltest.features.load_backbone(path, expected_sha, strip_map)` (bản sao chỉ-đọc) → kiểm hash bản trích = `meta.sha256` (b00612f5…). `recognition_model` lưu cả hai hash | Dùng lại đúng code đã tạo số liệu BLUFR; không phụ thuộc thư mục ngoài dự án |
| Q8 | fp16 hay fp32 | **fp16 (amp)**, cùng đường code BLUFR (`get_backbone(..., fp16=True)`) | Giống điều kiện tạo số liệu test |
| Q9 | Chọn mặt | **Giữ "mặt lớn nhất"**; Hub gọi `YuNetDetector.detect` + `norm_crop` trực tiếp, **không** dùng `FaceAligner` (tránh fallback landmark LFW); quyển ghi khác biệt với `pick_center_face` | R-14 |
| Q10 | Câu chuyện CH2 | Thống nhất: "b̃/s của V1 chặt hơn UniFace **tương đối** (FPIR 22% so với 42% trên BLUFR), nhưng chưa đủ dùng trực tiếp cho cửa; app dùng ngưỡng validation" | R-25 |
| Q11 | PIN HR | **PIN riêng từng HR** (gắn user_id). Đăng ký trên Kiosk tạo hồ sơ **`PENDING_REVIEW`**, chỉ vào gallery sau khi được xác nhận trên Web Admin (đăng nhập tài khoản + mật khẩu) | Kiosk bị chiếm PIN cũng không đầu độc được gallery |

## 2. Xử lý từng vấn đề
| Mã | Mức | Xử lý | Đưa vào đâu |
|---|---|---|---|
| R-01 | Nghiêm trọng | **Chấp nhận.** Đã sửa số trong `de-xuat-tong-the.md` và `tong-hop-thao-luan-app.md` (TB 10 trial, kèm tên trường) | sửa ngay |
| R-02 | Nghiêm trọng | Chấp nhận → Q3 | dac-ta: trạng thái NV, job xoá |
| R-03 | Cao | Chấp nhận → Q7 | dac-ta: M0, `recognition_model` |
| R-04 | Cao | Chấp nhận toàn bộ: dùng `load_backbone`/`extract_features` của `eval-test/evaltest/features.py`; fp16; BGR→RGB tường minh; unpack `norm_crop`. Parity hai mức: cùng laptop ≤ 1e-5 (hoặc cos ≥ 0,99999); so với feature Kaggle cos ≥ 0,9999 **[khởi đầu]**. Parity căn chỉnh: so landmark với `2026-11-05_eval-lfw/align_log.csv` (≤ 0,5 px), chế độ `pick_center_face`. Thêm unit test kênh màu | dac-ta: M0 |
| R-05 | Cao | Chấp nhận. Thay bộ đếm "liên tiếp" bằng **cửa sổ trượt N = 5 khung** **[khởi đầu]**: MATCH khi ≥ 3 khung cùng id* vượt τ và live; UNKNOWN khi ≥ 4 khung live không khớp ai **và** không có id nào đạt ≥ 2 phiếu; SPOOF khi ≥ 3 khung p_live < L. Reset cửa sổ khi mất mặt > 1 s. Có unit test bằng chuỗi điểm giả lập | dac-ta: thuật toán |
| R-06 | Cao | Phần lớn **không còn áp dụng** vì thử thách chuyển sang lộ trình (Q6). Ghi trong quyển: MiniFASNet không chống được tấn công có chủ đích (video chất lượng cao, mặt nạ) | dac-ta: hạn chế |
| R-07 | Cao | Chấp nhận → Q2 | dac-ta: bảo mật |
| R-08 | Cao | Chấp nhận → Q4 | dac-ta: nghiệp vụ |
| R-09 | Cao | Chấp nhận: `reviewer ≠ requester`; giải trình của Quản lý → HR/Chủ DN; không ai tự sửa ngày công của mình (chặn ở API) | dac-ta: quyền |
| R-10 | Cao | Chấp nhận: gán event theo cửa sổ **của ca** `[start−3h, end+4h]`, kiểm không chồng giữa hai ngày; chốt trạng thái ngày lúc **end + 4h** | dac-ta: chấm công |
| R-11 | Cao | Chấp nhận: W-15 chỉ nhận **event đã có** hoặc **gallery demo riêng** (người tình nguyện, consent riêng); chỉ hiện điểm của nhân viên khớp và ngưỡng, không liệt kê top-5 tên; mọi lần gọi ghi audit | dac-ta: W-15 |
| R-12 | Cao | Chấp nhận → Q5 (chờ An) | quyển + GVHD |
| R-13 | TB | Chấp nhận → Q1. Câu "gallery nhỏ hơn nên ngưỡng thận trọng hơn" ghi là **giả định** (lệch miền: người Việt, camera tablet, template 3–5 ảnh) | dac-ta + quyển |
| R-14 | TB | Chấp nhận → Q9; sửa câu "dùng lại đúng hàm căn chỉnh" thành "cùng detector, cùng phép căn chỉnh; khác quy tắc chọn mặt" | dac-ta |
| R-15 | TB | Chấp nhận: gắn **[chưa đo]**/**[mục tiêu]**; bỏ câu "vài ms", "4GB dư sức"; đo ở M1 | dac-ta |
| R-16 | TB | Chấp nhận: thêm bảng `holiday` (ngày nghỉ toàn công ty); giờ ra = event cuối sau mốc `end − 2h`, nếu event cuối trước mốc đó → `MISSING_OUT` + cờ "nghi quên quét" **[khởi đầu]**; exclusion constraint chống chồng phân ca; ghi rõ ngoài MVP: tăng ca, ca qua đêm, trừ giờ ra ngoài thực tế; E-02 ghi rõ cửa ACCESS_ONLY không tính công | dac-ta |
| R-17 | TB | Chấp nhận toàn bộ UNIQUE/chỉ mục. Quản lý: **chỉ dùng `user_role.scope_department_id`**, bỏ `department.manager_user_id`. Append-only: tách bảng `event_handling`, chặn UPDATE `recognition_event` bằng quyền DB. **Kiosk K-04 chỉ hiện tên + mã NV, không hiện ảnh khuôn mặt** (bỏ `avatar_sample_id`). **Không lưu crop cho event MATCH**; chỉ UNKNOWN/SPOOF, giữ `retention_days`. Thêm `alignment_version`, phiên bản torch/OpenCV vào `recognition_model`. MVP bật BitLocker cho ổ dữ liệu Hub + quyền thư mục | dac-ta: dữ liệu |
| R-18 | TB | Chấp nhận: rate-limit + khoá sau 5 lần cho `/kiosk/pair` và PIN; device token hạn 30 ngày + refresh; xác thực WS bằng message đầu tiên; `/ws/monitor` lọc theo phạm vi | dac-ta: bảo mật |
| R-19 | TB | Chấp nhận: M7 hiệu chỉnh L trên bộ thử nội bộ (thật/in/màn hình), lưu log là **kiểm thử chức năng**; crop cho MiniFASNet theo đúng code gốc của Silent-Face (scale 2,7 và 4,0 → 80×80; **xác minh trong code gốc khi làm M7**); cờ tắt chống giả mạo | dac-ta: M7 |
| R-20 | TB | Chấp nhận → Q6 | dac-ta: phạm vi |
| R-21 | TB | Chấp nhận: suy luận chạy trong **worker thread riêng** (hàng đợi), không chặn event loop; đo p50/p95 ở M1 với 1 và 3 kiosk giả lập. Ổ đĩa ~21 GB: **PostgreSQL cài native** (bỏ Docker/WSL2); Kiosk build bằng **EAS Build** nếu thiếu chỗ cho Android SDK (**hạn mức gói miễn phí chưa xác minh**). Hub dùng **cùng phiên bản torch/OpenCV với môi trường BLUFR** khi có bản cho Windows; ghi phiên bản thật vào `recognition_model` + log parity | dac-ta: môi trường |
| R-22 | TB | Chấp nhận: lưu **nội dung điều khoản** theo `terms_version`; log truy cập đọc ảnh khuôn mặt; xuất "hồ sơ xử lý dữ liệu" (lộ trình nếu không kịp); quyển có mục **Tuân thủ pháp luật**, trích Luật 91/2025/QH15 và NĐ 356/2025/NĐ-CP **sau khi An/nhóm đọc nguyên văn** (review mới đọc bản tóm tắt) | dac-ta + quyển |
| R-23 | Thấp | Chấp nhận: vẽ lại ERD đủ quan hệ, thêm "Ghi event SPOOF" vào F-03, sửa sơ đồ trạng thái theo cửa sổ trượt; use case cho quyển vẽ bằng PlantUML có system boundary | GĐ4 (sơ đồ mới) |
| R-24 | Thấp | Chấp nhận: luôn viết FPIR, chú thích tên trường `DIR_rank1@FAR=` | quyển |
| R-25 | Góp ý | Chấp nhận → Q10 | quyển + nhật ký |

## 3. Việc tiếp theo
1. An trả lời **Q5** (CASIA / CBSR) và xác nhận các quyết định ở mục 1. Đặc biệt **Q1** (đổi ngưỡng) và **Q6** (Employee App thành PWA) thay đổi so với đề xuất trước.
2. Session thiết kế viết **GĐ4 `03-app/dac-ta-app.md`** tích hợp toàn bộ mục 1–2, kèm sơ đồ vẽ lại.
3. An cập nhật nhật ký; báo GVHD (chống giả mạo là thành phần ứng dụng; nguồn CASIA).

---

## 4. Vòng 2 — góp ý bổ sung của reviewer (14/11/2026, sau khi đối chiếu file này)
Reviewer xác nhận lại các số mới (τ = 0,4233; FPIR 5,0% / FNIR 10,6%; UniFace 0,3692; hash, fp16, gallery 1000) và nêu 4 điểm + 2 điểm phụ. **Chấp nhận cả 6.**

| # | Góp ý | Quyết định |
|---|---|---|
| V2-1 | Q1 chỉ ghi lợi ích, thiếu cái giá | **Ghi rõ đánh đổi:** τ = 0,4233 giảm từ chối nhầm (FNIR 16,4% → 10,6%) nhưng **FPIR trên BLUFR tăng 1% → 5%** (khoảng 1/20 người lạ bị nhận nhầm, gallery 1000 người). **Mức mặc định theo loại cửa:** cửa `ATTENDANCE_ACCESS` = 0,4233 (validation); cửa `ACCESS_ONLY` (khu hạn chế) = **Nghiêm ngặt 0,4657**. Câu "văn phòng ít người → FPIR thấp hơn" là **giả định chưa đo**, chỉ đúng nếu phân phối điểm impostor tại chỗ giống LFW |
| V2-2 | mkcert chỉ giải quyết cho Kiosk, không cho Employee PWA | **Phương án chính:** tên miền thật + chứng chỉ **Let's Encrypt cấp qua DNS-01**, bản ghi DNS trỏ `hub.<tên-miền>` về IP LAN của Hub. Kiosk và PWA cùng dùng, không ai phải cài CA. **Rủi ro cần thử ở M1:** router/DNS chặn phản hồi IP nội bộ (DNS rebinding protection), gia hạn chứng chỉ 90 ngày tự động. **Dự phòng (chỉ demo):** mkcert cho Kiosk (đóng gói CA) + cài CA trên 1–2 điện thoại demo; ghi là hạn chế, không dùng cho bản thương mại |
| V2-3a | Bỏ thử thách → chỉ còn một ngưỡng liveness | Đặc tả dùng **một ngưỡng L** (giá trị khởi đầu định ở M7 qua hiệu chỉnh), bỏ L_low/L_high |
| V2-3b | Thứ tự ưu tiên khi xét cửa sổ | **SPOOF > MATCH > UNKNOWN**, xét theo thứ tự này trên cùng cửa sổ. Unit test: (i) mỗi luật riêng; (ii) chứng minh bằng test vét cạn mọi tổ hợp 5 khung (đã/không live × khớp id A / khớp id B / không khớp) rằng không có cửa sổ thoả hai luật cùng lúc, hoặc nếu có thì ra đúng ưu tiên |
| V2-4 | Chấm công hộ có thể bị lạm dụng | Thêm: người chấm hộ ≠ người được chấm; chỉ áp cho NV `attendance_method = MANUAL` (không mở cho NV dùng khuôn mặt); **báo cáo định kỳ số lượt chấm hộ theo từng người chấm** (W-09/W-11, lọc theo `performed_by`); ghi vào quyển là **hạn chế đã biết** |
| V2-5 | torch 2.11+cu130 cần driver hỗ trợ CUDA 13 trên RTX 3050 (chưa xác minh) | **M0 bước đầu tiên:** kiểm `nvidia-smi` + `torch.cuda.is_available()` với bản torch dự kiến. Nếu không được: dùng bản torch CUDA khác hợp driver, ghi phiên bản thật vào `recognition_model` + log parity, và parity với feature Kaggle dùng mức cos ≥ 0,9999 như đã định |
| V2-6 | Sau Q6, mobile chỉ còn Kiosk | Thêm vào việc của An: **hỏi GVHD** có chấp nhận "Mobile App = Kiosk App trên tablet/điện thoại + Employee PWA" không. Nếu GVHD muốn Employee là app native thì khôi phục Employee App (React Native) và cắt việc khác |

### Việc của An (cập nhật)
1. Q5: thỏa thuận CASIA/CBSR + báo GVHD.
2. Hỏi GVHD: cách hiểu "Mobile App" (V2-6) + chống giả mạo là thành phần ứng dụng.
3. Đọc nguyên văn Luật 91/2025/QH15 và NĐ 356/2025/NĐ-CP trước khi trích vào quyển.
4. Chuẩn bị tên miền cho V2-2 (nếu chọn phương án chính).
5. Nhật ký: thêm dòng "τ = 0,4233 đổi lại FPIR BLUFR 5% so với 1%; cửa hạn chế dùng mức Nghiêm ngặt 0,4657".
