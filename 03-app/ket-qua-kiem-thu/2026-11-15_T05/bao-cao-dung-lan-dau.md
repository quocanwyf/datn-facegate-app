# Báo cáo T05 — Cần chốt cách đếm lỗi ghép thiết bị

- Trạng thái: **DỪNG — thiếu thông tin thiết kế để thực hiện khóa mã ghép sau 5 lần sai**.
- Commit nền: c110df6 (T04 đã push, mọi tiêu chí T04 đạt).
- Chưa triển khai T05, chưa chạy test WS hoặc tạo dữ liệu nhận dạng. Báo cáo này không phải nghiệm thu T05 và chưa commit/push vì task chưa đạt.

## Điểm thiếu thông tin

Đối chiếu nguồn thật ngày 15/11/2026:

- `openapi/openapi.yaml`, schema PairRequest: required chỉ `code`; optional device_info chỉ có model/os/app_version. Không có device_id, pairing_id, phiên thử ghép hoặc mã định danh yêu cầu ghép.
- DevicePairing.qr_payload chỉ chứa JSON `{hub,code}`.
- `db/schema.sql` có `device.pairing_attempts`; `db/thiet-ke-db.md` yêu cầu mã ghép 6 số/10 phút/khóa sau 5 lần.
- `ui/man-hinh/kiosk.md` K-01: PAIRING_LOCKED hiện “Nhập sai quá 5 lần, mã đã bị khoá”.

Ví dụ có hai thiết bị chờ ghép với hai mã khác nhau. Request gửi một mã không khớp mã nào: Hub không thể biết người dùng định ghép thiết bị nào để tăng pairing_attempts và khóa đúng mã sau 5 lần sai. Khóa theo IP là một chính sách khác, không phải khóa một mã/thiết bị như UI đang mô tả. Không được tự suy ra rằng cần tăng lỗi cho mọi thiết bị đang chờ, dò mã gần đúng, hoặc tự thêm trường hợp đồng.

Root AGENTS.md yêu cầu: “Nếu đặc tả và code mâu thuẫn, hoặc task thiếu thông tin: dừng, ghi câu hỏi vào báo cáo, không tự đoán thiết kế.” Vì vậy giữ nguyên nguồn chuẩn và xin chốt trước khi viết hành vi này.

## Phương án cụ thể để chốt

1. **Khóa lượt thử theo IP 10 phút sau 5 lần sai**: giữ PairRequest/QR hiện tại, cần sửa mô tả và thông báo UI thành khóa lượt thử từ máy/IP; pairing_attempts không được giả làm bộ đếm cho mã đích chưa biết. Đây là đề xuất chưa được duyệt, không tự áp dụng.
2. **Khóa đúng từng mã/phiên**: thêm pairing_id hoặc định danh phiên tương đương vào QR và PairRequest; luồng nhập thủ công cũng cần định danh này. Cần đồng bộ hợp đồng/UI trước khi code, không tự thêm endpoint/trường.

## Cần An làm — tin nhắn soạn sẵn

An chốt giúp T05: khóa sau 5 lần sai theo IP (đề xuất khóa 10 phút, giữ request code hiện tại và đổi thông báo), hay khóa đúng từng mã bằng pairing_id trong QR/request và luồng nhập thủ công? Hiện PairRequest chỉ có code nên nhập sai không xác định được device.pairing_attempts nào cần tăng. Codex đã push T02 script/RUN-T02, T03 và T04; T05 chưa code và không sửa nguồn chuẩn. Sau khi chốt, đồng bộ các nguồn liên quan rồi tiếp tục T05 → T12. Không cần chạy T02 trước.

## Tiêu chí nghiệm thu T05

Cả bốn tiêu chí T05 và các bổ sung Q-001–Q-013: **CHƯA CHẠY**. Không ghi pass, không archive spec khi chưa có bằng chứng.
