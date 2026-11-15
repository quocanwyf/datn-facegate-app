# T08 — Kiosk App (Expo, máy ảo Android)
> Phụ thuộc: T05, T06 · Máy: máy Hy + máy ảo Android · Cần checkpoint: có (để quét thật)
> Luật chung: `AGENTS.md` + `03-app/plan-codex/README.md`. Báo cáo: `03-app/ket-qua-kiem-thu/<YYYY-MM-DD>_T08/bao-cao.md`.

## Mục tiêu
Kiosk App chạy trên máy ảo: ghép, quét, hiện kết quả, đăng ký khuôn mặt, mất kết nối — đúng `ui/man-hinh/kiosk.md`.

## Đọc trước
`03-app/kiosk/AGENTS.md` · `ui/design-system.md` · `ui/man-hinh/kiosk.md` · `ui/tokens/kiosk-theme.json`, `status.json` · `openapi/ws-protocol.md` · skill `kiosk-ws-protocol`, bộ Expo, `vercel-react-native-skills`, animations Software Mansion.

## Được ghi vào
`03-app/kiosk/` · `03-app/ket-qua-kiem-thu/<ngày>_T08/`.

## Các bước
1. Expo dev build, TS strict; cấu hình cleartext HTTP (bản demo); quyền camera; font Inter; theme.
2. `ws/KioskSocket.ts`: auth, dừng-và-chờ, BUSY, ping, nối lại lùi dần, xử lý mã lỗi.
3. Camera (vision-camera): camera trước, lấy khung → JPEG cạnh dài 640, q80; đọc QR ở K-01.
4. Màn K-01, K-02, K-04, K-05, K-06, K-07, K-08, K-09, K-11 + component trong design-system §6.2; animation Reanimated §7; âm thanh §8 (ghi nguồn).
5. Test đơn vị cho `KioskSocket` (mock WS): không bao giờ gửi khung khi chưa nhận phản hồi; không gửi khi đang hiện kết quả.
6. Quay video màn hình máy ảo: ghép → đăng ký 5 mẫu → (duyệt trên web) → quét ra OK → người khác ra DENY → tắt Hub → K-11 → bật lại.

## Tiêu chí nghiệm thu
| # | Tiêu chí |
|---|---|
| 1 | `tsc --noEmit` sạch; test `KioskSocket` pass |
| 2 | Video luồng đầy đủ (bước 6) trong thư mục kết quả |
| 3 | Đo thời gian từ lúc đứng vào khung tới màn kết quả trên máy Hy (CPU) cho 10 lượt — ghi số thật (mục tiêu < 2 s là mục tiêu cho laptop GPU, ở đây chỉ ghi nhận) |
| 4 | Không màn nào hiện ảnh khuôn mặt (kiểm bằng rà code + video) |

## Bổ sung nghiệm thu theo Q-001–Q-013 (14/11/2026)
Test disconnect3s, im lặng15s không cộng3s; retry1/2/4/8/15s; NO_GALLERY/máy chủ chưa sẵn sàng, hủy enroll giữ bản cũ. Nhãn/status theo token mới.
