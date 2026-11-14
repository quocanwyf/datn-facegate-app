# Báo cáo T04 — Lõi nhận dạng và bộ quyết định

- Trạng thái: XONG phạm vi T04, chưa nối WS/ghi sự kiện (T05).
- Commit nền: ce1e5f1; commit triển khai tra `T04: implement recognition components and exhaustive decision checks`.
- Máy: Windows, Python 3.13.13, torch 2.11.0+cpu; OpenCV 4.14.0. CPU, amp=False.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Vét cạn quyết định | 488.280 chuỗi dài 1–8 × 3 biến thể normal/lost_face/iou_reset = **1.464.840 chuỗi**; khớp tham chiếu độc lập | pytest.log | Đạt |
| 2 | Endpoint giả khi worker bận <50ms | **2,938ms**; một thread xử lý; 2 việc chờ/tablet, việc dư BUSY | pytest.log | Đạt |
| 3 | Embedding CPU max delta ≤1e-6 | **0,0** trên 1 ảnh webcam thật riêng từ kiểm T00; shape512, amp=False | pytest.log | Đạt |
| 4 | Gallery đọc DB, kể cả rỗng | DB seed thật trả 0 template, ready=True; NO_GALLERY phân biệt gallery lỗi; reload lỗi chặn top1 | pytest.log | Đạt |

Tổng **14 passed**, 2 cảnh báo từ vendor, 71,61 giây. Chạy bằng `.venv/Scripts/python.exe -m pytest tests/test_decision_exhaustive.py tests/test_worker.py tests/test_embed_smoke.py tests/test_gallery.py -q -s`, với TEST_FACES_DIR trỏ thư mục bằng chứng webcam riêng ngoài repo.

## Đã làm

Detector chọn bbox lớn nhất, kiểm cạnh ngắn/yaw theo settings; Embedder gọi norm_crop rồi biên RGB dùng chung T01/T02, chỉ vendor extract_features thực hiện chuẩn hóa/flip/L2. Liveness trả None vì chưa tới T13, khi tắt chống giả mạo mọi khung hợp lệ coi live.

Gallery lọc ACTIVE/SUSPENDED, FACE, consent, profile ACTIVE, template đúng model/công ty. Ma trận float32 CPU/CUDA, khóa bảo vệ reload/top1; reload lỗi xóa snapshot và ngừng nhận dạng. Gallery rỗng báo NO_GALLERY. Chỉ load từ DB, không tạo template/embedding giả.

Hàm quyết định thuần ưu tiên SPOOF > MATCH > UNKNOWN, dùng ≥ tại tau/L; DeviceSession quản lý cửa sổ hợp lệ, mất mặt >1s, IoU thấp, thời gian hiển thị và cooldown dùng chung theo cửa. Cooldown trả cờ suppressed/thời điểm trước để T05 không ghi event mới. Test độc lập kiểm từng tiền tố; UNKNOWN, ưu tiên khi thay tham số, đúng bằng ngưỡng, reset, INVALID và cooldown đều có kiểm.

Worker một thread/Queue; model initializer và mọi handler chạy trên thread này. submit trả concurrent Future để caller await asyncio.wrap_future; khống chế 2 khung chờ/thiết bị, lỗi khởi tạo được truyền về thay vì chạy nhận dạng.

## Dữ liệu và giới hạn

Ảnh webcam giữ tại thư mục riêng `%LOCALAPPDATA%/FaceGate/evidence`, không chép vào repo, không ghi vector/ảnh đầu ra. Ảnh đen không vượt kiểm chất lượng; chỉ ảnh có mặt hợp lệ được đo. Đây là so tính tương đương cùng ảnh, không phải số đo độ chính xác nhận dạng. Không tạo hồ sơ, sự kiện hay ngày công trong DB.

Vendor phát FutureWarning của skimage estimate/torch.cuda.amp; giữ nguyên vendor theo luật, không sửa để giấu cảnh báo. Bộ 44/44 và auth đã nghiệm thu T03; lần này chạy đúng các test của T04. Kiểm bí mật SẠCH (`secret-check.log`).

## File đã tạo

app/recog/{detector,embedder,liveness,gallery,decision,worker}.py; tests/{test_decision_exhaustive,test_worker,test_embed_smoke,test_gallery}.py; báo cáo và log.

## Đề xuất cho thiết kế / Cần An làm

Không cần thay nguồn chuẩn. Chưa archive FG-AI-002/003: còn nhánh enrollment nhiều mặt và bằng chứng NO_GALLERY/cooldown không ghi event qua WS ở T05. T02 GPU vẫn chạy riêng khi An rảnh.
