# Kịch bản test web FaceGate

Chuẩn bị ngày **16/11/2026**. Mở **http://127.0.0.1:5173/login**. Web → Hub port 8012 → PostgreSQL đã kiểm kết nối. Đây là **bản sao review mới từ T08**; phiên review T12 cũ và dữ liệu T08 gốc được giữ lại. Chưa nối app đang chạy sang Hub review này.

Kiểm trước khi bàn giao: Hub `ok`, DB `true`, model đã xác minh, gallery **1 hồ sơ thật được duyệt / 5 mẫu của NV006**. Các lượt qua cửa đã có được sao chép nguyên từ T08, không tạo thêm lượt giả. Chi tiết đọc thực tế trong [preflight.json](ket-qua-kiem-thu/2026-11-16_WEB-REVIEW/preflight.json).

## Tài khoản

Mật khẩu chung cho **các tài khoản demo dưới đây**: `Demo@123`.

| Vai trò | Email | Nhân viên / phạm vi |
|---|---|---|
| Nhân viên | nv006@demo.local | Võ Thanh Tùng · Kỹ thuật |
| Quản lý | nv005@demo.local | Đỗ Quang Huy · quản lý Kỹ thuật |
| HR | nv002@demo.local | Nguyễn Thị Thu Hà |
| Bảo vệ | nv020@demo.local | Kiều Thị Mai |
| OWNER | nv001@demo.local | Trần Minh Khoa |

Người có vai trò quản trị được chọn **Trang quản trị / Trang cá nhân** sau đăng nhập. Đăng xuất qua avatar/menu tài khoản. Refresh trang yêu cầu đăng nhập lại vì phiên lưu trong bộ nhớ; đây là hành vi hiện tại.

Làm lần lượt 01 → 12, phần xóa khuôn mặt làm cuối. Mỗi mục đánh dấu **Đạt / Lỗi / Chưa thử**; không đánh dấu đạt những luồng cần kiosk khi chưa chạy kiosk.

## 01 — Đăng nhập và trang hôm nay

1. Để trống hai ô rồi bấm Đăng nhập: phải nhắc nhập email/mật khẩu.
2. Nhập `nv006@demo.local` với mật khẩu sai: báo sai thông tin, vẫn cho nhập lại.
3. Đăng nhập đúng bằng tài khoản NV006: vào `/me`, chào **Võ Thanh Tùng**.
4. Kiểm ca Hành chính 08:30–17:30, ngày hiện tại, giờ vào/ra và trạng thái. Trước khi chốt, chưa vào phải là “Chưa đến — tạm thời”, không kết luận vắng sớm.
5. Có các lượt cũ ở cửa **T08 review**; cửa ACCESS_ONLY có ghi **Không tính công**. Vì thế có lượt nhận diện ở đây nhưng giờ vào/ra vẫn trống là đúng.
6. Bấm làm mới: dữ liệu tải lại, không sinh thêm lượt qua cửa.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 02 — Bảng công và chi tiết ngày

1. Vào **Bảng công**, chọn tháng **11/2026**, thử hai nút chuyển tháng rồi quay lại.
2. Mở chú giải trạng thái, kiểm bốn ô thống kê.
3. Chạm ngày **13/11/2026**: mở đúng ngày đó, có ca/giờ/trạng thái/nguồn/phút và danh sách sự kiện hoặc trạng thái rỗng.
4. Nếu chưa có giải trình pending, có nút **Gửi giải trình**. Nếu đã có pending, hiện trạng thái chờ thay cho nút gửi mới.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 03 — Nhân viên gửi giải trình

Vẫn dùng NV006. Ngày thử **13/11/2026** là ngày đã qua, tránh dùng giờ ra trong tương lai.

1. Mở chi tiết ngày 13/11 → **Gửi giải trình**.
2. Chọn **Quên chấm vào**, để trống giờ/lý do rồi gửi: phải nhắc nhập, chưa tạo yêu cầu.
3. Đổi sang **Đi công tác** (BUSINESS_TRIP), nhập giờ vào **08:41**, giờ ra **17:30**.
4. Nhập lý do: `TEST-WEB-01: đi công tác, đề nghị bổ sung giờ` rồi gửi.
5. Kết quả: về **Giải trình của tôi**, có bản **Chờ duyệt** đúng ngày/loại/giờ/lý do.
6. Quay lại chi tiết ngày: pending phải ẩn nút gửi mới. Nếu đi qua **Gửi mới** và cố gửi cùng ngày, server phải báo đã có yêu cầu đang chờ; form giữ nội dung.

Nếu ngày này đã có pending từ lần test trước, tiếp tục với bản đó hoặc hủy nó trước; không cần sửa DB.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 04 — Quản lý duyệt và nhân viên đối chiếu lại

