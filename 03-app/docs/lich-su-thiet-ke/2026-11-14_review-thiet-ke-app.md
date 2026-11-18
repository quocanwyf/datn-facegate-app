# REVIEW CHÉO — THIẾT KẾ APP ĐATN (GĐ1–3)
> Người review: session Claude độc lập (không viết thiết kế), 14/11/2026, theo `03-app/docs/lich-su-thiet-ke/prompt-review-cheo.md`.
> Phạm vi đã đọc: `CLAUDE.md`, `00-quan-ly/de-cuong.md`, `03-app/docs/lich-su-thiet-ke/tong-hop-thao-luan-app.md`, `03-app/docs/lich-su-thiet-ke/de-xuat-tong-the.md`, `03-app/docs/lich-su-thiet-ke/thiet-ke-gd3.md`, 8 hình `03-app/so-do/`, log trong `02-thuc-nghiem/results/`, code `02-thuc-nghiem/code/fr/`, `02-thuc-nghiem/eval-test/`.
> Chỉ đọc. Không sửa file thiết kế, không ghi vào `02-thuc-nghiem/`. Script đọc số chạy từ thư mục tạm ngoài dự án (nội dung ở Phụ lục).
> Phần pháp lý là tóm tắt để tham khảo, người review không phải luật sư.

---

## 1. Tóm tắt

Thiết kế tốt về kiến trúc và kỷ luật liêm chính: tách sự kiện gốc với ngày công dẫn xuất, model registry có SHA-256, bảng ngưỡng có trường nguồn, M0 parity test đặt trước mọi tính năng. Phần lớn số liệu khớp log (val 3 seed, chọn seed 3, flip-cộng, YuNet 2023mar, ngưỡng 0,466/0,401, t = 0,374, DIR 83,7%).

Các lỗi chính:
- (a) FPIR tại t = b̃/s ghi 21% / 22% / 29% là số của **trial 01**, không phải trung bình 10 trial (22,1% / 23,6% / 30,0%).
- (b) Kiểm thử M0 so SHA-256 của `best.pt` với `meta.sha256`, nhưng `meta.sha256` là hash của **bản trích chỉ-backbone**, nên phép thử sẽ luôn hỏng.
- (c) Parity test thiếu điều kiện fp16 (amp) và bước BGR→RGB.
- (d) Giả mã quyết định không reset `unknown_streak` / `spoof_streak`.
- (e) Dữ liệu khuôn mặt của nhân viên nghỉ việc vẫn được giữ, trái Điều 25 Luật Bảo vệ dữ liệu cá nhân 2025.
- (f) Không có cách chấm công thay thế cho người không đồng ý.

**Số vấn đề:** Nghiêm trọng 2 · Cao 10 · Trung bình 10 · Thấp/Góp ý 3 (tổng 25).

---

## 2. Bảng đối chiếu số liệu

Mọi giá trị "đọc từ nguồn" do script ở Phụ lục tính lại từ file gốc, không chép từ tài liệu thiết kế. Viết tắt: `KQ` = `02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json`; `V1s3` = khoá `ket_qua["r18_uniface_v1_lam0.6_m0.45_s3_e28:best"]`.

| # | Mục | Giá trị trong thiết kế | Giá trị đọc từ nguồn | Nguồn (file + trường) | Khớp? |
|---|---|---|---|---|---|
| 1a | Val TAR@FAR=1e-3 best, V1 s1 | 0,78011 (ep19) | 0,78011, ep19 | `results/V1-s1-Ngan/phien-1/r18_*/val.jsonl` (argmax `results["tar@far=0.001"]` trên 28 dòng epoch) = `summary.json.best_val` | ✔ |
| 1a | V1 s2 | 0,77741 (ep21) | 0,77741, ep21 | `results/V1-s2-Hy/.../val.jsonl`, `summary.json` | ✔ |
| 1a | V1 s3 | 0,78023 (ep18) | 0,78023, ep18 | `results/V1-s3-Hy/.../val.jsonl`, `summary.json` | ✔ |
| 1a | Quy tắc "val cao nhất" → seed 3 | seed 3 | seed 3 (hơn s1 0,00012) | như trên | ✔ |
| 1a | UniFace s3 (đối chứng) | (không ghi epoch) | 0,77551, ep20 | `results/UniFace-s3-Ngan/.../summary.json` | — (nên ghi epoch 20) |
| 1b | Quy ước feature | flip-cộng, (x/255−0,5)/0,5, L2, cosine | `flip="sum"`; "RGB uint8 112x112 -> (x/255-0.5)/0.5; flip ngang (dims=[3]); cộng; L2-normalize; cosine" | `KQ.quy_uoc_feature` | ✔ |
| 1b | Detector căn chỉnh LFW | `face_detection_yunet_2023mar.onnx` | `face_detection_yunet_2023mar.onnx`; OpenCV 4.14.0; `multi_face_images` = 2334/13233 | `KQ.toan_ven_du_lieu.lfw.align_summary` | ✔ (xem R-14 về 2334 ảnh nhiều mặt) |
| 1b | (bổ sung) Chế độ số học khi trích feature BLUFR | không ghi | **amp = true** (fp16, CUDA, Tesla T4) | `V1s3.meta.amp`; `eval-test/evaltest/features.py` dòng 80–81, 107; `eval_test/env.json` | thiếu (R-04) |
| 1c | `thr_DIR@0.01` TB 10 trial, V1 s3 | ≈ 0,466 | **0,4657** (sd 0,0079; min 0,4530 – max 0,4785) | `V1s3.blufr.per_trial[*]["thr_DIR@0.01"]` | ✔ |
| 1c | `thr_DIR@0.1` TB 10 trial | ≈ 0,401 | **0,4014** (sd 0,0035) | `V1s3.blufr.per_trial[*]["thr_DIR@0.1"]` | ✔ |
| 1c | `t_eq30` (= b̃/s), V1 s3 | ≈ 0,374 | **0,37365** | `V1s3.meta.t_eq30`; `V1s3.ch2_nguon_nguong.lech_t = 0.0` | ✔ |
| 1c | FPIR tại t = b̃/s, V1 s3 | ≈ 21% | **TB 10 trial = 22,10%** (sd 1,71%); trial 01 = 21,11% | `V1s3.blufr.CH2_tai_nguong_co_dinh["t=b/s"].FPIR.TB`; trial: `per_trial["split_t01.csv"].tai_nguong_co_dinh` | **✘** (lấy trial 01) |
| 1c | FPIR tại t = b̃/s, V1 s1 | ≈ 22% | **TB = 23,63%**; trial 01 = 22,45% | khoá `..._s1_e28:best`, cùng trường | **✘** |
| 1c | FPIR tại t = b̃/s, V1 s2 | ≈ 29% | **TB = 30,00%**; trial 01 = 28,88% | khoá `..._s2_e28:best`, cùng trường | **✘** |
| 1c | DIR rank-1 tại FPIR 1e-2, V1 s3 | ≈ 83,7% | **83,65%** (sd 1,74%) | `V1s3.blufr.summary["DIR_rank1@FAR=0.01"].mu` (tên trường ghi "FAR" nhưng là FPIR) | ✔ |
| 1c | "khoảng 16% bị từ chối" | ≈ 16% | 1 − 0,8365 = 16,35% | như trên | ✔ |
| 1c | (bổ sung) Ngưỡng từ **validation** của chính checkpoint | không dùng | `val_thr@far=1e-05` = 0,4233 → FPIR BLUFR TB 5,02%, FNIR 10,56%; `val_thr@far=1e-04` = 0,3678 → FPIR 25,45% | `V1s3.blufr.CH2_tai_nguong_co_dinh["val_thr@far=…"]`; giá trị ngưỡng = `thr@far=1e-05` ở epoch 18 trong `V1-s3-Hy/.../val.jsonl` (0,4233) | — (xem R-13) |
| 1c | (bổ sung) Protocol A, V1 s3 | không dùng | `thr@fpir=0.01` TB 0,4683; `thr@fpir=0.1` TB 0,4014; FPIR tại t = b̃/s TB 21,44% | `V1s3.protocol_a.per_split[*]` | — (nhất quán với BLUFR) |
| 1d | SHA-256 để kiểm thử M0 (V1 s3 best) | "khớp `meta.sha256` trong KQ" | `meta.sha256` = `b00612f58a5a3d6be9055ce6ff073fdafd3d8071c85ebdaa5462b198f2b1a065` với `is_stripped = true` (bản trích chỉ-backbone, 96.212.289 byte, nằm ở `C:\datn-backbones-24`, ngoài dự án). SHA-256 thật của `results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt` = **`120489621accefd7e78da9bd83fe3c6360ad94877e8ac4b9cdfa1038ec8eef88`** (137.372.031 byte) | `KQ…meta`; `sha256sum best.pt`; `eval-test/tools/windows/logs/strip_map_ban_sao.json` (source_sha256 120489… → dest_sha256 b00612…) | **✘ về đặc tả** (R-03) |
| 1d | SHA-256 UniFace s3 best (đối chứng) | — | gốc `3846bb9a…49e9` → trích `cfe78d46…5d2c` | như trên | — |
| 1e | `YuNetDetector(score_threshold=0.6)` | "YuNet(f, score ≥ 0.6)" | `YuNetDetector.__init__(model_path, score_threshold=0.6, nms_threshold=0.3, top_k=50)`; `detect(img_bgr, score_threshold=None)` nhận ảnh **BGR** | `code/fr/align/detector.py` dòng 34–52 | ✔ |
| 1e | `norm_crop` | `x = norm_crop(f, landmarks)` (dùng như ảnh) | `norm_crop(img, landmark, image_size=112)` trả **tuple `(warped, M)`**, ảnh BGR | `code/fr/align/template.py` dòng 41–44 | ✘ nhẹ (phải unpack, chuyển RGB) |
| 1e | `pick_center_face` | app chọn mặt lớn nhất | `pick_center_face(faces, img_shape)`: gần tâm ảnh, bằng nhau mới lấy hộp lớn hơn; `FaceAligner` gọi hàm này và có `retry_threshold=0.3` + `fallback_landmarks` | `detector.py` dòng 63–75; `pipeline.py` | đã biết (R-14) |
| 1e | `extract_embeddings(..., flip=True)` | đúng tên | `extract_embeddings(backbone, images_u8, device, batch_size=256, flip=True, amp=False)`; input tensor **(N,3,112,112) uint8 RGB**; BLUFR gọi với `amp = (device.type=="cuda")` và backbone `get_backbone(..., fp16=amp)` | `code/fr/eval/verification.py` dòng 21–34; `eval-test/evaltest/features.py` dòng 61–107 | tên ✔; tham số amp/layout **thiếu** (R-04) |
| 1e | "chỉ backbone" | ✔ | `head_keys_ignored = [bias, proto, proto_seen, weight, weight_mom]`, `missing_keys = []` | `V1s3.meta` | ✔ |

