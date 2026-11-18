# BÀN GIAO CHO HY — đọc đầu tiên
> An + Claude đã làm xong phần **thiết kế, đặc tả và plan**. Hy + Codex **code theo plan và tự chịu trách nhiệm nghiệm thu**. An **không review code, không duyệt PR** — chỉ làm đúng các việc ở mục 5.
> Ngày bàn giao: 14/11/2026.

## 1. Repo có gì
| Thư mục / file | Nội dung | Ai sửa |
|---|---|---|
| `AGENTS.md`, `.agents/skills/` | Luật cho Codex + 4 skill riêng (skill ngoài Codex cài ở T00) | An |
| `03-app/KE-HOACH-TONG.md` | Kế hoạch tổng, vai trò, trạng thái | An |
| `03-app/dac-ta-app.md` | **Đặc tả** (xem phiên bản ở đầu file; §0a = phạm vi bản demo) | An |
| `03-app/db/` | Thiết kế DB, `schema.sql`, `seed.sql`, `test_constraints.sql`, ERD | An |
| `03-app/ui/` | Design system, token màu/chữ, layout từng màn (`man-hinh/`) | An |
| `03-app/openapi/` | Hợp đồng API (`openapi.yaml`) + giao thức WebSocket | An |
| `03-app/plan-codex/` | **16 task T00–T15** cho Codex + mẫu báo cáo | An |
| `03-app/hub/`, `web/`, `kiosk/` | Mã nguồn Hub, web và kiosk | **Hy + Codex** |
| `03-app/tools/` | `kiem-checkpoint.py`, `kiem-bi-mat.py`, `dong-goi-repo.py` | — |
| `03-app/ket-qua-kiem-thu/` | Báo cáo + log mỗi task | Hy + Codex |
| `02-thuc-nghiem/` | Bản rút gọn code + log nghiên cứu (**chỉ đọc**) — xem `BAN-RUT-GON.md` | không ai |
| `03-app/docs/lich-su-thiet-ke/`, `03-app/so-do/` | Lịch sử thiết kế, review | đọc tham khảo |

## 2. Checkpoint (file mô hình)
- **Không có trong repo** (GitHub chặn file > 100 MB và mô hình không công khai).
- Cần từ **T01**. Nhắn An xin file `best.pt` (~132 MB, Google Drive / Zalo), đặt đúng vào:
  `02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt`
- Kiểm: `python 03-app/tools/kiem-checkpoint.py` → phải in **OK** (SHA-256 `120489621a…ef88`).
- Không cần file `.env` từ An: tự tạo từ `.env.example` (T00 hướng dẫn).

## 3. Bắt đầu (lần đầu)
1. `git clone <link repo>` vào một thư mục **không có dấu tiếng Việt và khoảng trắng**, vd. `D:\code\datn-facegate-app`.
2. Mở **ChatGPT desktop app → Codex**, thêm project = thư mục repo, chọn chế độ **Local** (Codex chạy lệnh bằng PowerShell trên máy Hy).
3. Giao task **T00** (cách dán lệnh ở `03-app/plan-codex/README.md`). T00 cài môi trường, PostgreSQL, máy ảo Android, skill ngoài.
4. Làm lần lượt theo bảng thứ tự trong `03-app/plan-codex/README.md`.

## 4. Mỗi task
1. `git pull` → giao task cho Codex → Codex code, chạy **mọi** lệnh kiểm trong "Tiêu chí nghiệm thu", viết `03-app/ket-qua-kiem-thu/<ngày>_Txx/bao-cao.md`.
2. Hy tự nghiệm thu: mọi tiêu chí **Đạt** (có số đo/log thật) → `kiem-bi-mat.py` SẠCH → commit + push thẳng lên `main` → làm task tiếp. Không cần chờ ai.
3. Chưa đạt → bảo Codex sửa tới khi đạt. Codex báo **DỪNG** (lỗi thiết kế, đặc tả mâu thuẫn) → mới nhắn An, kèm báo cáo.
4. Nếu báo cáo có mục **"Cần An làm"** → copy nguyên tin nhắn trong mục đó gửi An.

## 5. Những lúc DUY NHẤT cần An
| Khi | Hy nhắn An | An làm |
|---|---|---|
| Bắt đầu T01 | "Gửi mình `best.pt`" | Gửi file qua Drive/Zalo |
| T02 xong phần script | "Pull repo, chạy lệnh T02 theo `RUN-T02.md`" | Chạy trên laptop GPU, gửi lại thư mục log (nếu laptop Hy có GPU NVIDIA thì Hy tự chạy, An chỉ gửi thêm LFW + 24 backbone) |
| T13 cần dữ liệu thử | "Cần người tình nguyện quay mặt thật / ảnh in / màn hình / video" | Tổ chức quay, chạy script hiệu chỉnh, chọn ngưỡng L |
| T14 | "Hẹn ngày chạy demo chung Wi-Fi" | Cài Hub trên laptop mình, chạy demo cùng Hy |
| Codex báo DỪNG vì thiết kế | Gửi báo cáo | Trả lời / sửa thiết kế |
Ngoài các lúc này, Hy tự làm.

## 6. Trước mỗi lần push
`python 03-app/tools/kiem-bi-mat.py` → phải **SẠCH** (repo public: không `.env`, không `*.pt`, không ảnh khuôn mặt, không LFW).

## 7. Tài khoản demo (sau khi nạp `seed.sql`)
`nv001@demo.local` … `nv024@demo.local`, mật khẩu `Demo@123`. NV001 = Chủ DN, NV002 = HR (PIN Kiosk `2468`), NV005 = Quản lý Kỹ thuật, NV013 = Quản lý Kinh doanh, NV020/NV021 = Bảo vệ. NV019 tạm khoá, NV022 chấm công hộ. **Chỉ dùng cho demo.**
