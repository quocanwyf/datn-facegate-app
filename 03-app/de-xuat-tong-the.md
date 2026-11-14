# ĐỀ XUẤT TỔNG THỂ — APP ĐIỂM DANH & KIỂM SOÁT RA VÀO (GĐ1 + GĐ2)
> Session làm app soạn ngày 14/11/2026 (v2: đã tự trả lời 4 câu mở ở mục 10 dựa trên log thực nghiệm). Trạng thái: **ĐỀ XUẤT, chờ An duyệt**. Chưa phải đặc tả (đặc tả = `03-app/dac-ta-app.md`, GĐ4).
> ⚠ **TÀI LIỆU LỊCH SỬ (GĐ1–2).** Bản cuối là `03-app/dac-ta-app.md` **v1.4** (§0a bản demo) và `03-app/db/thiet-ke-db.md`. Khi lệch, hai file đó thắng. Mục 6 bên dưới đã được đồng bộ với v1.4 (14/11/2026); các mục khác giữ nguyên để truy vết quá trình ra quyết định.
> Ràng buộc giữ nguyên từ đề cương: app là phần tích hợp/trình diễn; dùng đúng mô hình UniFace + V1 đã train (R18, CASIA-WebFace, chỉ backbone); không train lại, không đổi cách trích feature; không giả lập kết quả nhận dạng; không ghi vào `02-thuc-nghiem/`.

---

## 1. Chốt lĩnh vực: CHẤM CÔNG + RA VÀO cho VĂN PHÒNG DOANH NGHIỆP VỪA VÀ NHỎ

**Khách hàng mục tiêu:** công ty 10–200 nhân viên, 1 văn phòng (1 cơ sở, 1–3 cửa): công ty phần mềm, agency, văn phòng đại diện, phòng khám, showroom có khu văn phòng.

**Vì sao chọn lĩnh vực này (so với các lựa chọn khác):**
| Lĩnh vực | Đánh giá |
|---|---|
| **Văn phòng SME (chọn)** | "Điểm danh" = chấm công, gắn trực tiếp với **tính lương** → khách hàng có lý do trả tiền. Nỗi đau thật: chấm công hộ (thẻ cho mượn), máy vân tay hỏng/không vệ sinh, tổng hợp bảng công thủ công. Điểm danh và ra vào xảy ra **ở cùng một cửa, cùng một người** → hai nghiệp vụ khớp tự nhiên. Người dùng đều là người lớn, có hợp đồng lao động → thu thập đồng ý (consent) dễ. |
| Trường học / trung tâm | Điểm danh theo lớp/tiết, giáo viên, phụ huynh → nghiệp vụ khác hẳn; học sinh vị thành niên → dữ liệu sinh trắc học nhạy cảm hơn. Để mở rộng sau. |
| Phòng gym | Ra vào gắn với gói tập, gia hạn, thanh toán → kéo theo nghiệp vụ bán hàng. Để mở rộng sau. |
| Tòa nhà nhiều công ty thuê | Nhiều tổ chức, khách, thang máy → phức tạp, cần phần cứng cửa thật. Không làm. |

**Hướng mở rộng về sau** (chỉ ghi trong quyển): chuỗi cửa hàng nhiều chi nhánh → trung tâm đào tạo → gym. Lõi nhận dạng giữ nguyên, chỉ thêm module nghiệp vụ.

---

## 2. Hệ sinh thái sản phẩm

```
                      ┌──────────────────────────── HUB (máy chủ tại văn phòng) ────────────────────────────┐
 [Kiosk App] ──frame──▶│ API (FastAPI) ─▶ Pipeline AI: phát hiện → căn chỉnh → CHỐNG GIẢ MẠO → trích feature │
 tablet/điện thoại     │                   → so khớp 1:N → ngưỡng → quy tắc nghiệp vụ → ghi sự kiện           │
 tại cửa      ◀─kết quả│ PostgreSQL (dữ liệu nghiệp vụ + embedding)   ·   WebSocket (sự kiện realtime)         │
                      └───────────────▲──────────────────────────────────▲───────────────────────────────────┘
                                      │                                  │
                              [Web Admin]                        [Employee App]
                     Chủ DN · HR · Quản lý · Lễ tân/Bảo vệ        điện thoại cá nhân nhân viên
```