---

## 3. Danh sách vấn đề

Mức: **Nghiêm trọng** = sai số liệu / vi phạm liêm chính / vi phạm giấy phép hoặc luật; **Cao** = lỗi logic hoặc bảo mật làm sai kết quả; **Trung bình**; **Thấp/Góp ý**.

### Nghiêm trọng

**R-01 · Nghiêm trọng · FPIR tại t = b̃/s lấy từ trial 01 nhưng trình bày như số tổng hợp**
- *Vị trí:* `de-xuat-tong-the.md` mục 5 (đoạn "KHÔNG dùng t = b̃/s…"); `tong-hop-thao-luan-app.md` A9.
- *Mô tả:* Ghi "FPIR ≈ 21% (s1 22%, s2 29%); trường `tai_nguong_co_dinh`". Trường `tai_nguong_co_dinh` nằm trong **từng trial**. Ba con số trùng với trial `split_t01.csv`. Trong cùng đoạn, ngưỡng 0,466/0,401 lại là TB 10 trial, nên người đọc hiểu FPIR cũng là TB.
- *Bằng chứng:* TB 10 trial (`CH2_tai_nguong_co_dinh["t=b/s"].FPIR.TB`) = 22,10% / 23,63% / 30,00% (s3/s1/s2); trial 01 = 21,11% / 22,45% / 28,88%. Script Phụ lục A.
- *Tác động:* không đổi quyết định "không dùng b̃/s làm mặc định". Nhưng đây là số đi vào quyển, và quy ước dự án là "không ghi số liệu sai nguồn".
- *Đề xuất:* sửa thành "TB 10 trial: s3 22,1% (sd 1,7%), s1 23,6%, s2 30,0%; trường `blufr.CH2_tai_nguong_co_dinh["t=b/s"].FPIR.TB`". Câu "cứ khoảng 5 người lạ thì 1 người được nhận nhầm" vẫn đúng (≈ 1/4,5).

**R-02 · Nghiêm trọng (pháp lý) · Giữ dữ liệu sinh trắc của nhân viên đã nghỉ việc**
- *Vị trí:* `de-xuat-tong-the.md` 4.3 ("Nhân viên bị vô hiệu hoá (nghỉ việc) → từ chối ngay, kể cả khi khuôn mặt vẫn khớp"); `thiet-ke-gd3.md` 5.1 (`DENIED_INACTIVE`), mục 6 (không có job xoá khi `INACTIVE`).
- *Mô tả:* Thiết kế ngầm giữ `face_sample` (ảnh PNG đã căn chỉnh), `face_embedding`, `face_template` sau khi nhân viên nghỉ việc. Điều 25 Luật Bảo vệ dữ liệu cá nhân 2025 yêu cầu bên sử dụng lao động xoá, huỷ dữ liệu cá nhân của người lao động khi chấm dứt hợp đồng, trừ khi có thoả thuận khác hoặc luật khác quy định. Tài liệu hướng dẫn (lsvn.vn, dẫn khoản 4 Điều 5 NĐ 356/2025) nêu thời hạn xoá theo yêu cầu là 20 ngày (nguồn thứ cấp, **chưa đối chiếu nguyên văn nghị định**).
- *Đề xuất:* thêm trạng thái `TERMINATED` (khác `INACTIVE` tạm khoá) kèm job xoá sinh trắc (sample, embedding, template, crop gắn nhân viên) trong N ngày **[khởi đầu]**, ghi audit. `DENIED_INACTIVE` chỉ áp dụng khi tạm khoá. Event chấm công (không phải sinh trắc) vẫn giữ theo luật lao động. Ghi rõ phần này trong quyển.

### Cao

**R-03 · Cao · Kiểm thử M0 "checksum mô hình" so sai hash**
- *Vị trí:* `thiet-ke-gd3.md` 9.3; `de-xuat-tong-the.md` 10.2 ("sha256 trong `ket_qua_blufr_lfw.json`").
- *Mô tả:* `meta.sha256` (b00612f5…) là hash của file đã trích chỉ-backbone ở `C:\datn-backbones-24` (ngoài dự án). Nếu Hub nạp `best.pt` gốc trong `results/V1-s3-Hy/...` thì hash là 120489621a…, không bao giờ khớp. Người làm sau có thể "sửa" phép thử cho qua, và khi đó phép thử mất tác dụng.
- *Bằng chứng:* bảng mục 2 dòng 1d; `strip_map_ban_sao.json` nối source → dest.
- *Đề xuất:* chọn một trong hai cách và ghi rõ trong đặc tả. (i) Hub nạp đúng file trích chỉ-backbone (sao từ `C:\datn-backbones-24`) và so với `meta.sha256`. (ii) Hub nạp `best.pt` gốc, so với `source_sha256` trong `strip_map_ban_sao.json`, rồi kiểm `strip_map` nối tới `meta.sha256`. Cách (ii) dùng lại được `evaltest.features.load_backbone(path, expected_sha, strip_map)`, vốn đã làm đúng việc này. Lưu `recognition_model.checkpoint_sha256` kèm loại (gốc hay trích).

