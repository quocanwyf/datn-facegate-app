# Báo cáo T11 — Ra vào và giám sát

- Trạng thái: **ĐẠT tiêu chí T11 ngày 16/11/2026**.
- Hoàn thành API event/CSV/manual-report/manual-open/handle; broker chỉ phát sau commit, WS xác thực thông điệp đầu, kiểm lại quyền/hạn và lọc company/team tại server. Web W02/W10/W11 dùng chung kết nối, refresh/nối lại, lịch sử không nhân đôi Event/Alert.
- Nghiệm thu ảnh thật dùng kiosk_sim + CPU Hub, gallery đã đăng ký/duyệt tại T08. Không tạo event hay vector giả để đo realtime.

## Bằng chứng và giới hạn

| Tiêu chí | Kết quả / bằng chứng |
|---|---|
| Quét → W10 ≤1 giây sau commit | MATCH 88,95 ms; UNKNOWN 13,44 ms; DENIED_INACTIVE 11,22 ms. [realtime-latency.json](realtime-latency.json), [browser-real.log](browser-real.log). Đây là ba mẫu trên cùng máy, không phải benchmark tải. |
| Quyền SECURITY/company, MANAGER/team | `test_events_api.py`, `test_monitor.py`; JWT thật, kiểm REST/WS, tài khoản khác company không nhận event. |
| IS_EMPLOYEE không tự thêm mẫu | 5 mẫu trước/sau, gallery vẫn 1; test API rollback và luồng browser/Hub thật. |
| CSV tiếng Việt trong Excel | [CSV thật](su-kien.csv), [ảnh Excel](screens/CSV-Excel-UTF8.png). Excel cài trên máy chưa kích hoạt nên không chỉnh được rộng cột; import Unicode UTF-8, phân cách dấu phẩy, tên đầy đủ đọc đúng ở Formula Bar. |
| SUSPENDED | DENY/INACTIVE, door DENY, attendance NONE; event DENIED_INACTIVE. Đã sửa cooldown cũ bị giữ sau đổi trạng thái; regression `test_runtime_status.py` giữ cooldown của người khác/reload thông thường. NV006 được mở lại trong finally. |
| Backend | 141 passed, 2 skipped, 1 warning; [pytest.log](pytest.log). Hai skip cần LFW và ảnh webcam riêng; warning Starlette/httpx có sẵn. |
| Web | Monitor fixture 3 pass; luồng Hub thật 1 pass; attendance regression 4 pass; auth/employees/session 32 pass + 1 fixture cần bổ sung WS, sau sửa session 2/2 pass. Logs riêng giữ cả lần lỗi để đối chiếu. |
| Build | Typecheck, ESLint, production build đạt. Vite báo chunk >500 kB; chưa phải kiểm hiệu năng điện thoại. |

Crop thật chỉ nằm trong kho riêng/Blob có xác thực; ảnh chụp W10 đã che crop, không commit ảnh người hoặc embedding. T08 vẫn còn thiếu video toàn luồng/đo CPU trên thiết bị; T13 chống giả mạo và T14 demo cần thực hiện cùng người dùng theo kế hoạch.

## Kịch bản review

1. Tại `03-app/hub`, chạy `.venv/Scripts/python.exe scripts/start_t11_review.py` (dùng DB/gallery T08 đã có trên máy).
2. Tại `03-app/web`, PowerShell: `$env:FACEGATE_HUB_URL='http://127.0.0.1:8000'`; chạy `& "$env:APPDATA/npm/pnpm.cmd" dev --port 5173` rồi mở `http://127.0.0.1:5173/login`.
3. Đăng nhập tài khoản demo OWNER `nv001@demo.local` / `Demo@123`, chọn quản trị → Giám sát. Quét từ kiosk đã ghép hoặc chạy helper probe bằng thư mục ảnh đã đồng ý ngoài repo. Kiểm dòng sự kiện xuất hiện; người lạ hiện cảnh báo.
4. Xử lý cảnh báo → “Là nhân viên”: thiếu NV phải bị chặn; chọn NV rồi lưu. Vào hồ sơ NV kiểm số mẫu không tăng.
5. Thử mở cửa mô phỏng/chấm hộ: bắt buộc lý do; chấm hộ chỉ có NV ACTIVE/MANUAL khác bản thân và cửa chấm công. Không nhập lùi thời gian.
6. Tra cứu sự kiện → lọc ngày/kết quả/cửa, xuất CSV; tab báo cáo chấm hộ đối chiếu lượt và số NV khác nhau. Link lịch sử từ W09 mang theo NV/ngày.
7. Với HR: có chấm hộ, không xử lý/mở cửa. Với SECURITY `nv020@demo.local`: chỉ danh sách tối thiểu ACTIVE/MANUAL để chấm hộ; URL quản lý nhân viên vẫn bị chặn. MANAGER chỉ đọc event team, không crop/CSV/báo cáo.
8. Tắt Hub: hiện mất kết nối; mở lại: tự nối và nạp REST bù. Có thể chạy lại fixture bằng `pnpm exec playwright test --config playwright.monitor.config.ts`.

## Quyết định phạm vi SECURITY — 16/11/2026

Đã phát hiện W10 cần tìm nhân viên để chấm hộ nhưng GET /employees chỉ có OWNER/HR/MANAGER. Đề xuất được người dùng trả lời trực tiếp: **“Cho SECURITY tìm riêng NV MANUAL, chỉ trả thông tin cần để chấm hộ (đề xuất).”**

Áp dụng Q-014: bổ sung SECURITY cho GET danh sách, ép ACTIVE/MANUAL và chỉ trả id/mã/tên/phòng ban/trạng thái/phương thức. Không bổ sung SECURITY vào GET chi tiết hoặc các API ghi nhân viên. Tài khoản có thêm OWNER/HR/MANAGER vẫn có quyền riêng của vai trò đó. Sẽ cập nhật nguồn OpenAPI/spec liên quan và kiểm quyền tại server; không cần đổi DB.