| Ứng dụng | Ai dùng | Thiết bị | Vai trò |
|---|---|---|---|
| **Kiosk App** | (không ai đăng nhập; thiết bị được ghép bằng mã QR) + HR mở "chế độ đăng ký khuôn mặt" bằng PIN | Tablet/điện thoại Android cố định ở cửa | Quét mặt, hiển thị kết quả (Chào + giờ chấm công / Từ chối / Yêu cầu quay đầu), âm thanh, "mở cửa" mô phỏng |
| **Employee App** | Nhân viên | Điện thoại cá nhân | Xem hôm nay đã chấm công chưa, bảng công, gửi giải trình, nhận thông báo |
| **Web Admin** | Chủ DN, HR, Quản lý, Lễ tân/Bảo vệ (menu theo quyền) | Trình duyệt | Quản lý nhân viên, ca, quy tắc cửa, bảng công, duyệt giải trình, giám sát realtime, cấu hình ngưỡng |
| **Hub** | — | Máy tính tại văn phòng (demo: laptop RTX 3050) | Chạy mô hình AI, API, CSDL. Ảnh khuôn mặt **không rời văn phòng** = điểm bán hàng về quyền riêng tư |

Kiosk App và Employee App: **một codebase React Native, hai bản build** (app khác nhau trên store, chung thư viện).

---

## 3. Vai trò người dùng (RBAC)

| Vai trò | Quyền chính | Ứng dụng |
|---|---|---|
| **Chủ doanh nghiệp (Owner)** | Toàn quyền; cấu hình công ty, cửa, thiết bị, ngưỡng nhận dạng & chống giả mạo; cấp tài khoản cho các vai trò khác; xem nhật ký thao tác (audit log) | Web Admin |
| **HR / Quản trị nhân sự** | Quản lý nhân viên, phòng ban; đăng ký/xoá khuôn mặt; tạo ca và phân ca; chốt bảng công tháng, xuất Excel; xử lý giải trình khi không có quản lý | Web Admin + Kiosk (chế độ đăng ký) |
| **Quản lý trực tiếp (Manager)** | Xem chấm công của team mình; duyệt/từ chối giải trình của team | Web Admin + Employee App |
| **Lễ tân / Bảo vệ (Security)** | Màn hình giám sát realtime; xem và xử lý cảnh báo người lạ / giả mạo; mở cửa thủ công (mô phỏng) **bắt buộc ghi lý do** | Web Admin (giao diện rút gọn) |
| **Nhân viên (Employee)** | Xem chấm công của chính mình; gửi giải trình; xem ca; xem/rút đồng ý dữ liệu khuôn mặt | Employee App |
| **Thiết bị Kiosk** (actor hệ thống) | Gửi khung hình, nhận kết quả; chỉ được gọi API nhận dạng của cửa mình | Kiosk App |
| **Người ngoài** (actor ngoài) | Bị từ chối; sinh sự kiện "người lạ" | — |

Một người có thể giữ nhiều vai trò (Manager cũng là Employee).

---

## 4. Nghiệp vụ

### 4.1 Khái niệm
- **Công ty → Phòng ban → Nhân viên**; mỗi nhân viên có **hồ sơ khuôn mặt** (3–5 ảnh đăng ký + embedding + template).
- **Cửa (Gate)**, mỗi cửa có 1 **chế độ**: `CHẤM CÔNG + RA VÀO` (cửa chính) hoặc `CHỈ RA VÀO` (vd. phòng server, kho).
- **Thiết bị kiosk** gắn với đúng 1 cửa.
- **Ca làm (Shift)**: giờ vào, giờ ra, phút cho phép đi muộn, nghỉ trưa. **Phân ca** cho nhân viên/phòng ban theo ngày trong tuần.
- **Quy tắc ra vào (Access rule)**: phòng ban/nhân viên X được qua cửa Y trong khung giờ Z.
- **Sự kiện (Event)**: mọi lần nhận dạng: `KHỚP` / `NGƯỜI LẠ` / `GIẢ MẠO` / `BỊ TỪ CHỐI DO QUY TẮC` / `MỞ THỦ CÔNG`.
- **Ngày công**: tổng hợp từ sự kiện theo ca.