**R-04 · Cao · Parity test thiếu điều kiện số học và bố cục ảnh; dung sai 1e-5 không phù hợp với mọi phép so**
- *Vị trí:* `thiet-ke-gd3.md` 1.2, 4 (giả mã), 9.1–9.2; `de-xuat-tong-the.md` 8.3(a)(b).
- *Mô tả:*
  1. Feature BLUFR được trích bằng **fp16 autocast** (`amp = device.type=="cuda"`; `get_backbone(..., fp16=amp)`) trên Tesla T4, Python 3.13, torch 2.11+cu130. Thiết kế không nói Hub chạy fp16 hay fp32. fp32 hoặc GPU khác (RTX 3050) sẽ lệch khoảng 1e-3, nên "max |Δ| ≤ 1e-5" chỉ đạt khi so **cùng máy, cùng chế độ**.
  2. `FaceAligner`/`norm_crop` trả ảnh **BGR HWC**, còn `extract_embeddings` nhận **RGB NCHW uint8** (`align_lfw.py` dòng 65: `cv2.cvtColor(warped, BGR2RGB).transpose(2,0,1)`). Giả mã bỏ qua bước này. Quên chuyển màu là lỗi im lặng: không báo lỗi gì, chỉ làm sai mọi điểm số.
  3. `norm_crop` trả tuple `(warped, M)`.
  4. `aligned_u8.npy` của lần test **không có** trong dự án (zip kết quả không chứa nó). Thư mục chỉ có `aligned_sha256` = 38d3fc75… và `2026-11-05_eval-lfw/align_log.csv` (5 landmark từng ảnh).
- *Đề xuất:*
  - Hub dùng đúng chuỗi `load_backbone` → `extract_features` của `eval-test/evaltest/features.py` (bản sao chỉ-đọc), kể cả `fp16=amp`.
  - Parity 9.1: so Hub với hàm thực nghiệm **trên cùng laptop, cùng chế độ** (≤ 1e-5). So với feature Kaggle thì dùng ngưỡng cos ≥ 0,9999 **[khởi đầu]**, ghi rõ hai mức.
  - Parity 9.2: so landmark Hub với `align_log.csv` (≤ 0,5 px), hoặc chạy lại `align_lfw.py` trên laptop rồi so `aligned_sha256` (phải cài **OpenCV 4.14.0** như log).
  - Thêm unit test "kênh màu": đưa ảnh BGR thẳng vào phải cho cos khác hẳn so với RGB.

**R-05 · Cao · Giả mã quyết định: bộ đếm "liên tiếp" không reset**
- *Vị trí:* `thiet-ke-gd3.md` mục 4, giả mã.
- *Mô tả:*
  - `unknown_streak` chỉ tăng, không reset khi `s* ≥ τ`. Một nhân viên có điểm dao động quanh τ (rất có thể khi ở FPIR 1e-2 còn khoảng 16% lượt bị từ chối) sẽ dồn đủ 6 khung "không khớp" **không liên tiếp** và bị báo `UNKNOWN`, sinh cảnh báo người lạ giả lên màn hình Bảo vệ.
  - `spoof_streak` cũng không reset khi `p_live ≥ L_low`, nên "k khung **liên tiếp** dưới L_low" (sơ đồ 07) không đúng với code.
  - `streak` không reset khi khung rơi vào vùng liveness không chắc.
- *Đề xuất:* reset chéo rõ ràng: khớp → `unknown_streak = 0`; live → `spoof_streak = 0`. Hoặc dùng cửa sổ trượt N khung với đa số phiếu. Viết unit test bằng chuỗi điểm giả lập (đây là logic ứng dụng, không đụng mô hình).

**R-06 · Cao · Thử thách quay đầu và bộ đếm gắn với "vị trí bbox", không gắn với danh tính**
- *Vị trí:* `thiet-ke-gd3.md` mục 4 (IoU < 0,3 → reset; cờ "đã qua thử thách").
- *Mô tả:*
  - IoU chỉ so với khung liền trước. Người A rời đi, người B bước vào gần cùng vị trí trong dưới 1 s thì IoU ≥ 0,3, và B **thừa hưởng "đã qua thử thách"** của A.
  - Thử thách chỉ có 1 bit ngẫu nhiên (trái/phải). Video quay sẵn cả hai hướng (hoặc tua) vượt được với xác suất cao.
  - Thử thách chỉ bật trong vùng `L_low ≤ p_live < L_high`. Một video phát lại chất lượng cao được MiniFASNet chấm ≥ 0,9 thì không bao giờ bị thử thách.
- *Đề xuất:*
  - Lưu `challenge_passed_for = id*` và hết hạn khi `id*` đổi hoặc mất mặt.
  - Yêu cầu `id*` không đổi trong suốt thử thách (khung quay đầu vẫn top-1 cùng người, có thể với ngưỡng nới **[khởi đầu]**, vì quay đầu làm giảm cos).
  - Cân nhắc chuỗi 2 hướng ngẫu nhiên.
  - Trong quyển ghi rõ: thử thách **không chống được video phát lại có chủ đích**, chỉ kiểm thử chức năng.

**R-07 · Cao · Truyền ảnh khuôn mặt và token bằng HTTP/WS không mã hoá qua Wi-Fi**
- *Vị trí:* `thiet-ke-gd3.md` 10, 11.6; `tong-hop` B6.
- *Mô tả:* Kiosk gửi JPEG khuôn mặt (dữ liệu sinh trắc, thuộc nhóm nhạy cảm theo NĐ 356/2025) và device token / JWT ở dạng rõ qua Wi-Fi. Ai cùng mạng cũng nghe lén và chiếm token được. Điều 31 Luật 91/2025 yêu cầu bảo mật vật lý cho thiết bị lưu trữ **và truyền tải** dữ liệu sinh trắc. Điều này mâu thuẫn với điểm bán hàng "ảnh không rời văn phòng".
- *Đề xuất:* dùng TLS ngay từ MVP với chi phí thấp: CA nội bộ bằng `mkcert`, Uvicorn `--ssl-*`, Kiosk/Employee App ghim chứng chỉ (cert pinning) hoặc cài CA. Nếu vẫn giữ HTTP cho demo, quyển phải ghi là **không tuân thủ** Điều 31, không chỉ là "hạn chế".

**R-08 · Cao · Không có cách chấm công thay thế cho người không đồng ý hoặc rút đồng ý**
- *Vị trí:* `thiet-ke-gd3.md` F-02, E-08 ("sẽ không chấm công bằng khuôn mặt được nữa"); `de-xuat-tong-the.md` 4.4.
- *Mô tả:* Trong quan hệ lao động, nếu khuôn mặt là **cách duy nhất** để được tính công thì sự đồng ý khó coi là tự nguyện. Về nghiệp vụ, người rút đồng ý sẽ thành `ABSENT` mỗi ngày.
- *Đề xuất:* thêm phương thức chấm công không sinh trắc tối thiểu, ví dụ Lễ tân/HR "chấm hộ có lý do" (event `MANUAL_ATTENDANCE`, audit) hoặc mã PIN cá nhân tại Kiosk. Trạng thái nhân viên ghi `attendance_method = FACE | MANUAL`. Màn K-07 cần nút "Không đồng ý" dẫn tới phương án này.

**R-09 · Cao · Quản lý tự duyệt giải trình của chính mình**
- *Vị trí:* `thiet-ke-gd3.md` 5.3 ("Người duyệt: quản lý phòng ban"), ma trận quyền mục 2.
- *Mô tả:* Quản lý cũng là nhân viên của phòng ban mình quản lý (`scope_department_id`), nên có thể tự gửi rồi tự duyệt giải trình và tự sửa ngày công. HR sửa bảng công của chính mình cũng có xung đột lợi ích tương tự.
- *Đề xuất:* quy tắc `reviewer ≠ requester`. Giải trình của quản lý chuyển cho HR hoặc Chủ DN. Thao tác sửa ngày công của chính mình bị chặn ở tầng API.

