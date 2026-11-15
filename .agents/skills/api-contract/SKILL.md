---
name: api-contract
description: Quy ước hợp đồng API giữa Hub, Web và Kiosk — dùng khi thêm/sửa endpoint, sinh client TypeScript, xử lý lỗi hoặc phân trang. 03-app/openapi/openapi.yaml là nguồn gốc duy nhất. Không dùng cho logic AI bên trong Hub.
---

# api-contract

1. **Nguồn gốc:** `03-app/openapi/openapi.yaml` (OpenAPI 3.1) + `03-app/openapi/ws-protocol.md`. Không tự thêm/đổi endpoint, trường, mã lỗi. Cần đổi → ghi đề xuất trong báo cáo task (An duyệt rồi mới sửa yaml).
2. **Hub** cài đúng path (tiền tố `/api/v1`), method, schema, mã HTTP, `operationId`. Test hợp đồng: `hub/tests/test_openapi_contract.py` so `app.openapi()` với file yaml — mọi path+method trong yaml phải có trong app; schema phản hồi của test mẫu phải validate được.
3. **Client:** Web và Kiosk sinh type bằng `openapi-typescript ../openapi/openapi.yaml -o src/api/schema.d.ts`, gọi bằng `openapi-fetch`. **Không viết type API bằng tay**, không sửa file sinh ra.
4. **Lỗi:** luôn `{"error":{"code","message","details?"}}`; `code` dạng UPPER_SNAKE (vd. `PAIRING_EXPIRED`, `ASSIGNMENT_OVERLAP`, `SELF_REVIEW_FORBIDDEN`); `message` tiếng Việt hiển thị được. Client hiển thị `message`, rẽ nhánh theo `code`.
5. **Phân trang:** `page` từ 1, `size` ≤ 100 → `{items,total,page,size}`.
6. **Thời gian:** ISO-8601 có offset; ngày `YYYY-MM-DD`; giờ ca `HH:mm`.
7. **Quyền:** `x-roles` trong yaml là danh sách vai trò được gọi; server vẫn kiểm phạm vi phòng ban (MANAGER) và các luật "không tự duyệt / không tự sửa / không tự chấm hộ".
8. Lint sau khi sửa yaml: `npx @redocly/cli lint 03-app/openapi/openapi.yaml` (0 lỗi).

## Quyền và trạng thái sau đồng bộ 14/11/2026
- HR PATCH gate chỉ default_policy, PUT allowed-departments được phép; trường khác 403. OWNER giữ tạo/sửa cửa/thiết bị. HR GET settings được, PUT chỉ OWNER. MANAGER export chỉ team.
- WAITING_IN bổ sung AttendanceStatus, đồng bộ CHECK DB và status.json.
- Q-006: 409 PROFILE_ALREADY_REVIEWED; 503 BIOMETRIC_DELETE_INCOMPLETE/RECOGNITION_UNAVAILABLE khi thao tác chưa xong; không báo thành công sớm hoặc mở quyền bằng client.
- RecognitionSettings: L [0,1], true cần L không NULL và đã chốt T13; W nguyên dương, ngưỡng đếm 1..W (kiểm quan hệ tại server), cấu hình lỗi giữ toàn bộ cũ.