### 4.2 Quy tắc chấm công (MVP: ca cố định trong ngày)
- Giờ vào = sự kiện khớp **đầu tiên** tại cửa chấm công trong cửa sổ ca; giờ ra = sự kiện khớp **cuối cùng**.
- Trạng thái ngày: `Đúng giờ` · `Đi muộn` · `Về sớm` · `Thiếu chấm công` (chỉ có vào hoặc ra) · `Vắng` · `Nghỉ` (HR đánh dấu).
- **Giải trình**: nhân viên gửi (quên chấm / máy không nhận / công tác) → Manager duyệt → ngày công cập nhật, **giữ nguyên sự kiện gốc** và lưu ai sửa, vì sao.
- **Chốt công tháng**: HR khoá → xuất Excel cho kế toán. Sau khi khoá, mọi sửa đổi phải mở khoá và có ghi lại.

### 4.3 Quy tắc ra vào
- Nhân viên khớp + được phép theo quy tắc → `Cho phép` (cửa mô phỏng: màn hình xanh + âm thanh).
- Nhân viên bị vô hiệu hoá (nghỉ việc) → từ chối ngay, kể cả khi khuôn mặt vẫn khớp.
- Người lạ → từ chối, lưu ảnh crop, đẩy cảnh báo lên màn hình Bảo vệ.
- Giả mạo → từ chối, cảnh báo mức cao.
- Bảo vệ mở cửa thủ công → bắt buộc nhập lý do, ghi sự kiện.

### 4.4 Đăng ký khuôn mặt
- MVP: HR mở chế độ đăng ký **trên chính Kiosk** (bằng PIN), chọn nhân viên, chụp 3–5 ảnh. Dùng cùng camera với lúc nhận dạng nên điều kiện ảnh khớp nhau hơn so với tự chụp bằng điện thoại cá nhân.
- Kiểm tra khi đăng ký: đúng 1 mặt; mặt đủ lớn; góc mặt gần thẳng (ước lượng từ 5 landmark); **qua chống giả mạo**; cảnh báo nếu mặt mới khớp một nhân viên khác (tránh đăng ký trùng/nhầm).
- Nhân viên ký đồng ý xử lý dữ liệu khuôn mặt (consent) trước khi đăng ký. Thu hồi đồng ý = xoá ảnh + embedding.
- Lưu: ảnh đăng ký đã căn chỉnh, từng embedding, **template = trung bình các embedding rồi L2-normalize**. Đây là lựa chọn của ứng dụng; quyển phải ghi rõ.

---

## 5. Pipeline AI trên Hub (mỗi khung hình)

1. **Phát hiện mặt + 5 landmark: YuNet** (OpenCV Zoo, giấy phép MIT, chạy CPU vài ms). Chọn mặt lớn nhất.
2. **Kiểm tra chất lượng:** kích thước mặt, góc quay ước lượng từ landmark.
3. **Căn chỉnh** về 112×112 theo 5 điểm chuẩn kiểu ArcFace/insightface (similarity transform), cùng chuẩn với dữ liệu CASIA bản insightface.
4. **Chống giả mạo (anti-spoofing).** Đây là thành phần ứng dụng, KHÔNG phải đóng góp nghiên cứu, dùng mô hình có sẵn:
   - **Lớp 1, thụ động:** MiniFASNet (dự án Silent-Face-Anti-Spoofing của Minivision). Chạy trên mọi lần quét, phát hiện ảnh in và màn hình điện thoại.
   - **Lớp 2, thử thách chủ động:** khi điểm thụ động nằm trong vùng không chắc, Kiosk yêu cầu "quay mặt sang trái/phải". Hub kiểm tra góc quay đổi đúng chiều qua landmark YuNet. Không cần thêm mô hình.
   - Ngưỡng chống giả mạo do Owner cấu hình. Báo cáo chỉ ghi **kiểm thử chức năng** (ảnh in, màn hình, video phát lại), không công bố độ chính xác như nghiên cứu.
5. **Trích feature: UniFace + V1 (R18)**, đúng quy trình thực nghiệm: (x/255 − 0,5)/0,5, flip-cộng, L2-normalize.
6. **So khớp 1:N:** cosine với ma trận template của nhân viên đang hoạt động (giữ trong RAM/GPU, N ≤ vài nghìn nên tính trực tiếp là đủ nhanh); lấy top-1.
7. **Quyết định:** top-1 ≥ ngưỡng → khớp, ngược lại là người lạ. **Logic ứng dụng** (không thuộc mô hình): cần k khung liên tiếp cùng khớp một người, kèm thời gian chờ (cooldown) để không ghi sự kiện lặp.
8. **Quy tắc nghiệp vụ** (mục 4) → ghi sự kiện → trả kết quả cho Kiosk + đẩy WebSocket lên Web Admin.