**R-10 · Cao · Thời điểm chốt ngày công mâu thuẫn với cửa sổ nhận event; cửa sổ có thể vắt qua nửa đêm**
- *Vị trí:* `thiet-ke-gd3.md` F-04 ("Hết ca + 2 giờ: … VẮNG / THIẾU CHẤM CÔNG") và 5.2 (cửa sổ `end + 4h`).
- *Mô tả:*
  - Scheduler gán `ABSENT`/`MISSING_OUT` lúc end+2h, nhưng event tới end+4h vẫn được tính. Trạng thái bị đổi ngược sau khi đã "chốt" và có thể đã gửi thông báo "thiếu chấm công".
  - Với ca 13:00–22:00, end+4h = 02:00 hôm sau. Ca không qua nửa đêm nhưng cửa sổ thì có, mâu thuẫn với "ngày công = ngày địa phương".
- *Đề xuất:* thời điểm chốt ≥ cuối cửa sổ (end+4h). Gán event vào ca theo khoảng `[start−3h, end+4h]` của **ca**, không theo ngày lịch. Kiểm tra cửa sổ của hai ngày liên tiếp không chồng nhau.

**R-11 · Cao · Trang "So sánh mô hình" thành công cụ tra cứu danh tính bằng ảnh bất kỳ**
- *Vị trí:* `thiet-ke-gd3.md` W-15, `/models/compare` ("upload 1 ảnh → điểm top-1/top-5").
- *Mô tả:* Chủ DN tải ảnh bất kỳ (ảnh mạng xã hội, ảnh chụp lén) lên và nhận top-5 nhân viên giống nhất. Đây là chức năng tìm người bằng khuôn mặt, nằm ngoài mục đích chấm công/ra vào, nên khó hợp với nguyên tắc dùng đúng mục đích. Nó cũng lệ thuộc gallery thật để trình diễn.
- *Đề xuất:* chỉ cho chọn **event đã có** hoặc ảnh từ một "gallery demo" riêng (người tình nguyện). Mọi lần gọi ghi `audit_log`. Ẩn top-5 tên, chỉ hiện điểm.

**R-12 · Cao (có thể Nghiêm trọng nếu xác nhận) · Nguồn và điều kiện sử dụng CASIA-WebFace chưa được làm rõ**
- *Vị trí:* `de-xuat-tong-the.md` 8.1; `tong-hop` A12; `de-cuong.md` 4 (dataset "bản insightface, Kaggle").
- *Mô tả:* Trang CBSR ghi CASIA-WebFace **chỉ dành cho nghiên cứu và giáo dục**, phải xin bằng thỏa thuận do lãnh đạo khoa/trường ký, **không nhận cá nhân**. README insightface ghi dữ liệu train đóng gói và các model train từ đó **chỉ cho nghiên cứu phi thương mại**. Dự án dùng bản insightface tải từ Kaggle (`env.json`: `debarghamitraroy/casia-webface`). Mục đích nghiên cứu/giáo dục là phù hợp, nhưng việc **không có thỏa thuận** với CBSR thì chưa rõ. Thiết kế mới nói "chỉ dùng cho demo", chưa nói chuyện nguồn tải.
- *Đề xuất:* không đổi dữ liệu (quyết định đã chốt). Ghi rõ trong quyển: nguồn tải, điều khoản CBSR + insightface, "mô hình và mọi embedding sinh ra chỉ dùng cho nghiên cứu/giáo dục". Báo GVHD như đã làm với IJB-C. App nên hiện nhãn "Bản trình diễn nghiên cứu, không dùng thương mại".

### Trung bình

**R-13 · Trung bình · Ngưỡng vận hành chọn từ log test: không rò rỉ vào kết luận nghiên cứu, nhưng cách trình bày cần chặt hơn; có phương án lấy từ validation**
- *Vị trí:* `de-xuat-tong-the.md` mục 5 (i)–(iii); `tong-hop` C.
- *Đánh giá:*
  - Không rò rỉ vào CH1/CH2: test đã mở và báo cáo trước (nhật ký Buổi 46), ngưỡng 0,466 không quay lại chọn mô hình hay cấu hình.
  - Nhưng nếu quyển viết "ngưỡng mặc định cho FPIR 1%" thì đó là số **khớp trên chính tập test**: FPIR 1% là theo định nghĩa, không phải kết quả kiểm chứng.
  - Lập luận (i) "gallery văn phòng nhỏ hơn → ngưỡng BLUFR thận trọng hơn" chỉ đúng nếu phân phối điểm impostor giống LFW. Thực tế có lệch miền: người Việt so với CASIA/LFW chủ yếu người nổi tiếng phương Tây, camera tablet, JPEG q80. Thêm nữa, template là trung bình 3–5 ảnh, trong khi BLUFR dùng 1 ảnh mẫu. **[ngoài log — nhận định, chưa đo]**
- *Đề xuất:*
  - Cách 1 (sạch hơn): ngưỡng mặc định lấy từ **validation** của checkpoint, `thr@far=1e-05` ở epoch 18 = 0,4233. Lúc đó BLUFR trở thành kiểm chứng độc lập: FPIR thực đo 5,0%, FNIR 10,6% (`CH2_tai_nguong_co_dinh["val_thr@far=1e-05"]`). Số này đã có sẵn, không cần chạy thêm.
  - Cách 2: giữ 0,466 nhưng quyển ghi đúng là "hiệu chỉnh trên BLUFR-test sau khi đã báo cáo; không phải kết quả".
  - Cả hai cách: thêm bước hiệu chỉnh tại chỗ (lộ trình đã có), và câu (i) ghi là giả định.

**R-14 · Trung bình · Chọn mặt lớn nhất vs gần tâm; câu "dùng lại đúng hàm căn chỉnh của `align_lfw.py`" chưa chính xác**
- *Vị trí:* `de-xuat-tong-the.md` 5.1 và 8.3; `thiet-ke-gd3.md` 4.
- *Mô tả:*
  - Phép biến đổi căn chỉnh (`norm_crop`, template ArcFace) **giống hệt**, nên không vi phạm "không đổi cách căn chỉnh".
  - Khác ở **chọn mặt**: `FaceAligner` gọi `pick_center_face`, có `retry_threshold=0.3` và `fallback_landmarks` (trung vị landmark LFW, vô nghĩa với camera kiosk). Trên LFW có 2334/13233 ảnh (17,6%) nhiều mặt, nên parity 9.2 dùng "mặt lớn nhất" có thể lệch ở các ảnh này.
  - Ở kiosk, mặt lớn nhất thường đúng người đứng trước camera, nên ảnh hưởng tới chất lượng nhận dạng nhỏ. Tuy vậy, chưa đo bao nhiêu ảnh trong 2334 ảnh có mặt lớn nhất ≠ mặt gần tâm.
- *Đề xuất:* Hub gọi trực tiếp `YuNetDetector.detect` + `norm_crop`, **không** dùng `FaceAligner` (tránh fallback). Parity 9.2 chạy ở chế độ `pick_center_face`, ghi riêng số ảnh khác nhau khi chuyển sang "lớn nhất". Sửa câu trong 8.3 thành "dùng lại cùng detector, cùng phép căn chỉnh; khác quy tắc chọn mặt".

**R-15 · Trung bình · Có câu khẳng định hiệu năng hoặc khả năng chưa đo mà không đánh dấu**
- *Vị trí và bằng chứng:*
  - `de-xuat` 5.1 "YuNet … chạy CPU vài ms": log căn chỉnh 13.233 ảnh mất 1052,8 s (≈ 80 ms/ảnh, gồm đọc ảnh hai lượt + warp, CPU Kaggle; `align_summary.seconds`). Không chứng minh "vài ms".
  - `de-xuat` 6 "4GB VRAM dư sức": chưa đo (log train ghi 6,2 GB nhưng đó là lúc **train**, không áp dụng cho suy luận).
  - `de-xuat` 5.4 "MiniFASNet … phát hiện ảnh in và màn hình điện thoại": khả năng chưa kiểm.
  - `de-xuat` 5 (i) "thường thận trọng hơn": xem R-13.
- *Đề xuất:* gắn nhãn **[chưa đo]** hoặc **[mục tiêu]** như mục 10 GĐ3 đã làm, và đưa các phép đo vào M0/M1.

