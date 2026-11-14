# PLAN CODE CHO CODEX — đọc trước khi làm bất kỳ task nào
> Soạn 14/11/2026 bởi session thiết kế (An + Claude). Người chạy: **Hy + Codex** (ChatGPT desktop app, chế độ Local, Windows). Người duyệt: **An**.
> Luật chung: `AGENTS.md` ở gốc repo + `AGENTS.md` của thư mục con + skill trong `.agents/skills/`.

## Cách giao một task cho Codex
Mở Codex ở thư mục gốc repo, dán:
```
Làm task Txx theo file 03-app/plan-codex/Txx-<ten>.md. Đọc AGENTS.md và các file trong mục "Đọc trước" của task.
Chỉ làm đúng phạm vi task, chạy đủ lệnh kiểm trong "Tiêu chí nghiệm thu", viết báo cáo theo mẫu ở 03-app/plan-codex/README.md.
Gặp "Điều kiện dừng" thì dừng và báo cáo, không tự nới tiêu chí.
```

## Thứ tự và phụ thuộc
| Task | Tên | Cần xong trước | Máy | Cần checkpoint |
|---|---|---|---|---|
| T00 | Môi trường dev + skill ngoài + DB | — | Hy | không |
| T01 | Vendor + cổng nạp mô hình | T00 | Hy (CPU) | **có** |
| T02 | Parity trên GPU + bảng ngưỡng | T01 | **laptop An** | có |
| T03 | Khung Hub + DB (Alembic) + auth/RBAC | T00 | Hy | không |
| T04 | Lõi nhận dạng + bộ quyết định | T01, T03 | Hy (CPU) | có |
| T05 | WS Kiosk + ghép thiết bị + đăng ký khuôn mặt | T04 | Hy | có |
| T06 | REST đầy đủ theo openapi + client TS | T03 | Hy | không |
| T07 | Web nền + màn quản trị lõi | T06 | Hy | không |
| T08 | Kiosk App | T05, T06 | Hy + máy ảo Android | có (để quét thật) |
| T09 | Chấm công (backend) | T06 | Hy | không |
| T10 | Chấm công (web) | T07, T09 | Hy | không |
| T11 | Ra vào & giám sát | T05, T07 | Hy | có |
| T12 | Trang nhân viên `/me` | T07, T09 | Hy | không |
| T13 | Chống giả mạo (MiniFASNet) | T04, T08 | Hy + **laptop An** | có |
| T14 | Tích hợp đầu-cuối + đo + kịch bản demo | tất cả | **laptop An** + Hy | có |
| T15 | Tư liệu cho quyển | T14 | Hy | — |
Song song được: T01 ∥ T03 · T07 ∥ T08 · T09 ∥ T11.
Checkpoint (1 file `best.pt` ~132 MB) **không có trong repo** — Hy xin An khi tới T01, đặt đúng đường dẫn, chạy `python 03-app/tools/kiem-checkpoint.py`.

## Mẫu báo cáo task — `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_Txx/bao-cao.md`
```markdown
# Báo cáo Txx — <tên>
- Trạng thái: XONG | DỪNG (lý do) | XONG MỘT PHẦN (phần nào)
- Nhánh / PR: task/Txx-… / #…
- Máy chạy: (Windows, CPU/GPU, phiên bản Python/Node/torch/OpenCV — dán output thật)

## Tiêu chí nghiệm thu
| # | Tiêu chí (copy từ task) | Số đo / kết quả thật | Log | Đạt? |

## Đã làm (ngắn)
## File đã tạo / sửa
## Vấn đề gặp + cách xử lý
## Đề xuất cho thiết kế (nếu có — KHÔNG tự sửa đặc tả/db/ui/openapi)
## Câu hỏi cho An
```
Log thật (stdout/stderr, output pytest, ảnh chụp màn) để cùng thư mục.

## Quy ước chung cho mọi task
- Nhánh `task/Txx-<ten-ngan>`; PR vào `main`; An duyệt (có thể nhờ session thiết kế đối chiếu báo cáo).
- Không chạm vào `02-thuc-nghiem/`, `03-app/hub/vendor/` (sau T01), `03-app/dac-ta-app.md`, `03-app/db/`, `03-app/ui/`, `03-app/openapi/`, `03-app/plan-codex/`.
- Mọi tham số có nhãn **[khởi đầu]** trong đặc tả để trong `company.settings` / cấu hình, không hard-code.
