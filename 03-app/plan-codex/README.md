# PLAN CODE CHO CODEX — đọc trước khi làm bất kỳ task nào
> Soạn 14/11/2026 bởi session thiết kế (An + Claude). Người chạy: **Hy + Codex** (ChatGPT desktop app, chế độ Local, Windows). Nghiệm thu: **Hy tự nghiệm thu theo tiêu chí** (An không review code). An chỉ tham gia ở các mốc ghi **laptop An** / checkpoint / DỪNG.
> Luật chung: `AGENTS.md` ở gốc repo + `AGENTS.md` của thư mục con + skill trong `.agents/skills/`.

## Cách giao một task cho Codex

### Tiến độ cập nhật 16/11/2026

- T09/T10/T11 đã có triển khai và báo cáo nghiệm thu; T11 push `5b8b7af`, archive `7ac3bdc`.
- T12 đã có các màn cá nhân và kiểm thử web/Hub/PostgreSQL. AC5 ảnh Chrome Android chờ người dùng kiểm tra sau theo phản hồi trong chat; không coi T12 đã nghiệm thu toàn bộ. [Báo cáo](../ket-qua-kiem-thu/2026-11-16_T12/bao-cao.md), [mở và review thủ công](../ket-qua-kiem-thu/2026-11-16_T12/RUN-T12.md).
- T02 chạy trên laptop riêng khi người dùng rảnh; không chặn các task phần mềm theo chỉ đạo đã chốt. T08 còn video toàn luồng và phép đo CPU thiết bị.
- T13/T14 đã có phần mềm tích hợp, script quay/hiệu chỉnh/phê duyệt/benchmark và launcher web+app chung, [kịch bản demo](../kich-ban-demo.md). Backend150pass, web cấu hình2pass; tiền kiểm CPU WS1/3 đã chạy. **Chưa nghiệm thu**: người dùng chưa có 4 nhóm video; chưa L/SPOOF video, chưa20lượt/300khungGPU. Máy hiện chỉ báo Intel UHD/PyTorchCPU, CUDAfalse. Chưa bật chống giả mạo hoặc tự chốt L. Xem [RUN-T13](../ket-qua-kiem-thu/2026-11-16_T13/RUN-T13.md), [RUN-T14](../ket-qua-kiem-thu/2026-11-16_T14/RUN-T14.md).

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
- Commit: <hash>
- Máy chạy: (Windows, CPU/GPU, phiên bản Python/Node/torch/OpenCV — dán output thật)

## Tiêu chí nghiệm thu
| # | Tiêu chí (copy từ task) | Số đo / kết quả thật | Log | Đạt? |

## Đã làm (ngắn)
## File đã tạo / sửa
## Vấn đề gặp + cách xử lý
## Đề xuất cho thiết kế (nếu có — KHÔNG tự sửa đặc tả/db/ui/openapi)
## Cần An làm (nếu có) — tin nhắn soạn sẵn để Hy gửi
## Câu hỏi cho An (chỉ khi DỪNG)
```
Log thật (stdout/stderr, output pytest, ảnh chụp màn) để cùng thư mục.

## Quy ước chung cho mọi task
- Làm thẳng trên `main`; push khi mọi tiêu chí Đạt + `kiem-bi-mat.py` SẠCH. Không chờ duyệt.
- Không chạm vào `02-thuc-nghiem/`, `03-app/hub/vendor/` (sau T01), `03-app/dac-ta-app.md`, `03-app/db/`, `03-app/ui/`, `03-app/openapi/`, `03-app/plan-codex/`.
- Mọi tham số có nhãn **[khởi đầu]** trong đặc tả để trong `company.settings` / cấu hình, không hard-code.