**R-16 · Trung bình · Quy tắc chấm công: các trường hợp biên**
- *Vị trí:* `thiet-ke-gd3.md` 5.2.
- *Mô tả:*
  1. Ra ăn trưa có quét (12:00), vào lại (13:00), chiều quên quét: `check_out` = 13:00 → `EARLY` thay vì `MISSING_OUT`. Đây là sai lệch có hệ thống với người hay ra ngoài.
  2. Không có bảng **ngày lễ / lịch nghỉ công ty**, nên dịp Tết mọi người thành `ABSENT` trừ khi HR đánh dấu từng người.
  3. Nhân viên không có ca nhưng vẫn đến: `OFF`, event bị bỏ (tăng ca không ghi nhận, nên nói rõ là ngoài MVP).
  4. Đến sớm hơn 3 h trước ca: event ngoài cửa sổ, nên thành `ABSENT` dù có mặt.
  5. Nhiều `shift_assignment` cá nhân chồng thời gian: chưa có ràng buộc.
  6. `worked_min` trừ nghỉ trưa cố định, không trừ thời gian ra ngoài thật.
  7. Đi qua cửa nhiều lần: cooldown 60 s ổn; nhưng cửa `ACCESS_ONLY` có tính công không? Mục 5.2 nói không, nên ghi rõ trên UI E-02.
- *Đề xuất:* thêm bảng `holiday`. Quy tắc "giờ ra = event cuối **sau mốc end − X**", hoặc gắn cờ "nghi quên quét" khi event cuối < end − 2h **[khởi đầu]**. Ràng buộc không chồng lấn bằng exclusion constraint của PostgreSQL (`tstzrange`/`daterange`). Ghi các trường hợp ngoài MVP vào quyển.

**R-17 · Trung bình · Mô hình dữ liệu: thiếu ràng buộc, chỉ mục, nguồn sự thật bị trùng**
- *Vị trí:* `thiet-ke-gd3.md` mục 6.
- *Mô tả và đề xuất:*
  - **UNIQUE còn thiếu:** `face_embedding(sample_id, model_id)`; `face_template(employee_id, model_id)`; `threshold_profile(model_id, level)` (trừ CUSTOM); `recognition_model`: tối đa 1 dòng `is_active` / `PRODUCTION` (partial unique index); `employee(company_id, code)` (hiện ghi "duy nhất" toàn cục, sẽ vướng khi đa công ty); `attendance_period(company_id, month)`; `device(token_hash)`; `user_role(user_id, role, scope_department_id)`; `face_consent`: tối đa 1 bản còn hiệu lực/nhân viên.
  - **Chỉ mục:** `recognition_event(gate_id, occurred_at)`, `(employee_id, occurred_at)`, partial `(handled_status) WHERE handled_status='NEW'`; `attendance_day(period_id)`; `audit_log(at)`.
  - **Hai nguồn sự thật cho "quản lý":** `department.manager_user_id` và `user_role.scope_department_id`. Chọn một.
  - **Append-only chỉ là quy ước:** nên dùng trigger chặn `UPDATE` các cột nhận dạng, hoặc tách bảng `event_handling`.
  - **Rút đồng ý:** xoá `face_sample` làm hỏng `employee.avatar_sample_id` (FK). Avatar là ảnh khuôn mặt hiện công khai trên Kiosk K-04, nên cần consent riêng hoặc dùng ảnh hồ sơ khác. Event cũ vẫn giữ `employee_id`, `top1_score`, `snapshot_path`: crop của event `MATCH`/`IS_EMPLOYEE` là ảnh khuôn mặt, nên phải xoá theo consent (hoặc theo `retention_days` áp cho **mọi** crop, không chỉ người lạ).
  - **Đổi mô hình:** event lưu `model_id` + `threshold_used` là tốt. Cần thêm `alignment_version` (detector + OpenCV + quy tắc chọn mặt) vào `recognition_model`, vì re-extract từ PNG chỉ hợp lệ khi căn chỉnh không đổi.
  - **Lưu trữ:** ảnh PNG đã căn chỉnh là dữ liệu sinh trắc lưu thô. "Mã hoá khi lưu" đang để lộ trình. Tối thiểu MVP nên dùng BitLocker cho ổ dữ liệu Hub và quyền thư mục (Điều 31: kiểm soát truy cập, bảo mật thiết bị lưu trữ).

**R-18 · Trung bình · Bảo mật Kiosk: ghép thiết bị, PIN HR, token WebSocket**
- *Vị trí:* `thiet-ke-gd3.md` F-01, F-02, 7, 10.
- *Mô tả:*
  - Mã ghép 6 số (10⁶ khả năng, 10 phút) không có rate-limit (mục 10 chỉ rate-limit đăng nhập và PIN).
  - "PIN HR" chưa rõ là PIN chung công ty hay PIN riêng từng HR. Nếu chung thì audit không biết ai đăng ký. PIN nhập ở nơi công cộng cũng dễ bị nhìn trộm.
  - Kiosk bị chiếm (token + PIN) có thể đăng ký khuôn mặt kẻ gian vào hồ sơ một nhân viên. F-06 đã chống đầu độc gallery, nhưng F-02 thì chưa.
  - Device token không hết hạn và không xoay vòng.
  - Token WS truyền qua query string sẽ bị ghi vào log truy cập.
- *Đề xuất:*
  - Rate-limit + khoá sau N lần cho `/kiosk/pair`.
  - PIN riêng từng HR (gắn `user_id`, ghi audit). Đăng ký mới hoặc thay khuôn mặt cần **xác nhận lần 2 trên Web Admin** (trạng thái `PENDING_REVIEW`).
  - Device token có hạn và refresh.
  - Xác thực WS bằng message đầu tiên hoặc header `Sec-WebSocket-Protocol`.
  - `/ws/monitor` chỉ đẩy dữ liệu đúng phạm vi vai trò.

**R-19 · Trung bình · Chống giả mạo: ngưỡng và crop không chuyển nguyên từ dự án gốc; vai trò trong quyển**
- *Vị trí:* `de-xuat-tong-the.md` 5.4; `thiet-ke-gd3.md` 4 (L_low/L_high 0,5/0,9).
- *Mô tả:*
  - Dự án Silent-Face crop theo bbox của detector riêng của họ, với tỉ lệ phóng 2,7 và 4,0 rồi resize về 80×80 **(chưa xác minh trong code gốc, theo tên file trọng số `2.7_80x80_MiniFASNetV2.pth` / `4_0_0_80x80_MiniFASNetV1SE.pth`)**. Bbox của YuNet có kích thước và tâm khác, nên phân phối điểm thay đổi.
  - README chỉ mở mã "APK model"; "high-precision model" không mở. Mô hình mở là bản nhẹ.
  - **Về đề cương:** không mâu thuẫn mục 2, vì đề cương chỉ loại anti-spoofing khỏi **trọng tâm nghiên cứu**. Nhưng cần: (a) báo GVHD (đã ghi trong tong-hop D4); (b) quyển đặt nó ở chương hệ thống, không có bảng "độ chính xác" của nó; (c) ghi vào nhật ký khi An chốt.
- *Đề xuất:* M7 có bước hiệu chỉnh L_low/L_high trên một bộ thử nội bộ (ảnh thật / in / màn hình) và **ghi log** như kết quả kiểm thử chức năng. Thêm cờ cấu hình "tắt chống giả mạo" để demo không bị chặn nếu MiniFASNet chạy kém với bbox YuNet.

**R-20 · Trung bình · Phạm vi MVP lớn so với nhóm 2 người**
- *Vị trí:* `de-xuat-tong-the.md` 7, 9; `thiet-ke-gd3.md` 8.
- *Mô tả:* 4 thành phần, **37 màn hình** (11 Kiosk + 10 Employee + 16 Web), RBAC có phạm vi, bộ máy chấm công (ca, chốt kỳ, giải trình, Excel), quy tắc ra vào, chống giả mạo 2 lớp, so sánh 2 mô hình, audit. Phần quyển và slide cũng còn nhiều.
- *Đề xuất cắt (theo thứ tự ưu tiên giữ lõi chứng minh mô hình):*
  - (1) Employee App → gộp vào Web Admin dạng responsive (E-02, E-03, E-05, E-08), bỏ build mobile thứ hai.
  - (2) Quy tắc ra vào → chỉ `gate.default_policy` + danh sách phòng ban được phép, bỏ khung giờ / ưu tiên.
  - (3) Chốt kỳ công → chỉ xuất Excel theo tháng, bỏ khoá/mở khoá.
  - (4) Chống giả mạo → giữ MiniFASNet, thử thách để lộ trình (hoặc ngược lại).
  - (5) Notification, W-02 biểu đồ, K-10 → lộ trình.
  - **Giữ:** M0 parity, F-01/F-02/F-03, W-10, W-14, W-15 (cầu nối nghiên cứu), consent/xoá.

