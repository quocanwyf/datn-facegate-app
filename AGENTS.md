# AGENTS.md — App chấm công & ra vào bằng khuôn mặt (ĐATN, bản demo)

Repo này chứa phần **App** của ĐATN "Mobile App tích hợp tối ưu AI cho hệ thống điểm danh và kiểm soát ra vào bằng nhận dạng khuôn mặt" (Nguyễn Quốc An, PTIT). Mô hình nhận dạng (UniFace + V1, R18) **đã train xong**; app chỉ tích hợp và trình diễn. Giao tiếp, báo cáo, chú thích nghiệp vụ: **tiếng Việt**; tên biến/hàm/commit: tiếng Anh.

## Đọc trước mỗi task (theo thứ tự)
1. `03-app/plan-codex/Txx-*.md` — task đang làm (phạm vi, tiêu chí nghiệm thu, điều kiện dừng). **Chỉ làm đúng task đó.**
2. `03-app/dac-ta-app.md` (v1.4.4) — đặc tả; §0a (bản demo) ưu tiên hơn các mục khác.
3. Theo task: `03-app/db/thiet-ke-db.md` + `db/schema.sql` · `03-app/openapi/openapi.yaml` + `ws-protocol.md` · `03-app/ui/design-system.md` + `ui/man-hinh/*.md` + `ui/tokens/*`.
4. `AGENTS.md` của thư mục con đang làm (`03-app/hub/`, `03-app/web/`, `03-app/kiosk/`) và skill trong `.agents/skills/`.

## Nguồn sự thật — không tự sửa
| Nội dung | File | Ai được sửa |
|---|---|---|
| Đặc tả, DB, UI, hợp đồng API, plan task | `03-app/dac-ta-app.md`, `03-app/db/`, `03-app/ui/`, `03-app/openapi/`, `03-app/plan-codex/` | An (qua session thiết kế). Codex **chỉ đề xuất** trong báo cáo task |
| Code + số liệu nghiên cứu | `02-thuc-nghiem/` (bản rút gọn, **chỉ đọc**) | Không ai trong repo này |
| Code app | `03-app/hub/`, `03-app/web/`, `03-app/kiosk/`, `03-app/tools/` | Codex theo task |
| Kết quả kiểm thử | `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_Txx/` | Codex (log thật) |

Nếu đặc tả và code mâu thuẫn, hoặc task thiếu thông tin: **dừng, ghi câu hỏi vào báo cáo**, không tự đoán thiết kế.

## Luật chung
- Không sửa, không format lại `02-thuc-nghiem/` và `03-app/hub/vendor/` (bản sao có kiểm hash).
- Không ghi số đo/kết quả nào mà không có log hoặc output lệnh đi kèm trong `ket-qua-kiem-thu/`. Không ghi "pass" khi chưa chạy.
- Không seed hay tạo giả sự kiện nhận dạng, ngày công, khuôn mặt (dữ liệu demo chỉ là `03-app/db/seed.sql`).
- Không commit: `*.pt`, `.env`, ảnh khuôn mặt, `HUB_DATA_DIR`, LFW, `node_modules/`, `.venv/` (đã có trong `.gitignore`).
- Checkpoint mô hình **không có trong repo**. Task cần mà chưa có file `02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt` → dừng, báo Hy xin An. Kiểm bằng `python 03-app/tools/kiem-checkpoint.py`.
- Không thêm tính năng ngoài đặc tả (đặc biệt: **không** có trang so sánh mô hình, **không** hiện ảnh khuôn mặt trên Kiosk).

## Môi trường
- Máy dev: **Windows**, Codex chạy chế độ **Local** (PowerShell). Lệnh trong plan viết cho PowerShell; đường dẫn dùng `/` trong code Python/TS.
- Hub: Python 3.11+ (khuyến nghị 3.13), PostgreSQL 16 cài native, dev bằng **CPU**. Bước cần GPU (T02, T13) chạy trên laptop An theo hướng dẫn trong task.
- Web: Node 20+ (pnpm). Kiosk: Expo dev build + **máy ảo Android** (Android Studio), Hub trên cùng máy gọi qua `http://10.0.2.2:8000`.

## Quy trình mỗi task
1. `git pull` trên `main` (làm thẳng trên `main`, không cần nhánh/PR; An không review code).
2. Làm theo các bước trong file task; chạy hết lệnh kiểm trong mục "Tiêu chí nghiệm thu".
3. Viết `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_Txx/bao-cao.md` theo mẫu ở `03-app/plan-codex/README.md` (kèm log).
4. Chỉ khi **mọi** tiêu chí Đạt (số đo/log thật) và `kiem-bi-mat.py` SẠCH: commit nhỏ, thông điệp tiếng Anh `Txx: <what>`, push lên `main`.
4b. Nếu task có bước người khác phải làm (gửi file, chạy trên máy GPU, quay dữ liệu, chạy demo chung): báo cáo phải có mục **"Cần An làm"** gồm một tin nhắn soạn sẵn để Hy copy gửi An (việc gì, file/lệnh chính xác, gửi lại gì). Với T02/T13 phần chạy trên máy An: viết thêm `03-app/ket-qua-kiem-thu/RUN-Txx.md` — lệnh PowerShell copy-dán chạy được, không cần đọc code.
5. Gặp **điều kiện dừng** của task → dừng ngay, ghi báo cáo trạng thái "DỪNG" + lý do, không tự nới tiêu chí.
