# Báo cáo T06 — REST quản trị, client TS và rà soát bảo mật

- Trạng thái: **XONG phạm vi T06**, theo ngoại lệ task cho phép để API chấm công/sự kiện tới T09/T11.
- Commit nền: ab712c9 (T05); commit triển khai tra `T06: implement scoped admin APIs and generated clients`.
- Máy: Windows, Python 3.13.13, PostgreSQL 16.16 native; torch CPU. Node 24.15.0/pnpm 11.25.0, TypeScript 5.9.3, openapi-typescript 7.13.0.

## Tiêu chí nghiệm thu

| # | Tiêu chí | Kết quả thật | Log | Đạt? |
|---|---|---|---|---|
| 1 | Contract test; liệt kê operation T09/T11 | 48 operation đã cài có route thật và đúng operationId/contract; 29 deferred được liệt kê chính xác | contract-tests.log, tests/test_openapi_contract.py | Đạt trong phạm vi |
| 2 | Quyền từng ô ma trận thuộc task | 50 ca đọc theo 5 nhóm role; OWNER/HR ghi nhân viên/phòng ban/tài khoản; HR chặn OWNER và field cửa của OWNER; MANAGER lọc đúng team và chặn đổi bộ lọc ra ngoài; mẫu ảnh OWNER/HR thật, các role khác 403 | admin-tests.log, pytest-full.log, real-run-03/summary.json | Đạt |
| 3 | Terminate/xóa file+dòng+gallery+audit | Ảnh/mẫu thật U03: gallery 1→0, profile biến mất, file không còn, có FACE_DELETE/EMPLOYEE_TERMINATE. Thử lỗi xóa giữ NULL consent/MANUAL, retry hoàn tất | real-review-03.log, real-run-03/summary.json | Đạt |
| 4 | Sinh client/tsc cả web+kiosk | gen:api chạy cả hai; web tsc toàn bộ và typecheck:api riêng; kiosk tsc strict không emit | web/kiosk-gen-api.log, web/kiosk-typecheck.log, web-api-typecheck.log | Đạt |
| 5 | Skill security review | differential-review chính thức Trail of Bits, đã ghim nguồn/license; 1 HIGH + 1 MEDIUM đã sửa và rà lại, có hồi quy | SECURITY-REVIEW.md, security-history.log, security-callers.json, permission-locks.log | Đạt |

Bộ kiểm cuối: **87 passed, 1 skipped, 3 warnings trong 101,84 giây** (`pytest-full.log`). Skip duy nhất: test màu T02 chưa có LFW. Không sửa vendor hoặc nới ngưỡng để đạt.

## Đã làm

Departments/users/roles/PIN/reset-password; employees tạo/sửa/suspend/reactivate/terminate/xóa mặt; face-profiles đọc/duyệt/từ chối, sample image có quyền; gates/policy/departments; settings/model đang chạy; audit; dashboard đọc dữ liệu thật; me/face và tự rút consent. Mọi thao tác ghi quản trị có audit; không lưu mật khẩu tạm vào audit/log.

Đầu vào mới kiểm trực tiếp bằng JSON Schema từ OpenAPI, dùng whitelist update. OpenAPI của app chỉ mô tả các route thật đã cài, dùng cùng schemas/operationId/roles/response nguồn. Test kiểm cả route thật để không che thiếu endpoint bằng việc chép tài liệu. Khác biệt cấu trúc include_router mới của FastAPI 0.163 được xử lý trong test; log lần phát hiện đầu giữ tại contract-discovery-first-run.log.

HR không sửa/cấp OWNER, không sửa name/mode/threshold/is_active của cửa. MANAGER chỉ team; read vai trò từ DB. Liveness không thể bật trước T13; W và quan hệ ngưỡng đếm được kiểm toàn bộ trước lưu, sai giữ cấu hình cũ. Runtime mô hình ghi phiên bản và thời điểm xác minh thật sau cổng kiểm.

Đồng thời duyệt cùng hồ sơ: chỉ một 200, lần sau 409 PROFILE_ALREADY_REVIEWED. Lỗi gallery/cleanup trả 503, không nhận dạng bằng snapshot chưa cập nhật. Xóa trước hết thu hồi consent/quyền dùng mặt, sau đó file/DB/cache/gallery; không khôi phục khi lỗi. Dữ liệu thử sinh bằng API/WS và ảnh thật được người dùng cung cấp, không seed giả khuôn mặt/event/công.

## Hai race tìm thấy và đã sửa

1. Quyền bị đổi trong lúc chốt MATCH: giữ FOR NO KEY UPDATE Device → Gate → Employee đến commit. Bài thử ảnh thật giữ ngay trước INSERT cho thấy suspend phải đợi event commit; không có OPEN mới sau khi đã báo thu hồi xong.
2. Reload giải phóng pause của thao tác khác: generation/token theo nhân viên **và loại thao tác/profile**, retry đúng chủ sở hữu. Suspend cùng người không hoàn tất hộ cleanup approval; full-delete chỉ hoàn tất những token đã chụp của đúng người sau xóa thành công. 5 test barrier và rà lại độc lập xác nhận sửa đúng.

Xem SECURITY-REVIEW.md để biết phạm vi/giới hạn; không tuyên bố đã kiểm mọi crash/interleave hoặc toàn bộ dự án.

## Client và phạm vi còn lại

Web/kiosk sinh schema.d.ts từ OpenAPI, openapi-fetch gắn token qua provider (kiosk hỗ trợ provider bất đồng bộ để T08 nối SecureStore). T06 chưa viết màn hình/khung Expo. Web có `typecheck:api` tự chứa để kiểm client ngay khi clone trước T07; `typecheck` toàn dự án hiện cũng đã chạy với UI đang có tại máy, khung Vite/UI sẽ commit đúng task T07.

29 operation trong contract-tests.log là ca/ca cá nhân/phân ca/ngày lễ/bảng công/giải trình/Excel và event/manual-open. Không tạo stub trả thành công. Ca MANAGER Excel chỉ team thuộc /attendance/export được ghi để kiểm ở T09; T06 không đánh dấu ca đó đã chạy. Không archive feature còn AC UI hoặc nghiệp vụ T09–T12.

## File chính

hub/app/api/{contract,organization,employees,faces,gates,settings,dashboard}.py; biz/{admin,gallery_sync}.py và các đường ghi event/xóa/đăng ký; recog/{runtime,mutations}.py; scripts/{review_t06,security_inventory}.py; tests/{test_admin_api,test_openapi_contract,test_mutation_barrier}.py; web/kiosk package+src/api, lockfile; skill differential-review và nguồn/license.

## Cần An làm

Không có bước bắt buộc để tiếp tục T07. Kịch bản xem/chạy lại ở REVIEW-T06.md. T02 vẫn chờ An chạy riêng khi rảnh, không chặn tiến độ.