**R-21 · Trung bình · Khả thi phần cứng và môi trường: chưa đo, có vài điểm nghẽn**
- *Vị trí:* `thiet-ke-gd3.md` 1.4, 10; `de-xuat-tong-the.md` 6.
- *Mô tả:*
  - Ước lượng tải: 3 kiosk × 4 khung/s = 12 khung/s qua **một** worker, mỗi khung gồm YuNet (CPU) + MiniFASNet (2 mô hình nhỏ) + R18 ×2 (flip). Ngân sách khoảng 83 ms/khung. Khả thi về VRAM (R18 fp16 vài trăm MB) **[nhận định, chưa đo]**, nhưng YuNet trên CPU là ẩn số (R-15).
  - FastAPI async: suy luận PyTorch phải chạy ngoài event loop (thread/process riêng). Nếu không, WebSocket của các kiosk khác và Web Admin bị đứng.
  - Đề cương ghi ổ đĩa còn ~21 GB (12/11). Docker Desktop (WSL2) + Postgres + Node + **Android SDK cho Expo dev build (react-native-vision-camera cần native build)** có thể vượt mức này.
  - Hub ghi Python 3.11, còn feature BLUFR được tạo bằng Python 3.13 / torch 2.11+cu130.
- *Đề xuất:*
  - Thêm phép đo vào M1: latency p50/p95 từng bước, 1 và 3 kiosk giả lập.
  - Cân nhắc **EAS Build** (cloud) để khỏi cài Android SDK local **(chưa xác minh hạn mức gói miễn phí)**, hoặc Postgres cài native thay Docker.
  - Ghi phiên bản torch/OpenCV của Hub vào `recognition_model` và parity log.

**R-22 · Trung bình · Nghĩa vụ pháp lý còn thiếu trong thiết kế (ngoài R-02, R-07, R-08)**
- *Vị trí:* `de-xuat-tong-the.md` 8.5 ("chưa tra").
- *Mô tả:*
  - Khách hàng mục tiêu là SME. Theo VCCI, Điều 41 NĐ 356/2025 cho doanh nghiệp nhỏ / khởi nghiệp ân hạn 5 năm, nhưng ngoại lệ **không áp dụng khi trực tiếp xử lý dữ liệu cá nhân nhạy cảm**. Hệ thống sinh trắc đặt khách hàng vào diện phải tuân thủ đầy đủ.
  - NĐ 356 yêu cầu lưu trữ sự đồng ý.
  - Hồ sơ đánh giá tác động (DPIA) được Bộ Công an đánh giá (theo PwC).
  - Điều 31 yêu cầu có hệ thống theo dõi để phát hiện xâm phạm, và thông báo cho chủ thể khi gây thiệt hại.
- *Đề xuất:* thiết kế đã có `face_consent` (có phiên bản) và audit, đó là nền tốt. Bổ sung:
  - Lưu **bản điều khoản** theo `terms_version` (nội dung, mục đích, thời hạn lưu, quyền rút).
  - Xuất "hồ sơ xử lý dữ liệu" phục vụ DPIA.
  - Log truy cập ảnh khuôn mặt (ai xem W-04 tab Khuôn mặt).
  - Mục "Tuân thủ pháp luật" trong quyển, trích đúng Luật 91/2025/QH15 và NĐ 356/2025/NĐ-CP (thay NĐ 13/2023).

### Thấp / Góp ý

**R-23 · Thấp · Sơ đồ khớp text Mermaid nhưng còn thiếu sót**
- Đã xem cả 8 PNG; nội dung trùng các khối Mermaid trong `thiet-ke-gd3.md`.
- `08-erd.png`:
  - Thiếu `NOTIFICATION`.
  - Thiếu quan hệ `RECOGNITION_MODEL–RECOGNITION_EVENT` (`model_id`), `DEVICE–RECOGNITION_EVENT`, `ACCESS_RULE`/`SHIFT_ASSIGNMENT–EMPLOYEE/DEPARTMENT`, `ATTENDANCE_DAY–SHIFT`, `ATTENDANCE_DAY–RECOGNITION_EVENT` (check_in/out_event_id), `ATTENDANCE_REQUEST–USER_ACCOUNT` (reviewer), `DEPARTMENT–USER_ACCOUNT` (manager), `DEVICE–FACE_SAMPLE`.
- `05-F03`: nhánh "Nghi giả mạo" không có bước "Ghi event SPOOF" (hai nhánh kia đều có), trong khi mục 6 có `result = SPOOF`.
- `07-state`: ghi "k khung liên tiếp" (khác giả mã, xem R-05).
- `02-use-case`: Mermaid vẽ dạng cây, không có ranh giới hệ thống. Quyển (chương phân tích thiết kế) nên vẽ lại bằng công cụ UML (draw.io / PlantUML) có system boundary.

**R-24 · Thấp · Tên trường `DIR_rank1@FAR=…` thực chất là FPIR**
- Trong `KQ`, các trường `DIR_rank1@FAR=0.01`, `FPIR_actual@0.01`, `thr_DIR@0.01` dùng "FAR" cho 1:N.
- Thiết kế đã viết đúng "FPIR 1e-2". Khi trích vào quyển hoặc trang W-14, nên giữ chữ FPIR và chú thích tên trường.

**R-25 · Góp ý · Câu chuyện CH2 trong nhật ký lệch với quyết định của app**
- `nhat-ky.md` (mục CH2, dòng 12) viết t = b̃/s là "điểm ứng dụng mạnh nhất của V1 cho cổng điểm danh (ngưỡng mặc định 'đúng' hơn)".
- App lại quyết định **không** dùng b̃/s vì FPIR TB 22%. Hai ý không mâu thuẫn về số liệu: V1 chặt hơn UniFace (22% so với 42%, TB UniFace s3 = 42,15%). Nhưng quyển cần nói nhất quán: "b̃/s của V1 tốt hơn **tương đối**, chưa đủ dùng trực tiếp cho cửa ra vào".

---

## 4. Pháp lý & giấy phép

| Thành phần | Giấy phép / điều khoản | Link nguồn | Dùng thương mại được? | Ghi chú |
|---|---|---|---|---|
| Silent-Face-Anti-Spoofing (code, Minivision) | Apache-2.0 (file LICENSE, Minivision 2020) | https://raw.githubusercontent.com/minivision-ai/Silent-Face-Anti-Spoofing/master/LICENSE ; https://github.com/minivision-ai/Silent-Face-Anti-Spoofing | Có (giữ NOTICE, ghi thay đổi) | README: chỉ mở "APK model", "high-precision model" không mở; công ty bán SDK riêng |
| Trọng số MiniFASNet pretrained (trong repo) | Không có điều khoản riêng cho trọng số; nằm trong repo Apache-2.0 | như trên | **(chưa xác minh)**: không thấy điều khoản riêng; dữ liệu train không công bố | Coi là Apache-2.0 theo repo là suy luận; ghi rõ "chưa xác minh dữ liệu train" |
| YuNet `face_detection_yunet_2023mar.onnx` (OpenCV Zoo) | MIT ("All files in this directory are licensed under MIT License") | https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/README.md ; bản lưu: `02-thuc-nghiem/code/LICENSES/opencv_zoo_yunet_MIT.txt` | Có | Dữ liệu train YuNet: **(chưa xác minh)** |
| CASIA-WebFace (dữ liệu train) | Chỉ nghiên cứu và giáo dục; xin bằng thỏa thuận do lãnh đạo khoa/trường ký, không nhận cá nhân | http://www.cbsr.ia.ac.cn/english/CASIA-WebFace-Database.html | **Không** | Dự án dùng bản insightface tải từ Kaggle: xem R-12 |
| insightface: code (`iresnet.py`, `face_align` template) | MIT | https://github.com/deepinsight/insightface (mục License); bản lưu `code/LICENSES/insightface_MIT.txt` | Có | |
| insightface: model pretrained + dữ liệu train đóng gói (`faces_webface_112x112`) | Chỉ nghiên cứu phi thương mại | https://github.com/deepinsight/insightface | **Không** | Thiết kế không dùng model insightface (đúng). Nhưng dữ liệu train của đề tài là bản đóng gói này, nên checkpoint của đề tài cũng chỉ dùng cho nghiên cứu/giáo dục |

