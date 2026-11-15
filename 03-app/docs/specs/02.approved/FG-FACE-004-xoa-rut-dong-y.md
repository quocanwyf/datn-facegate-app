# FG-FACE-004 — Xóa sinh trắc và rút đồng ý

- Phiên bản: 1.2 — 14/11/2026; bổ sung quyết định Q-006 của người dùng, giữ các quyết định đã chốt trước đó.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §0a, §5.9; DB §5; me.md E-08. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-04, E-08; W-03 nghỉ việc.
- Task liên quan: T05, T06, T07, T12 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-FACE-003](FG-FACE-003-duyet-ho-so-gallery.md), [FG-EMP-001](FG-EMP-001-nhan-vien.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Xóa sinh trắc và rút đồng ý trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR xóa cho NV; EMPLOYEE rút của mình. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: employee, face_profile/sample/embedding/template; snapshot_path, event_handling, audit_log.
- Đầu vào nghiệp vụ: employee_id quản trị hoặc danh tính token /me.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Hiện trạng thái/tác động và xác nhận theo UI
2. Xóa profile/mẫu/file/embedding/template
3. Xóa crop liên kết NV và NULL snapshot_path
4. Ghi biometric_deleted_at/audit, cập nhật gallery
5. Rút đồng ý, từ chối agree=false hoặc xóa hành chính: đặt face_consent_at/by cùng NULL và attendance_method=MANUAL.

## 5. Quy tắc nghiệp vụ và bất biến

- TERMINATED tự xóa sinh trắc
- Giữ bảng công và event gốc
- Không retention job hoặc xác nhận2 bước trong demo
- Không hiện ảnh ở /me
- Theo Q-005, từ chối/rút đồng ý và OWNER/HR xóa hành chính đều xóa sinh trắc ACTIVE/PENDING, đặt face_consent_at và face_consent_by cùng NULL, chuyển MANUAL.
- Muốn dùng mặt lại sau xóa cần đồng ý và đăng ký lại; không tự khôi phục mẫu/vector cũ.
- Hủy chụp khác với từ chối consent: quy tắc giữ bản chờ Q-004 không áp dụng để giữ dữ liệu khi người dùng đã từ chối/rút hoặc yêu cầu xóa.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /me/face` | `getMeFace` | EMPLOYEE | `MeFace` | 200, 401, 403 |
| `POST /me/face/revoke` | `postMeFaceRevoke` | EMPLOYEE | `MeFace` | 200, 401, 403, 503 |
| `DELETE /employees/{id}/face` | `deleteEmployeesFace` | OWNER, HR |  | 204, 401, 403, 404, 503 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- Không có hồ sơ theo hành vi contract
- Theo Q-006, rút/xóa phải ngừng dùng khuôn mặt để nhận dạng; nếu xóa file lỗi thì báo chưa hoàn tất và cho thử lại, không khôi phục nhận dạng trong lúc chờ dọn xong.
- Gallery không cập nhật được thì tạm ngưng nhận dạng đến khi phục hồi; chỉ báo thành công khi mọi bước bắt buộc hoàn tất. Không khẳng định file/DB là một giao dịch nguyên tử.
- Không xóa người khác bằng /me

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-FACE-004-AC01**: Không còn mẫu/vector/crop liên kết sau xóa.
- **FG-FACE-004-AC02**: Event giữ nguyên ngoài đường dẫn NULL.
- **FG-FACE-004-AC03**: Rút đồng ý chuyển MANUAL và loại gallery trước thành công.
- **FG-FACE-004-AC04**: Công lịch sử còn nguyên.
- **FG-FACE-004-AC05**: Chỉ đúng chủ thể/vai trò được thao tác.

- **FG-FACE-004-AC06**: OWNER/HR xóa hành chính hoặc nhân viên rút/từ chối đều đặt hai cột consent NULL và chuyển MANUAL, xóa ACTIVE/PENDING và sinh trắc liên quan.
- **FG-FACE-004-AC07**: Sau xóa không nhận dạng được bằng dữ liệu cũ; dùng mặt lại cần consent mới và hồ sơ đăng ký được duyệt, trong khi lịch sử công/event vẫn giữ.

- **FG-FACE-004-AC08**: Xóa file thất bại được báo chưa hoàn tất và có thể thử lại; người đã rút/xóa không tiếp tục được nhận dạng.
- **FG-FACE-004-AC09**: Thử lại hoàn tất xóa không làm mất công/event gốc hoặc khôi phục dữ liệu nhận dạng đã rút.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