1. Đăng xuất NV006, đăng nhập **NV005**, chọn **Trang cá nhân** → **Duyệt**.
2. Phải thấy yêu cầu `TEST-WEB-01` của NV006 trong team Kỹ thuật, đủ giờ đề nghị/lý do/giờ thực tế.
3. Bấm **Duyệt**, nhập ghi chú `Đồng ý giờ công tác TEST-WEB-01`, xác nhận.
4. Yêu cầu biến mất khỏi danh sách chờ.
5. Đăng nhập lại NV006 → **Giải trình → Đã xử lý**: có kết quả duyệt và ghi chú.
6. Mở ngày 13/11 trong bảng công: giờ **08:41–17:30**, nguồn **Đã giải trình**, trạng thái đi muộn; phút muộn **11** theo giờ ca. Ngày đã chốt không hiện IN_PROGRESS.
7. Tổng ngày công của tháng chỉ tính ngày này một lần; tải lại/chuyển tháng không làm tăng thêm ngày vì cùng một giải trình.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 05 — Hủy và từ chối giải trình

1. NV006 tạo giải trình ngày **12/11/2026**, loại **Lý do khác**, lý do `TEST-WEB-02: thử hủy`.
2. Trong danh sách chờ, bấm Hủy → chọn giữ: yêu cầu vẫn còn.
3. Bấm Hủy lần nữa → xác nhận: không còn ở Chờ duyệt, xuất hiện trạng thái **Đã hủy** ở Đã xử lý. Không có nút hủy lần nữa.
4. Tạo lại một yêu cầu ngày này với lý do `TEST-WEB-03: thử từ chối`.
5. NV005 → Duyệt → Từ chối: để trống ghi chú phải bị chặn; nhập `Cần bổ sung thông tin` rồi xác nhận.
6. NV006 thấy **Từ chối** và ghi chú; giờ đề nghị của bản bị từ chối không được áp vào bảng công.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 06 — Không tự duyệt, không đọc ngoài team

1. NV005 vào **Trang cá nhân → Giải trình**, tự gửi yêu cầu ngày 12/11 với lý do `TEST-WEB-MANAGER`.
2. Vào tab **Duyệt**: không được hiển thị yêu cầu của chính NV005 để tự duyệt.
3. Chọn Trang quản trị: bảng công/nhân viên/sự kiện chỉ trong team Kỹ thuật; không có các nút sửa công dành OWNER/HR.
4. HR NV002 → Trang quản trị → Giải trình: có thể xử lý yêu cầu của quản lý theo đúng Q011. Không dùng NV005 để duyệt chính mình.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 07 — OWNER: quản lý nhân viên và phòng ban

1. NV001 → Trang quản trị → Nhân viên: tìm `NV006`, mở chi tiết và các tab.
2. Kiểm hồ sơ khuôn mặt đang ACTIVE, 5 mẫu; xem bảng công/lịch sử liên quan.
3. Tạo một nhân viên thử có mã **REVIEW001**, tên **Nhân viên thử web**, điền các trường bắt buộc, chọn phương thức **Chấm công hộ**. Nếu mã đã tồn tại, dùng REVIEW002.
4. Tìm lại mã vừa tạo, sửa tên/lưu, tải lại trang và đăng nhập lại: thông tin sửa phải còn.
5. Thử tạm khóa rồi mở khóa chính nhân viên REVIEW vừa tạo; kiểm trạng thái thay đổi đúng.
6. Vào Phòng ban: thử tạo phòng **Phòng thử web**, sửa tên. Không cần đổi phòng ban của dữ liệu NV006/NV005 đang dùng cho các ca trên.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 08 — Ca, phân ca, ngày lễ

1. OWNER → Ca/Phân ca: tạo ca **Ca thử web**, 08:30–17:30, nghỉ 12:00–13:00, grace vào/ra 10 phút.
2. Phân ca cho **REVIEW001** theo Thứ Hai–Thứ Sáu, hiệu lực từ 16/11/2026.
3. Thử thêm phân ca khác trùng cùng nhân viên/thứ/khoảng hiệu lực: báo trùng, không lưu chồng lấn, giữ form để sửa.
4. Thêm ngày lễ **31/12/2026 – Ngày nghỉ thử web**, kiểm danh sách đúng năm.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 09 — Bảng công quản trị, sửa có lý do, xuất Excel

1. OWNER → Bảng công tháng 11/2026, lọc Kỹ thuật/NV006 và mở ngày 13/11 đã duyệt.
2. Kiểm nguồn Đã giải trình/giờ đã duyệt; nút lịch sử mở trang sự kiện với đúng nhân viên/ngày. Không có event gốc mới do duyệt giải trình là đúng.
3. Thử sửa công của **chính NV001**: nút không cho tự sửa hoặc server từ chối.
4. Thử sửa một ngày của REVIEW001/người khác: thiếu lý do không lưu; có lý do thì nguồn **Sửa tay**, tải lại vẫn giữ.
5. Xuất Excel: mở hai sheet **Tổng hợp / Chi tiết**, đọc đúng tiếng Việt/ngày/giờ; thống kê không cộng trùng ngày theo số request.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 10 — Bảo vệ: chấm hộ và mở cửa mô phỏng