**Văn bản pháp luật Việt Nam về dữ liệu cá nhân (dữ liệu sinh trắc học)**

| Văn bản | Hiệu lực | Điểm chính liên quan app | Nguồn |
|---|---|---|---|
| Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 (thông qua 26/6/2025) | 01/01/2026 | Đ.31: nghĩa vụ với dữ liệu sinh trắc (bảo mật vật lý thiết bị lưu trữ và truyền tải; hạn chế người truy cập; hệ thống phát hiện xâm phạm; tuân thủ tiêu chuẩn; thông báo chủ thể khi gây thiệt hại). Đ.25: dữ liệu người lao động lưu theo luật/thoả thuận, xoá/huỷ khi chấm dứt hợp đồng (trừ thoả thuận/luật khác); biện pháp công nghệ giám sát phải hợp pháp và người lao động được biết. Đ.9–10: sự đồng ý, rút lại sự đồng ý | https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-31 ; …/dieu-25 ; https://gvlawyers.com.vn/wp-content/uploads/2025/09/VN_Legal-alert-_Law-on-PDP-2025.pdf |
| Nghị định 356/2025/NĐ-CP (31/12/2025), hướng dẫn Luật, **thay NĐ 13/2023** | 01/01/2026 | Đ.4: dữ liệu sinh trắc học thuộc danh mục dữ liệu cá nhân nhạy cảm; phải lưu trữ sự đồng ý; hồ sơ DPIA nộp và được Bộ Công an đánh giá; Đ.41: ân hạn 5 năm cho DN nhỏ/khởi nghiệp **không áp dụng** khi trực tiếp xử lý dữ liệu nhạy cảm | https://thuvienphapluat.vn/van-ban/Quyen-dan-su/Nghi-dinh-356-2025-ND-CP-huong-dan-Luat-Bao-ve-du-lieu-ca-nhan-687428.aspx ; https://www.pwc.com/vn/vn/publications/2026/20260128-new-rules-personal-data-protection.pdf ; https://vcci.com.vn/tin-tuc/luat-bao-ve-du-lieu-ca-nhan-luu-y-ve-hanh-lang-phap-ly-moi-cho-doanh-nghiep ; https://lsvn.vn/phuong-thuc-the-hien-su-dong-y-cua-chu-the-du-lieu-ca-nhan-a167945.html |
| Nghị định 330 (xử phạt an ninh mạng + bảo vệ dữ liệu cá nhân) | **(chưa xác minh số hiệu đầy đủ / ngày hiệu lực)** | Chế tài khi không tuân thủ | https://www.ey.com/content/dam/ey-unified-site/ey-com/vi-vn/technical/tax/documents/ey-vn-decree-330-providing-sanctions-for-personal-data-protection.pdf |

**Đối chiếu thiết kế với các yêu cầu**

| Yêu cầu | Thiết kế hiện tại | Đủ? |
|---|---|---|
| Có sự đồng ý, lưu trữ sự đồng ý, rút được | `face_consent` có `terms_version`, `revoked_at`; rút → xoá | Gần đủ: thiếu lưu nội dung điều khoản; thiếu phương án thay thế (R-08) |
| Xoá khi chấm dứt hợp đồng | Không có | **Thiếu** (R-02) |
| Bảo mật truyền tải | HTTP trong LAN | **Thiếu** (R-07) |
| Bảo mật lưu trữ, hạn chế truy cập | RBAC; mã hoá để lộ trình | Một phần (R-17) |
| Phát hiện xâm phạm, thông báo | audit log thao tác ghi | Một phần: chưa log truy cập đọc ảnh, chưa có quy trình thông báo (R-22) |
| Thời hạn lưu | `retention_days` 30 ngày cho ảnh người lạ | Một phần: chưa áp cho crop của nhân viên, chưa có thời hạn cho mẫu đăng ký |

**Chưa xác minh được**
- Nguyên văn NĐ 356/2025 (đã đọc qua bản tóm tắt của EY, PwC, VCCI, lsvn, thuvienphapluat), gồm thời hạn 20 ngày xoá dữ liệu và chi tiết Đ.41.
- Điều khoản riêng cho trọng số MiniFASNet và dữ liệu train của nó.
- Dữ liệu train YuNet.
- Số hiệu, hiệu lực Nghị định 330.
- Nguyên văn Điều 9–10 Luật 91/2025 về hình thức đồng ý.

---

## 5. Những điểm thiết kế làm tốt
- Sự kiện append-only, ngày công là dữ liệu dẫn xuất qua `recompute_day` idempotent; giải trình giữ event gốc.
- Model registry + `threshold_profile.source_ref` + `threshold_used`/`model_id` trong mỗi event: truy vết được mọi quyết định về đúng mô hình, ngưỡng và log.
- Đặt M0 (parity, checksum, ngưỡng sinh tự động từ JSON) trước mọi tính năng; dùng code thực nghiệm dạng chỉ-đọc kèm hash.
- Quyết định không dùng t = b̃/s làm mặc định là đúng và có số liệu (sau khi sửa R-01).
- Ghi rõ DIR ≈ 83,7% nghĩa là khoảng 16% lượt bị từ chối, và "app PHẢI đo tại chỗ": trung thực.
- "Là nhân viên" không tự thêm ảnh vào hồ sơ (chống đầu độc gallery).
- Tham số đánh dấu **[khởi đầu]**; mục tiêu hiệu năng ghi là "mục tiêu, sẽ ĐO".
- Lưu ảnh căn chỉnh để trích lại khi đổi mô hình.
- Flip-cộng làm embedding **bất biến với lật gương** (emb(x) = L2(B(x)+B(flip x)) = emb(flip x)), nên ảnh từ camera trước có lật gương hay không cũng không ảnh hưởng nhận dạng. Chỉ hướng thử thách quay đầu là cần quy đổi. Đây là điểm cộng nên ghi trong quyển.

---

## 6. Câu hỏi cho An
1. **Ngưỡng mặc định:** giữ 0,466 (hiệu chỉnh trên BLUFR-test, ghi rõ là hiệu chỉnh sau test), hay chuyển sang ngưỡng từ **validation** 0,4233 (BLUFR kiểm chứng FPIR 5,0%, FNIR 10,6%)? (R-13)
2. **HTTPS ngay từ MVP** (mkcert, chi phí thấp) hay chấp nhận ghi "không tuân thủ Điều 31" cho bản demo? (R-07)
3. **Nghỉ việc:** xoá sinh trắc ngay, hay sau N ngày? Cần trạng thái `TERMINATED` tách khỏi `INACTIVE`? (R-02)
4. **Người không đồng ý:** phương án chấm công thay thế nào (Lễ tân chấm hộ có lý do / PIN cá nhân)? (R-08)
5. **CASIA bản Kaggle:** nhóm/trường đã có thỏa thuận với CBSR chưa? Có báo GVHD như IJB-C không? (R-12)
6. **Cắt phạm vi:** đồng ý gộp Employee App vào Web responsive và rút gọn quy tắc ra vào / chốt kỳ không? Nếu không, ưu tiên cắt gì? (R-20)
7. **Checkpoint cho Hub:** nạp bản trích chỉ-backbone (`C:\datn-backbones-24`) hay `best.pt` gốc + `strip_map`? (R-03)
8. **Chế độ suy luận:** chạy fp16 (giống BLUFR) hay fp32 trên Hub? (R-04)
9. **Chọn mặt:** giữ "lớn nhất" cho kiosk (khuyến nghị) và ghi khác biệt với `pick_center_face` trong quyển? (R-14)
10. **Câu chuyện CH2:** thống nhất cách nói "b̃/s của V1 tốt hơn tương đối nhưng chưa đủ dùng trực tiếp" trong quyển và slide? (R-25)
11. **PIN HR:** riêng từng người hay chung? Có cần xác nhận đăng ký lần 2 trên Web Admin? (R-18)

