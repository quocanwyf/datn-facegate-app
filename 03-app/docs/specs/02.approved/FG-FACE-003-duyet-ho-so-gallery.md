# FG-FACE-003 — Duyệt hồ sơ và cập nhật gallery

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-006 của người dùng, giữ các quyết định đã chốt trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §4.6, §5.2, §6; admin.md W-08; DB §4.2. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-08; W-04 xem mẫu.
- Task liên quan: T04, T05, T07 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-FACE-002](FG-FACE-002-thu-mau-dang-ky.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Duyệt hồ sơ và cập nhật gallery trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: face_profile/sample/embedding/template, employee, audit_log.
- Đầu vào nghiệp vụ: profile_id; ghi chú theo approve/reject schema.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tải hàng chờ và 5 ảnh mẫu
2. Xem cảnh báo trùng và điểm
3. Xác nhận hoặc từ chối
4. Duyệt đăng ký lại thay hồ sơ cũ/xóa mẫu cũ
5. Cập nhật gallery trước khi trả thành công

## 5. Quy tắc nghiệp vụ và bất biến

- Duyệt trùng bắt buộc lý do
- Tối đa1 ACTIVE và 1 PENDING/employee theo DB
- Dữ liệu định danh: NV FACE có consent hiệu lực, profile ACTIVE và template đúng model. Theo Q-002, phải nhận ra cả ACTIVE và SUSPENDED; SUSPENDED chỉ dùng để trả DENY/INACTIVE, không được phép qua cửa/tính công.
- Gallery định danh đã đồng bộ tại đặc tả §4.6: ACTIVE/SUSPENDED đủ điều kiện; chỉ ACTIVE được xét cho qua cửa, SUSPENDED chỉ để từ chối. TERMINATED hoặc đã xóa sinh trắc/rút consent không được đưa lại vào dữ liệu định danh.
- Không log đọc ảnh trong demo
- Ảnh mẫu chỉ OWNER/HR

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /face-profiles` | `getFaceProfiles` | OWNER, HR | `FaceProfileStatus`, `PageFaceProfile` | 200, 400, 401, 403 |
| `GET /face-profiles/{id}` | `getFaceProfilesById` | OWNER, HR | `FaceProfile` | 200, 401, 403, 404 |
| `POST /face-profiles/{id}/approve` | `postFaceProfilesApprove` | OWNER, HR | `ReviewInput`, `FaceProfile` | 200, 400, 401, 403, 404, 422, 409, 503 |
| `POST /face-profiles/{id}/reject` | `postFaceProfilesReject` | OWNER, HR | `ReviewInput`, `FaceProfile` | 200, 400, 401, 403, 404, 422, 409, 503 |
| `GET /face-samples/{id}/image` | `getFaceSamplesImage` | OWNER, HR |  | 200, 401, 403, 404 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Thiếu lý do trùng không thành công
- Hồ sơ không tồn tại/trạng thái sai theo contract
- Theo Q-006, chỉ một người xử lý hồ sơ khi duyệt đồng thời; người còn lại nhận “Hồ sơ đã được xử lý”.
- Không cập nhật được gallery thì tạm ngưng nhận dạng đến khi phục hồi; không báo duyệt thành công khi còn bước bắt buộc chưa hoàn tất.

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-FACE-003-AC01**: Duyệt ACTIVE dùng ngay sau API thành công.
- **FG-FACE-003-AC02**: Trùng thiếu lý do bị chặn.
- **FG-FACE-003-AC03**: MANAGER/SECURITY không đọc ảnh mẫu.
- **FG-FACE-003-AC04**: Thay bản cũ chỉ sau duyệt mới.
- **FG-FACE-003-AC05**: Gallery cập nhật khi dữ liệu liên quan thay đổi.

- **FG-FACE-003-AC06**: Nhân viên SUSPENDED có hồ sơ hợp lệ được định danh để từ chối; TERMINATED hoặc đã rút/xóa sinh trắc không được giữ lại để nhận dạng.

- **FG-FACE-003-AC07**: Duyệt đồng thời cùng hồ sơ chỉ một lần có hiệu lực; người còn lại được báo hồ sơ đã xử lý.
- **FG-FACE-003-AC08**: Lỗi cập nhật gallery không trả thành công sớm và khiến nhận dạng tạm ngưng đến khi phục hồi.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