**Ngưỡng nhận dạng.** Owner chọn mức, hệ thống quy đổi sang ngưỡng cos lấy từ log BLUFR thật (`02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json`, trường `thr_DIR@…`; giá trị dưới đây là trung bình 10 trial của checkpoint triển khai V1 s3 best.pt):

| Mức | FPIR mục tiêu trên BLUFR | Ngưỡng cos | Dùng cho |
|---|---|---|---|
| Cân bằng | 1e-1 | ≈ 0,401 | Chỉ chấm công (không mở cửa) |
| **Nghiêm ngặt (mặc định)** | 1e-2 | ≈ 0,466 | Cửa chính: chấm công + ra vào |
| Tuỳ chỉnh | — | nhập tay | Chuyên gia/kiểm thử |

**KHÔNG dùng t = b̃/s làm ngưỡng mặc định.** Log cho thấy với V1 s3, t = b̃/s ≈ 0,374 cho FPIR **trung bình 10 trial 22,1% (sd 1,7%)** trên BLUFR (s1: 23,6%, s2: 30,0%; trường `blufr.CH2_tai_nguong_co_dinh["t=b/s"].FPIR.TB`). *(Sửa 14/11 theo review R-01: bản trước ghi nhầm số của trial 01.)* Ở mức này cứ khoảng 5 người lạ thì 1 người được nhận nhầm, không chấp nhận được cho cửa ra vào. Trang "So sánh mô hình" vẫn hiển thị t = b̃/s để trình diễn CH2.

Cần nói rõ ba điểm khi trình bày:
- (i) FPIR tăng theo kích thước gallery (FPIR ≈ N × FAR). Văn phòng 10–200 người nhỏ hơn gallery BLUFR, nên ngưỡng lấy từ BLUFR thường **thận trọng hơn** mức cần, không phải dễ dãi hơn.
- (ii) Đây là ngưỡng **vận hành** chọn sau khi đã báo cáo kết quả test, không dùng cho bất kỳ so sánh nghiên cứu nào.
- (iii) Ở ngưỡng FPIR = 1e-2, DIR rank-1 của V1 s3 trên BLUFR ≈ 83,7%, tức khoảng 16% lượt người đã đăng ký bị từ chối **trong điều kiện LFW chỉ có 1 ảnh mẫu**. Ở văn phòng có 3–5 ảnh đăng ký chụp bằng chính camera Kiosk, cộng thêm việc thử lại theo nhiều khung hình, kết quả có thể khác. App PHẢI đo tại chỗ, không được suy diễn con số.

**Chọn mô hình (model registry):** bảng lưu tên mô hình, đường dẫn checkpoint, SHA-256 checkpoint, nguồn ngưỡng. Web Admin có trang **"So sánh mô hình"** (chỉ Owner): cùng một ảnh, hiển thị điểm top-1 của UniFace và UniFace + V1, đều là mô hình thật. Đây là cầu nối với phần nghiên cứu khi bảo vệ.

---

## 6. Tech stack (đã quyết)