1. NV020 → Trang quản trị: vào **Giám sát**.
2. Chấm công hộ: tìm **NV022 · Cao Nhật Minh**, chọn cửa có mode chấm công, nhập lý do `TEST-WEB-MANUAL`, xác nhận.
3. Phải xuất hiện sự kiện **Chấm công hộ** với thời điểm hiện tại/người thực hiện/lý do. API không nhận giờ quá khứ do người dùng nhập.
4. Tìm NV006 trong lựa chọn chấm hộ: khi còn FACE phải không có; không được tự chấm cho NV020.
5. Chọn **Mở cửa mô phỏng**, chọn cửa, nhập lý do `TEST-WEB-OPEN`: tạo sự kiện mở tay, không tạo giờ công của một nhân viên.
6. Chỉ bấm một lần rồi đợi kết quả; thao tác gửi lặp phải bị khóa khi đang gửi.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 11 — Tra cứu, CSV, báo cáo và quyền HR

1. NV020 → Sự kiện, lọc hôm nay/kết quả chấm hộ hoặc mở tay: thấy các thao tác ở mục 10.
2. Tab báo cáo chấm hộ: đối chiếu số lượt và số nhân viên khác nhau; một người được chấm nhiều lần không tăng số NV riêng biệt tương ứng.
3. Bỏ lọc nhân viên/người chấm nếu có, xuất CSV và mở trong Excel: tiếng Việt đúng. CSV chỉ hỗ trợ bộ lọc thời gian/cửa/kết quả theo hợp đồng hiện tại.
4. HR NV002 → Giám sát: có chấm hộ, **không có** xử lý cảnh báo/mở cửa tay.
5. MANAGER NV005: không có CSV/báo cáo/crop ngoài quyền; SECURITY không có trang quản lý hồ sơ nhân viên.
6. Nếu có cảnh báo UNKNOWN/SPOOF chưa xử lý, OWNER/SECURITY thử “Là nhân viên”: thiếu người liên kết phải bị chặn; sau lưu số mẫu của người liên kết không tăng.

Nếu không có cảnh báo chưa xử lý, ghi **Chưa thử** mục 6; cần quét ảnh/người thật qua kiosk ở cùng Hub để tạo cảnh báo, không tự chèn event vào DB.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## 12 — Giao diện điện thoại và rút đồng ý (làm cuối)

1. Thu nhỏ cửa sổ về khoảng 390 px hoặc dùng chế độ thiết bị của DevTools. NV006 → Trang cá nhân, chuyển bốn tab.
2. Không tràn ngang; thanh dưới cố định, chạm được; nút gửi/đóng hộp thoại không bị che. Ngày dd/MM/yyyy, giờ 24h HH:mm.
3. Khuôn mặt: có trạng thái ACTIVE/đã đồng ý nhưng **không hiện ảnh mẫu**.
4. Bấm Rút đồng ý → Hủy: trạng thái giữ nguyên.
5. Khi muốn thử xóa trên **bản sao review này**, bấm lại và xác nhận: chỉ báo thành công khi hoàn tất, phương thức thành **Chấm công hộ**, consent không còn.
6. OWNER mở lại NV006: hồ sơ/mẫu khuôn mặt không còn; công và lịch sử sự kiện ở các mục trước vẫn giữ. Muốn sử dụng mặt lại phải consent và đăng ký lại qua kiosk.

Chỉ xác nhận xóa khi đã xong các ca cần hồ sơ mặt. Không cần xóa để test các mục 01–11.

Kết quả: ☐ Đạt ☐ Lỗi ☐ Chưa thử. Ghi chú: …

## Gửi lỗi cho Codex

Mỗi lỗi gửi: **mã mục + tài khoản + thao tác + kết quả thực tế + kết quả mong đợi + ảnh màn hình**. Ví dụ: `04 / nv005 / duyệt TEST-WEB-01 / báo 403 dù đúng team`.

Luồng nhận diện vào/ra trực tiếp, đăng ký/duyệt mẫu mới, mất kết nối kiosk và chống giả mạo cần app/kiosk cùng Hub. Kịch bản trên tập trung phần web đã có; chống giả mạo T13 và demo T14 chưa nghiệm thu.

Nếu cần khởi động lại dịch vụ, xem [RUN-T12.md](ket-qua-kiem-thu/2026-11-16_T12/RUN-T12.md); `--resume` bây giờ tiếp tục bản review mới. Dữ liệu trước lần mở review này còn tại context riêng `LOCALAPPDATA\FaceGate\T12-before-user-review-context.json`.