---

## 7. Phụ lục — lệnh và script đã chạy

Môi trường: `device_bash` trên máy An (VM Linux, thư mục dự án mount chỉ-đọc theo quy ước review). Script lưu ở thư mục tạm `$HOME/rv/`, **không** nằm trong dự án.

### A. `doi_chieu.py`: val 3 seed, quy ước feature, BLUFR (thr, FPIR, DIR, ngưỡng validation), meta
```python
import json, statistics as st, glob, os, sys
ROOT = sys.argv[1]
R = os.path.join(ROOT, '02-thuc-nghiem/results')
runs = {'V1 s1':'V1-s1-Ngan','V1 s2':'V1-s2-Hy','V1 s3':'V1-s3-Hy','UniFace s3':'UniFace-s3-Ngan'}
for name, d in runs.items():
    rd = glob.glob(f'{R}/{d}/phien-1/r18_*/')[0]
    rows = [json.loads(l) for l in open(rd+'val.jsonl') if l.strip()]
    ep = [r for r in rows if r.get('tag','').startswith('epoch_')]
    best = max(ep, key=lambda r: r['results']['tar@far=0.001'])
    sm = json.load(open(rd+'summary.json'))['best_val']
    print(name, best['results']['tar@far=0.001'], best['epoch'], len(ep), sm['value'], sm['epoch'],
          best['results']['thr@far=0.001'], best['results']['thr@far=1e-05'])
J = json.load(open(f'{R}/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json'))
print(J['quy_uoc_feature'], J['toan_ven_du_lieu']['lfw']['align_summary']['detector'],
      J['toan_ven_du_lieu']['lfw']['align_summary']['multi_face_images'])
for key in ['r18_uniface_v1_lam0.6_m0.45_s1_e28:best','r18_uniface_v1_lam0.6_m0.45_s2_e28:best',
            'r18_uniface_v1_lam0.6_m0.45_s3_e28:best','r18_uniface_lam0.6_m0.45_s3_e28:best']:
    r = J['ket_qua'][key]; pt = r['blufr']['per_trial']
    m = lambda f: (st.mean(pt[t][f] for t in pt), st.stdev([pt[t][f] for t in pt]))
    fp = [pt[t]['tai_nguong_co_dinh']['t=b/s']['FPIR'] for t in sorted(pt)]
    print(key, r['meta']['epoch'], r['meta']['sha256'], r['meta']['is_stripped'], r['meta'].get('t_eq30'))
    for f in ['thr_DIR@0.01','thr_DIR@0.1','DIR_rank1@FAR=0.01','DIR_rank1@FAR=0.1']: print(' ', f, m(f))
    print('  FPIR@t=b/s mean', st.mean(fp), 'trial01', fp[0],
          'CH2 TB', r['blufr']['CH2_tai_nguong_co_dinh']['t=b/s']['FPIR']['TB'])
    for k2, v in r['blufr']['CH2_tai_nguong_co_dinh'].items():
        if k2.startswith('val_thr'): print('  ', k2, v['threshold'], v['FPIR']['TB'], v['FNIR_rank1']['TB'])
```
Kết quả chính (trích stdout):
```
V1 s1: val max=0.78011 ep19 | summary 0.78011 ep19 | thr@far=1e-5=0.4244
V1 s2: val max=0.77741 ep21 | summary 0.77741 ep21 | thr@far=1e-5=0.4262
V1 s3: val max=0.78023 ep18 | summary 0.78023 ep18 | thr@far=1e-3=0.3043 thr@far=1e-5=0.4233
UniFace s3: val max=0.77551 ep20 | summary 0.77551 ep20
quy_uoc_feature = {'flip': 'sum', 'tien_xu_ly': 'RGB uint8 112x112 -> (x/255-0.5)/0.5; flip ngang (dims=[3]); cộng; L2-normalize; cosine'}
detector = face_detection_yunet_2023mar.onnx | multi_face_images = 2334 | n_images = 13233
V1 s3 best: epoch=18 sha256=b00612f5…a065 is_stripped=True t_eq30=0.3736472427845001
   thr_DIR@0.01 mean=0.4657 sd=0.0079 | thr_DIR@0.1 mean=0.4014 sd=0.0035
   DIR_rank1@FAR=0.01 mean=0.8365 | FPIR@t=b/s mean=0.2210 trial01=0.2111
   val_thr@far=1e-05: thr=0.4233 FPIR TB=0.0502 FNIR TB=0.1056
V1 s1 best: FPIR@t=b/s mean=0.2363 trial01=0.2245 | thr_DIR@0.01 mean=0.4727
V1 s2 best: FPIR@t=b/s mean=0.3000 trial01=0.2888 | thr_DIR@0.01 mean=0.4746
UniFace s3 best: epoch=20 sha256=cfe78d46…5d2c | FPIR@t=b/s mean=0.4215 | thr_DIR@0.01 mean=0.4148
```

### B. `protA.py`: kiểm chéo ngưỡng bằng Protocol A (V1 s3)
```python
import json, statistics as st, sys
J = json.load(open(sys.argv[1]))
r = J['ket_qua']['r18_uniface_v1_lam0.6_m0.45_s3_e28:best']['protocol_a']['per_split']
for f in ['thr@fpir=0.01','thr@fpir=0.1','tpir@fpir=0.01']:
    v = [r[s][f] for s in r]; print(f, st.mean(v), st.stdev(v), len(v))
print('fpir@t=b/s', st.mean(r[s]['at_threshold']['fpir'] for s in r))
```
```
thr@fpir=0.01 0.4683 0.0084 10 | thr@fpir=0.1 0.4014 0.0039 10 | tpir@fpir=0.01 0.8145 | fpir@t=b/s 0.2144 | n_gallery_ids {840}
```

### C. SHA-256 checkpoint gốc và bản đồ trích backbone
```bash
sha256sum results/V1-s3-Hy/phien-1/r18_*/checkpoints/best.pt results/UniFace-s3-Ngan/phien-1/r18_*/checkpoints/best.pt
# 120489621accefd7e78da9bd83fe3c6360ad94877e8ac4b9cdfa1038ec8eef88  …V1 s3 best.pt (137372031 byte)
# 3846bb9aa8967ae6d07bbf05a9e621eb7fcbbbdc6d415257e0d4aa04c04049e9  …UniFace s3 best.pt (116793283 byte)
python3 -c "import json;d=json.load(open('eval-test/tools/windows/logs/strip_map_ban_sao.json'));[print(v) for v in d.values() if 's3_e28:best' in v['id'] and 'uniface' in v['id']]"
# V1 s3:      source 120489621a… → dest b00612f58a… (96212289 byte)  = meta.sha256 trong KQ
# UniFace s3: source 3846bb9aa8… → dest cfe78d4685… (96212161 byte)
```

### D. Chữ ký hàm và chế độ trích feature
```bash
grep -n "^def \|^class \|    def \|score_threshold" code/fr/align/*.py
grep -n "def extract_embeddings" -A14 code/fr/eval/verification.py
grep -n "amp\|fp16\|extract_embeddings\|RGB" eval-test/evaltest/features.py
grep -n "cvtColor\|aligned_u8\|transpose" code/tools/align_lfw.py
cat results/2026-11-12_test-blufr-lfw/eval_test/env.json      # Python 3.13.16, torch 2.11.0+cu130, 2× Tesla T4
python3 -c "import zipfile;print(zipfile.ZipFile('results/2026-11-12_test-blufr-lfw/eval_test_20261112_1826.zip').namelist())"  # không có aligned_u8.npy
```

### E. Sơ đồ
8 file PNG trong `03-app/so-do/` được sao tạm (chỉ đọc) để xem và so với các khối Mermaid trong `thiet-ke-gd3.md` (kết quả ở R-23).