| Thành phần | Chọn | Lý do / ghi chú |
|---|---|---|
| Hub API | **Python 3.11 + FastAPI + Uvicorn** | Cùng ngôn ngữ với code thực nghiệm; async, WebSocket, tự sinh OpenAPI |
| Suy luận AI | **PyTorch (CUDA trên RTX 3050, fallback CPU)** | Dùng thẳng định nghĩa backbone + tiền xử lý của code thực nghiệm (bản sao chỉ-đọc, kèm hash) → không đổi cách trích feature. R18 112×112 nhẹ, 4GB VRAM dư sức. Chưa dùng ONNX (ONNX là tối ưu, nằm ngoài phạm vi) |
| Phát hiện mặt | **OpenCV `FaceDetectorYN` (YuNet)** | MIT, có 5 landmark. KHÔNG dùng model pretrained của insightface (giấy phép chỉ cho nghiên cứu phi thương mại) |
| Chống giả mạo | **MiniFASNet (PyTorch)**, thụ động, có cờ bật/tắt. *(v1.4: thử thách quay đầu chuyển sang lộ trình — review R-06)* | Xem `dac-ta-app.md` §4.5 |
| CSDL | **PostgreSQL 16 cài native trên Windows** + **SQLAlchemy 2 + Alembic** *(v1.4: bỏ Docker để tiết kiệm ổ đĩa — review R-21)* | Embedding lưu dạng mảng float trong Postgres, nạp vào RAM khi khởi động/thay đổi. pgvector để lộ trình (khi N lớn) |
| Tác vụ nền | **APScheduler** (trong tiến trình) | Chốt trạng thái ngày công cuối ngày; dọn ảnh người lạ quá hạn |
| Xác thực | **JWT (access + refresh)**, RBAC theo vai trò + phạm vi; kiosk dùng token thiết bị cấp qua mã ghép QR | |
| Web Admin | **React 18 + Vite + TypeScript + Ant Design + TanStack Query + React Router** | An đã quen React; Ant Design hợp màn hình bảng/biểu mẫu quản trị |
| Mobile (**chỉ Kiosk**) | **React Native (Expo, dev build) + TypeScript + react-native-vision-camera** *(v1.4: trang nhân viên là web responsive `/me` trong codebase `web/`, không còn Employee App native)* | Chung TypeScript với Web. Kiosk gửi ảnh JPEG khoảng 3–5 khung/giây qua WebSocket trong mạng LAN; mọi xử lý AI ở Hub → một pipeline duy nhất, dễ kiểm chứng |
| Thông báo | WebSocket (trong app) cho MVP; push notification để lộ trình | |
| Xuất báo cáo | openpyxl (Excel) / CSV | |
| Triển khai demo | Postgres native + API chạy trực tiếp trên Windows (CUDA); **HTTP trong LAN**, điện thoại và laptop chung Wi-Fi *(v1.4)* | Truy cập từ ngoài văn phòng: lộ trình |
| Repo | Monorepo `03-app/`: `hub/`, `web/` (Web Admin `/admin` + trang nhân viên `/me`), `kiosk/`, `db/`, `openapi/`, `ket-qua-kiem-thu/` *(v1.4, theo `dac-ta-app.md` §2.2)* | |

---

## 7. Phạm vi: MVP (code) và Lộ trình (chỉ thiết kế, ghi trong quyển)

| Module | MVP | Lộ trình |
|---|---|---|
| Nhận dạng | 1 mặt/khung, k khung liên tiếp, ngưỡng theo mức | Nhiều mặt cùng lúc; hiệu chỉnh ngưỡng từ dữ liệu tại chỗ |
| Chống giả mạo | MiniFASNet + thử thách quay đầu | Camera hồng ngoại/độ sâu; mô hình tốt hơn |
| Chấm công | Ca cố định, trạng thái ngày, giải trình, chốt công, xuất Excel | Ca xoay/ca đêm, đơn nghỉ phép, tăng ca, kết nối phần mềm lương |
| Ra vào | Quy tắc phòng ban–cửa–giờ, cửa mô phỏng, mở thủ công | Relay/khoá điện thật, khách mời bằng QR |
| Đăng ký mặt | HR đăng ký tại Kiosk, có consent | Nhân viên tự đăng ký qua app → HR duyệt |
| Employee App | Hôm nay đã chấm chưa, lịch sử/bảng công, giải trình, ca của tôi | Push notification, nộp đơn nghỉ |
| Giám sát | Màn hình realtime cho Bảo vệ, cảnh báo người lạ/giả mạo | Thống kê, dashboard |
| Hệ thống | 1 công ty, 1 cơ sở; `company_id` có sẵn trong mọi bảng | SaaS đa công ty, đa chi nhánh, cloud portal |
| Quyền riêng tư | Consent, xoá dữ liệu, audit log, thời hạn lưu ảnh người lạ | Mã hoá embedding khi lưu |

---

## 8. Rủi ro & lưu ý liêm chính / thương mại hoá

