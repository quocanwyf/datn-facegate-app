# BÀN GIAO CHO HY — đọc đầu tiên
> An + Claude đã làm xong phần **thiết kế, đặc tả và plan**. Hy + Codex **code theo plan**. An duyệt mọi thay đổi.
> Ngày bàn giao: 14/11/2026.

## 1. Repo có gì
| Thư mục / file | Nội dung | Ai sửa |
|---|---|---|
| `AGENTS.md`, `.agents/skills/` | Luật cho Codex + 4 skill riêng (skill ngoài Codex cài ở T00) | An |
| `03-app/KE-HOACH-TONG.md` | Kế hoạch tổng, vai trò, trạng thái | An |
| `03-app/dac-ta-app.md` | **Đặc tả** (v1.4.2; §0a = phạm vi bản demo) | An |
| `03-app/db/` | Thiết kế DB, `schema.sql`, `seed.sql`, `test_constraints.sql`, ERD | An |
| `03-app/ui/` | Design system, token màu/chữ, layout từng màn (`man-hinh/`) | An |
| `03-app/openapi/` | Hợp đồng API (`openapi.yaml`) + giao thức WebSocket | An |
| `03-app/plan-codex/` | **16 task T00–T15** cho Codex + mẫu báo cáo | An |
| `03-app/hub/`, `web/`, `kiosk/` | Code (hiện chỉ có `AGENTS.md`) | **Hy + Codex** |
| `03-app/tools/` | `kiem-checkpoint.py`, `kiem-bi-mat.py`, `dong-goi-repo.py` | — |
| `03-app/ket-qua-kiem-thu/` | Báo cáo + log mỗi task | Hy + Codex |
| `02-thuc-nghiem/` | Bản rút gọn code + log nghiên cứu (**chỉ đọc**) — xem `BAN-RUT-GON.md` | không ai |
| `03-app/review/`, `xu-ly-review.md`, `so-do/`, `de-xuat-tong-the.md`, `thiet-ke-gd3.md` | Lịch sử thiết kế, review | đọc tham khảo |

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
1. Codex tạo nhánh `task/Txx-…`, code, chạy kiểm, viết `03-app/ket-qua-kiem-thu/<ngày>_Txx/bao-cao.md`.
2. Hy xem nhanh, chạy lại lệnh kiểm nếu cần, mở **Pull Request** vào `main`.
3. Nhắn An link PR. An duyệt (đối chiếu báo cáo với tiêu chí) → merge → task tiếp.
4. Codex báo **DỪNG** → không tự sửa đặc tả/tiêu chí; gửi báo cáo cho An.

## 5. Việc cần laptop An (có GPU)
- **T02** (parity GPU), **T13** (hiệu chỉnh chống giả mạo), **T14** (demo). Hy viết script ở máy mình, An chạy trên laptop của An theo hướng dẫn trong task, gửi lại log.

## 6. Trước mỗi lần push
`python 03-app/tools/kiem-bi-mat.py` → phải **SẠCH** (repo public: không `.env`, không `*.pt`, không ảnh khuôn mặt, không LFW).

## 7. Tài khoản demo (sau khi nạp `seed.sql`)
`nv001@demo.local` … `nv024@demo.local`, mật khẩu `Demo@123`. NV001 = Chủ DN, NV002 = HR (PIN Kiosk `2468`), NV005 = Quản lý Kỹ thuật, NV013 = Quản lý Kinh doanh, NV020/NV021 = Bảo vệ. NV019 tạm khoá, NV022 chấm công hộ. **Chỉ dùng cho demo.**
