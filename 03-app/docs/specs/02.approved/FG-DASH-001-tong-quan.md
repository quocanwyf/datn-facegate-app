# FG-DASH-001 — Tổng quan hôm nay và điều hướng quản trị

- Phiên bản: 1.1 — 14/11/2026; cập nhật theo quyết định Q-012 của người dùng.
- Trạng thái: **APPROVED — đã review và được người dùng duyệt**.
- Người review: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Người approved: người dùng giao việc trong chat này; xác nhận ngày 14/11/2026 (Asia/Bangkok).
- Căn cứ duyệt: [lịch sử duyệt](../LICH-SU-DUYET.md#approved-2026-11-14), áp dụng toàn bộ specs trong draft.
- Đồng bộ nguồn: hoàn tất theo Q-001–Q-013 ngày 14/11/2026; đặc tả v1.4.4, OpenAPI v1.1.0 và các nguồn liên quan. Xem CAN-CHOT và lịch sử duyệt.
- Hoàn thành/nghiệm thu: chưa xác nhận, chưa có bằng chứng.
- Nguồn: [đặc tả v1.4.4](../../../dac-ta-app.md) §9.3; admin.md W-02/khung chung. Xem [quy tắc chung](../QUY-UOC-CHUNG.md) và các tài liệu gốc được liên kết ở đó.
- Màn hình/luồng: W-02; shell /admin.
- Task liên quan: T06, T07, T11 (không thay phạm vi/điều kiện dừng của task gốc).
- Liên quan/phụ thuộc: [FG-MON-001](../03.archived/FG-MON-001-giam-sat-canh-bao.md)
- Quyết định / đồng bộ nguồn: các mục Q liên quan đã chốt và đồng bộ; không còn chờ sửa nguồn cho 13 quyết định này — [sổ quyết định](../CAN-CHOT.md).

## 1. Mục tiêu và phạm vi

Tổng quan hôm nay và điều hướng quản trị trong bản demo. Cung cấp hành vi, kết quả và giới hạn dưới đây; không đưa lại các chức năng đã bỏ ở §0a.

## 2. Tác nhân, quyền và điều kiện trước

OWNER/HR xem tổng quan; shell theo vai trò. Quyền REST cụ thể trong mục 6; server kiểm thêm phạm vi công ty/phòng ban/bản thân. Nếu quyền nghiệp vụ khác x-roles, giữ nguyên nguồn và chờ chốt, không tự mở quyền.

Hub/DB và dữ liệu tham chiếu phải sẵn sàng. Tài khoản/thiết bị được xác thực khi operation yêu cầu. Các luồng AI cần model đã qua cổng kiểm; đăng ký cần phiên còn hạn và consent. Các điều kiện này áp dụng theo luồng, không biến endpoint public thành yêu cầu đăng nhập.

## 3. Dữ liệu, đầu vào và đầu ra

- Thực thể liên quan: Dashboard response, Event, counters, device_status.
- Đầu vào nghiệp vụ: Ngày công ty; monitor WS.
- Đầu ra: dữ liệu/trạng thái ở luồng chính; các operation REST dùng đúng response schema ở mục 6. Chỉ đọc không sinh thay đổi nghiệp vụ.
- Tên trường, required, kiểu, enum, min/max theo OpenAPI và constraints DB. Liệt kê nghiệp vụ ở đây không thay thế DTO.
- API thời gian ISO-8601 có offset, ngày YYYY-MM-DD; tính theo múi giờ công ty, UI dd/MM/yyyy và HH:mm.

## 4. Luồng chính

1. Tải dashboard và 10 event mới nhất qua `GET /api/v1/events?page=1&size=10`, thứ tự mới nhất trước.
2. Hiện4 KPI
3. Hiện số hồ sơ/giải trình/cảnh báo/thiết bị offline
4. WS cập nhật và mở màn đích

## 5. Quy tắc nghiệp vụ và bất biến

- 4 KPI Có mặt/Đi muộn/Chưa đến/Lượt người lạ, theo định nghĩa Q-012 dưới đây.
- OWNER/HR mặc địnhW-02, SECURITY W-10, MANAGER W-09team
- Menu ẩn theo quyền nhưng API kiểm riêng
- Không thêm dashboard biểu đồ nghiên cứu
- Dùng page=1 và size=10, không query limit ngoài hợp đồng.

### Định nghĩa chỉ số theo Q-012

| Chỉ số | Cách tính |
|---|---|
| Có mặt | Số nhân viên có giờ vào ca hôm nay |
| Đi muộn | Trong nhóm có mặt, giờ vào > giờ bắt đầu ca + grace_in |
| Chưa đến | Đã tới giờ ca nhưng chưa có giờ vào |
| Lượt người lạ | Số sự kiện UNKNOWN xảy ra hôm nay, không gồm SPOOF |

Ba chỉ số nhân viên chỉ xét ACTIVE có ca hôm nay, loại HOLIDAY/LEAVE/OFF; đếm mỗi nhân viên một lần trên giờ công hiệu lực theo Q-009/Q-010. Đi muộn là tập con của Có mặt. Có mặt nghĩa là đã ghi nhận vào ca; các lượt quét lặp không làm tăng số người.

Ngày theo timezone company. UNKNOWN đếm lượt event theo occurred_at trong ngày, không suy luận danh tính để đếm người riêng biệt. Bộ đếm trong ngày là tạm thời: tính Đi muộn từ giờ vào/grace không thay trạng thái IN_PROGRESS thành LATE trước chốt.

Đồng bộ nhãn W-02 và định nghĩa tổng hợp trong nguồn chuẩn; không tạo endpoint hoặc thêm trường counters WS mới trong bước ghi nhận này.

## 6. REST / tích hợp

| Method / path (thêm `/api/v1`) | operationId | x-roles hiện tại | Schema $ref trực tiếp | HTTP khai báo |
|---|---|---|---|---|
| `GET /dashboard/today` | `getDashboardToday` | OWNER, HR | `Dashboard` | 200, 400, 401, 403 |

Schema trong bảng là mọi $ref trực tiếp của operation (có thể gồm tham số, request, response), không phải chỉ response. Tra required/fields/alias tại [OpenAPI](../../../openapi/openapi.yaml); xem [ma trận API](../MA-TRAN-API.md). WebSocket theo [giao thức gốc](../../../openapi/ws-protocol.md).

## 7. Nhánh lỗi và trạng thái UI

- 403 hiện thông báo không quyền
- KPI tạm thời không coi là kết luận đã chốt
- Mất WS báo đang nối lại

Hiển thị đang tải, rỗng, lỗi và không có quyền theo màn hình gốc. Message lỗi tiếng Việt, rẽ nhánh theo code hợp đồng. Không tự thêm mã lỗi. Các gợi ý chống gửi lặp trong quy tắc chung là đề xuất UX, không thay đổi API.

## 8. Tiêu chí nghiệm thu dự kiến

- **FG-DASH-001-AC01**: Đủ 4 KPI và 10 event mới nhất.
- **FG-DASH-001-AC02**: Số chờ mở W-08/W-12/W-10.
- **FG-DASH-001-AC03**: Vai trò vào đúng mặc định.
- **FG-DASH-001-AC04**: Không menu ngoài quyền.
- **FG-DASH-001-AC05**: KPI theo định nghĩa đã chốt.

- **FG-DASH-001-AC06**: Có mặt/Đi muộn/Chưa đến chỉ đếm ACTIVE có ca, loại lễ/LEAVE/không ca; quét lặp không tăng số người.
- **FG-DASH-001-AC07**: Đi muộn là tập con Có mặt dựa giờ vào vượt grace; trước chốt vẫn giữ nhãn công tạm thời theo Q-008.
- **FG-DASH-001-AC08**: Lượt người lạ đếm event UNKNOWN đúng ngày timezone company, không gồm SPOOF và không khẳng định là số người riêng biệt.
- **FG-DASH-001-AC09**: 10 event mới nhất lấy page=1/size=10, không gửi query limit ngoài contract.

Các AC **chưa chạy/chưa đánh dấu đạt**. Khi triển khai dùng bộ kiểm task gốc và lưu log thật trong `03-app/ket-qua-kiem-thu/`. Không seed giả sự kiện nhận dạng, khuôn mặt hoặc ngày công.