1. **Giấy phép dữ liệu train:** CASIA-WebFace được phát hành cho mục đích nghiên cứu và giáo dục. Vì vậy **mô hình hiện tại chỉ dùng cho demo/DATN**. Thương mại hoá thật cần train lại trên dữ liệu có giấy phép thương mại hoặc dữ liệu tự thu có đồng ý. Kiến trúc model registry cho phép thay mô hình mà không sửa app. Quyển ghi rõ điểm này trong phần hạn chế.
2. **Giấy phép thành phần:** YuNet (MIT); MiniFASNet: các bản phái sinh ghi Apache-2.0 cho dự án gốc **(chưa xác minh trực tiếp file LICENSE của repo gốc và điều khoản của trọng số pretrained — phải kiểm tra trước khi dùng)**; model pretrained của insightface: không dùng.
3. **Căn chỉnh (đã kiểm tra log):** đánh giá BLUFR/LFW của đề tài **đã dùng chính YuNet (`face_detection_yunet_2023mar.onnx`) + căn chỉnh 5 điểm** (`code/tools/align_lfw.py`; log ghi trong `toan_ven_du_lieu.lfw.align_summary`). Vì vậy pipeline app trùng với pipeline đã tạo ra số liệu test. Rủi ro còn lại chỉ là lệch giữa dữ liệu train (CASIA bản insightface) và ảnh căn chỉnh bằng YuNet, và lệch này đã nằm sẵn trong kết quả BLUFR. Hub **dùng lại đúng hàm căn chỉnh của `align_lfw.py`** (bản sao chỉ-đọc, kèm hash). Kiểm thử tích hợp bắt buộc (lưu ở `03-app/`):
   - (a) **Parity test:** cùng ảnh, embedding từ Hub = embedding từ `extract_embeddings(..., flip=True)` (sai số ≤ 1e-5).
   - (b) Chạy toàn pipeline của Hub trên ảnh LFW gốc, so khớp đặc trưng với đặc trưng của lần test BLUFR.
4. **Feature (đã kiểm tra log):** BLUFR dùng flip-cộng (`quy_uoc_feature`: RGB uint8 112×112 → (x/255−0,5)/0,5; flip ngang; cộng; L2-normalize; cosine), **trùng với app**, nên bảng ngưỡng ở mục 5 dùng trực tiếp được.
5. **Pháp lý dữ liệu cá nhân:** dữ liệu sinh trắc học là dữ liệu nhạy cảm theo quy định bảo vệ dữ liệu cá nhân của Việt Nam. Văn bản hiện hành **chưa tra** → khi viết quyển phải trích đúng.
6. **Chống giả mạo** chỉ là lớp bảo vệ cơ bản bằng mô hình có sẵn, không phải đóng góp nghiên cứu; không tuyên bố tỉ lệ chống giả mạo.

---

## 9. Thứ tự xây dựng (không ước lượng thời gian)
M0 Parity test + kiểm thử LFW gốc → M1 Hub: pipeline nhận dạng + API → M2 Kiosk App (quét + hiển thị) → M3 Web Admin: nhân viên, đăng ký mặt, thiết bị → M4 Chấm công: ca, ngày công, giải trình, chốt công, Excel → M5 Ra vào: quy tắc cửa, màn hình Bảo vệ, cảnh báo → M6 Employee App → M7 Chống giả mạo (2 lớp) + audit log + hoàn thiện.

## 10. Trả lời 4 câu mở (session tự đánh giá, An duyệt)
1. **Lĩnh vực:** chấm công + ra vào cho văn phòng SME (lý do: mục 1).
2. **Checkpoint triển khai: UniFace + V1 seed 3, best.pt** (epoch 18, sha256 trong `ket_qua_blufr_lfw.json`).
   - Quy tắc chọn đặt cơ học: **val TAR@FAR=1e-3 cao nhất**. Giá trị val: s1 = 0,78011 (ep19), s2 = 0,77741 (ep21), **s3 = 0,78023 (ep18)** (nguồn: `results/V1-s*/phien-1/session_*.md`).
   - s1 và s3 gần như bằng nhau (chênh 0,00012), nên chọn seed nào cũng được. Không dùng số test để chọn.
   - Mô hình đối chứng cho trang "So sánh mô hình": **UniFace seed 3 best.pt** (cùng seed, đúng cặp ablation).
3. **Flip-cộng trong BLUFR: CÓ**, trùng với app (mục 8.4). BLUFR cũng dùng YuNet để căn chỉnh (mục 8.3). Kết luận: bảng ngưỡng mục 5 lấy trực tiếp từ log, và ngưỡng mặc định là ngưỡng FPIR = 1e-2, không phải b̃/s.
4. **Phân công:** An làm Hub (pipeline AI, API, CSDL) + Web Admin, vì An nắm code thực nghiệm và mạnh web. Bạn cùng nhóm làm Mobile (Kiosk App + Employee App) trên hợp đồng API do An viết trước (OpenAPI). Ghi vào "Bảng phân công nhiệm vụ nhóm" trong quyển.
- Lưu ý còn lại: chống giả mạo là thành phần ứng dụng dùng mô hình có sẵn, không mâu thuẫn đề cương mục 2. An nên báo GVHD và ghi nhật ký.
