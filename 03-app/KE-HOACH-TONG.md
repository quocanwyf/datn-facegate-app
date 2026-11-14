# KẾ HOẠCH TỔNG — PHẦN APP ĐATN (thiết kế → bàn giao → code)
> Cập nhật 14/11/2026 (lần 2: chốt theo trả lời của An về bàn giao, máy Hy, animation, skill), session thiết kế app (Claude) cùng An. **File điều phối chính của phần App**: đọc file này trước, rồi tới `dac-ta-app.md` v1.4.2, `db/thiet-ke-db.md`.
> Ký hiệu trạng thái: ✅ xong (có file) · 🔄 đang làm · ⏳ chưa làm · 🅰 việc của An · 🅷 việc của Hy.

## 0. Vai trò và cách làm việc
| Ai | Làm gì | Không làm |
|---|---|---|
| **An + Claude (chat này)** | Đặc tả, ERD, thiết kế DB, schema/seed, UI design system, hợp đồng API, AGENTS.md + skill riêng của dự án, plan từng task cho Codex, đóng gói bàn giao, review kết quả từng mốc | Không code tính năng |
| **Hy + Codex** | Code toàn bộ Hub, Web, Kiosk **theo plan** trong `03-app/plan-codex/`; mỗi task xong nộp báo cáo + log | Không tự đổi đặc tả/thiết kế; đề xuất ghi vào mục "Đề xuất cho thiết kế" của báo cáo task |
| **An** | Duyệt mọi quyết định; chạy các bước cần **GPU RTX 3050** (M0, demo) vì laptop An là máy Hub; tình nguyện viên khuôn mặt | — |
| **Review chéo** | Session Claude mới, đọc lạnh bộ bàn giao, tìm lỗ hổng trước khi gửi Hy | — |

Luồng một task: Claude soạn task → An duyệt → Hy giao cho Codex → Codex code + test + báo cáo → Hy đẩy lên repo → An mang báo cáo về chat này → Claude đối chiếu tiêu chí → task tiếp.

## 1. Trạng thái (cập nhật 14/11/2026 — **xong phần thiết kế + setup, sẵn sàng bàn giao**)
| # | Hạng mục | Trạng thái | File |
|---|---|---|---|
| 1 | Nghiệp vụ, kiến trúc, đặc tả (5 vòng review) | ✅ | `dac-ta-app.md` v1.4.3 |
| 2 | ERD chi tiết | ✅ | `db/erd/` |
| 3 | Thiết kế DB, schema, seed, test ràng buộc 44/44 | ✅ | `db/` |
| 4 | **S1** Design system + layout 31 màn (9 Kiosk, 8 `/me`, 14 `/admin`) + token + màu trạng thái chung (20/20 cặp đạt AA) | ✅ | `ui/` |
| 5 | **S2** Hợp đồng API (66 path, 77 operation, lint 0 lỗi, sinh client TS thử được) + giao thức WS | ✅ | `openapi/` |
| 6 | **S3** `AGENTS.md` (gốc repo, hub, web, kiosk) + 4 skill riêng + danh sách skill ngoài | ✅ | `ban-giao/repo-root/`, `hub|web|kiosk/AGENTS.md`, `SKILLS-NGOAI.md` |
| 7 | **S4** Plan 16 task T00–T15 + mẫu báo cáo | ✅ | `plan-codex/` |
| 8 | **S5** Script đóng gói, kiểm checkpoint, kiểm bí mật, README bàn giao | ✅ | `tools/`, `ban-giao/repo-root/` |
| 9 | **S6** Tự kiểm bộ bàn giao | ✅ | mục 7 bên dưới |
| 10 | **S7** Đẩy repo GitHub public + gửi Hy | ⏳ 🅰 | hướng dẫn mục 8 |
| 11 | Code (Hy + Codex) T00 → T15 | ⏳ 🅷 | `plan-codex/README.md` |

## 2. Quyết định cho hai đầu vào mới

### 2.1 UI kit
| Kit | Dùng cho | Vì sao | Lưu ý khi chuyển thành design system |
|---|---|---|---|
| **Canopy** (teal `#0E7C74`, Poppins + Inter, control bo 8–12, bảng/biểu mẫu dày vừa) | **Web Admin `/admin` và trang nhân viên `/me`** (cùng codebase, cùng theme) | Kit gốc là dashboard B2B: bảng, thanh lọc, pill trạng thái, tab — khớp màn quản trị | Đặc tả chọn **Ant Design**, kit viết cho Tailwind → S1 sẽ **map token sang theme Ant Design** (`ConfigProvider`: colorPrimary, borderRadius, fontFamily, Table/Form/Tag token). Bỏ phần glass-frame/ảnh phong cảnh nếu làm chậm; `/me` dùng cùng token nhưng layout mobile 1 cột |
| **Fresh Bloom** (lime `#A3D853`, nút pill, bo lớn, mẫu "scan camera") | **Kiosk App** (React Native) | Kit có sẵn mẫu màn camera quét (khung lime, overlay quét, CTA tròn) — đúng màn K-02 | Lime **không dùng làm chữ** trên nền trắng (1,7:1) theo chính kit; kết quả nhận dạng dùng màu ngữ nghĩa (thành công / từ chối / cảnh báo) lấy từ bảng semantic của kit, kiểm tương phản để đọc được từ 1–2 m |
| Chung | — | Hai sản phẩm hai thiết bị nên khác màu chính là chấp nhận được | S1 thống nhất **màu trạng thái** (MATCH / DENY / SPOOF / ALREADY, trạng thái ngày công) giữa web và kiosk để người dùng thấy cùng một ý nghĩa |

Kit được dựng lại từ ảnh màn hình của sản phẩm khác (ghi trong STYLE-GUIDE); chỉ dùng **phong cách**, không dùng logo/ảnh/nội dung — đúng như kit đã ghi.

### 2.2 Skill repo cho Codex
Giữ nguyên danh sách skill ngoài trong file của An. Bổ sung/điều chỉnh khi làm S3:
- Vị trí skill: `.agents/skills/` ở gốc repo (Codex quét từ thư mục đang làm việc lên gốc repo — đã đối chiếu tài liệu Codex 14/11/2026); skill riêng của từng phần có thể đặt ở `03-app/hub/.agents/skills/` v.v.
- Skill `kiosk-ws-protocol`: file của An ghi "WSS" → bản demo v1.4 là **WS (HTTP trong LAN)**.
- Skill riêng: **4 skill** (`hub-rules`, `api-contract`, `kiosk-ws-protocol`, `cham-cong-vn`) — An quyết định không cần skill thứ 5.
- **Animation làm ngay trong lúc dựng UI** (không để sau): web dùng skill **GSAP** (greensock/gsap-skills), kiosk dùng skill **animations** của Software Mansion (Reanimated). S1 ghi đặc tả chuyển động cho từng màn; T07, T08 cài và dùng.
- **Cách cài skill:** 4 skill riêng do Claude viết ở S3 và commit sẵn trong repo. Skill ngoài do **Codex cài ở task T00 trên máy Hy** (bằng `$skill-installer`, vào `.agents/skills/` của repo) rồi commit, để mọi người clone repo đều có cùng bộ skill.
- Ghi chú trong file của An: "có nguồn ghi openai/skills đã ngừng phát triển" — **chưa xác minh**, Hy kiểm README trước khi cài.
- Ở gốc dự án nghiên cứu đã có `AGENTS.md` (cho phần thực nghiệm, ngày 08/11). Repo bàn giao sẽ có `AGENTS.md` **riêng cho App** (mục 3), không dùng lại file đó.

## 3. Việc còn lại trước bàn giao (An + Claude)
| Bước | Nội dung | Đầu ra | Tiêu chí xong |
|---|---|---|---|
| **S1** UI design system | Gộp 2 kit (web teal Canopy, kiosk lime Fresh Bloom — An chốt) → design system của dự án: token màu/chữ/khoảng cách/bo góc/bóng, **chuyển động (GSAP cho web, Reanimated cho kiosk)**; map sang **theme Ant Design** (web) và **theme RN** (kiosk); bảng màu trạng thái chung; component dùng chung; **layout từng màn** (K-01…K-12, E-01…E-10, W-01…W-16) theo một mẫu thống nhất (mục đích, vùng bố cục, component, dữ liệu từ API nào, trạng thái rỗng/lỗi/đang tải, copy tiếng Việt) | `ui/design-system.md`, `ui/tokens/{web-antd-theme.json, kiosk-theme.json}`, `ui/man-hinh/{kiosk,me,admin}.md`, (tuỳ chọn) vài wireframe PNG | Mỗi màn trong đặc tả §9 có đúng 1 mục layout; mọi màu chữ đạt AA |
| **S2** Hợp đồng API | `openapi.yaml` đầy đủ endpoint §8 đặc tả, schema khớp `db/`, mã lỗi chung, ví dụ request/response; mô tả 2 giao thức WebSocket (kiosk, monitor) trong `openapi/ws-protocol.md` | `openapi/openapi.yaml`, `openapi/ws-protocol.md` | Lint OpenAPI không lỗi (vd. `npx @redocly/cli lint`); sinh được client TypeScript thử |
| **S3** Hướng dẫn cho Codex | `AGENTS.md` ở gốc repo + `03-app/hub/`, `web/`, `kiosk/`; 4 skill riêng (`hub-rules`, `api-contract`, `kiosk-ws-protocol`, `cham-cong-vn`) đúng định dạng `SKILL.md` (frontmatter `name`, `description`); `SKILLS-NGOAI.md` liệt kê skill ngoài + lệnh cài | các file trên | Mỗi luật quan trọng của đặc tả có ở đúng 1 nơi (AGENTS.md hoặc skill), có trỏ về mục đặc tả |
| **S4** Plan task cho Codex | Mỗi task 1 file `plan-codex/Txx-<ten>.md`: mục tiêu, đọc gì, được ghi vào đâu, các bước, **tiêu chí nghiệm thu đo được**, lệnh kiểm, điều kiện dừng, mẫu báo cáo. Chuyển `prompt-giao-M0.md` thành T01–T02 | `plan-codex/README.md` + T00…T15 | Mỗi tiêu chí M0–M7 trong đặc tả §12 nằm trong ≥ 1 task |
| **S5** Đóng gói repo | Tạo repo bàn giao (mục 5), `.gitignore`, `README-BAN-GIAO.md` (Hy đọc đầu tiên: cài đặt, tải checkpoint, chạy T00), script kiểm checksum checkpoint | repo + README | Clone sạch trên máy khác chạy được T00 |
| **S6** Review chéo bộ bàn giao | Session Claude mới đọc lạnh repo như Hy/Codex, tìm chỗ thiếu/mâu thuẫn, thử T00 | `03-app/review/<ngày>_review-ban-giao.md` | Không còn vấn đề mức Cao |
| **S7** Gửi Hy 🅰 | Mời Hy vào repo, gửi link checkpoint, họp 15 phút hướng dẫn luồng làm việc | — | Hy chạy xong T00 và gửi báo cáo |

Thứ tự: **S1 và S2 song song** (S2 không phụ thuộc UI) → S3 → S4 → S5 → S6 → S7.

## 4. Kế hoạch code (Hy + Codex) — sẽ chi tiết hoá ở S4
| Task | Nội dung | Mốc đặc tả | Phụ thuộc | Máy chạy |
|---|---|---|---|---|
| T00 | Cài môi trường dev trên Windows (Python, Node, PostgreSQL native, Android Studio + **máy ảo Android**, Expo), **Codex cài skill ngoài vào `.agents/skills/` rồi commit**, tạo DB từ `schema.sql` + `seed.sql`, chạy `test_constraints.sql` = 44/44 | — | S5 | máy Hy |
| T01 | Vendor code thực nghiệm + `MANIFEST.sha256` + `test_vendor_hash`; lớp nạp mô hình với **cổng khởi động 4 bước** — **task đầu tiên cần file checkpoint → Hy báo An gửi** | M0 (2)(3) | T00 | máy Hy (CPU được) |
| T02 | `check_env`, so tensor, parity feature/landmark/màu, sinh ngưỡng từ log | M0 (1)(3)(4)–(7) | T01 | 🅰 **laptop An (GPU)**, Hy viết script |
| T03 | Khung Hub: FastAPI, cấu hình, SQLAlchemy 2 + Alembic **tương đương `schema.sql`** (chạy lại `test_constraints.sql` 44/44 trên DB tạo bằng Alembic), auth JWT + RBAC, nạp seed | M1, M3 | T00 | máy Hy |
| T04 | Lõi nhận dạng: detector, embedder, gallery, `decide()` + **test vét cạn**, worker thread suy luận | M1 | T01, T03 | máy Hy (CPU) |
| T05 | WS Kiosk (dừng-và-chờ), ghép thiết bị, đăng ký khuôn mặt → `PENDING_REVIEW`, script Kiosk giả lập | M1, M2 | T04, S2 | máy Hy |
| T06 | Cài các endpoint REST theo `openapi.yaml`; sinh client TS cho web + kiosk | M1, M3 | T03, S2 | máy Hy |
| T07 | Web Admin: theme Canopy→AntD **+ GSAP**, layout, đăng nhập, phân quyền route; W-03/04/05/07/08/14 | M3 | T06, S1 | máy Hy |
| T08 | Kiosk App: theme Fresh Bloom **+ animation Reanimated**, K-01…K-12, camera, WS client | M2 | T05, S1 | máy Hy, **máy ảo Android** (camera máy ảo lấy webcam laptop; máy ảo gọi Hub trên cùng máy qua `10.0.2.2`) |
| T09 | Chấm công BE: ca, phân ca, ngày lễ, `recompute_day`, `finalize_day`, giải trình, chấm hộ, Excel + **bộ test kịch bản biên** | M4 | T06 | máy Hy |
| T10 | Chấm công FE: W-06, W-09, W-12 | M4 | T07, T09 | máy Hy |
| T11 | Ra vào & giám sát: chính sách cửa, `/ws/monitor`; W-02, W-10, W-11 | M5 | T07, T05 | máy Hy |
| T12 | Trang nhân viên `/me`: E-01…E-10 | M6 | T07, T09 | máy Hy |
| T13 | Chống giả mạo (MiniFASNet, hiệu chỉnh L với người tình nguyện) | M7 | T04, T08 | 🅰 laptop An (GPU) + Hy |
| T14 | Tích hợp đầu-cuối trên laptop Hub + điện thoại thật; đo độ trễ (§11); kịch bản demo | §11, §12 | tất cả | 🅰 + 🅷 |
| T15 | Tư liệu cho quyển: ảnh màn hình, bảng kết quả kiểm thử, sơ đồ | — | T14 | 🅷, Claude soạn khung chương |

**Song song được:** T03 ∥ T01; T07 ∥ T08 (sau S1, S2); T09 ∥ T11.

## 5. Bàn giao cho Hy (đã chốt 14/11/2026)
### 5.1 Cách gửi
| Thứ | Cách gửi | Ghi chú |
|---|---|---|
| **Code + tài liệu** | **GitHub repo public** (An quyết định: ĐATN/môn học, không cần mời) | Hy clone về; Codex làm việc trên bản clone |
| **1 file checkpoint**: `best.pt` của UniFace + V1 s3 (~132 MB) — mô hình duy nhất app dùng (v1.4.2 bỏ So sánh mô hình) | Google Drive hoặc zip qua Zalo, **gửi khi Hy tới T01** | GitHub chặn file > 100 MB, và checkpoint train trên CASIA nên **không đưa lên repo public**. Hy đặt đúng đường dẫn ở 5.2 rồi chạy script kiểm SHA-256 |
| **File `.env`** | **Không cần gửi** | Repo có sẵn `.env.example`; bản demo không có bí mật thật (chỉ chuỗi kết nối Postgres trên máy Hy + `JWT_SECRET` tự sinh). Hy tự tạo `.env` theo hướng dẫn trong `README-BAN-GIAO.md` |

Vì repo **public**, trước khi push lần đầu (S5) chạy kiểm tra: không có `.env`, `*.pt`, ảnh khuôn mặt, thư mục dữ liệu Hub, LFW; `.gitignore` chặn sẵn các loại này. Mật khẩu/PIN trong `seed.sql` chỉ là dữ liệu demo.

### 5.2 Nội dung repo (tên gợi ý `datn-facegate-app`)
Repo **không** chứa toàn bộ thư mục nghiên cứu (~7,9 GB, chủ yếu checkpoint). Repo giữ **cùng đường dẫn tương đối** với thư mục nghiên cứu để mọi đường dẫn trong đặc tả vẫn đúng:
```
datn-facegate-app/
├── README-BAN-GIAO.md          ← Hy đọc đầu tiên
├── AGENTS.md                   ← luật chung cho Codex (phần App)
├── .agents/skills/             ← 4 skill riêng (commit sẵn) + skill ngoài (Codex cài ở T00)
├── .gitignore                  ← chặn *.pt, .env, dữ liệu khuôn mặt, LFW, node_modules, .venv
├── .env.example
├── 03-app/                     ← đặc tả, db, ui, openapi, plan-codex, review, so-do (+ hub/ web/ kiosk/ do Codex tạo)
└── 02-thuc-nghiem/             ← BẢN RÚT GỌN, CHỈ-ĐỌC, chỉ các file App cần:
    ├── code/{train.py, fr/}                         (vendor)
    ├── code-v1/fr/{backbones,eval,align,utils}/     (test so khớp code-v1)
    ├── eval-test/evaltest/{__init__,features,common,strip_backbone}.py
    ├── eval-test/manifest/manifest_24.json
    ├── eval-test/tools/windows/logs/strip_map_ban_sao.json
    └── results/
        ├── 2026-11-12_test-blufr-lfw/eval_test/{ket_qua_blufr_lfw.json, env.json}
        ├── 2026-11-05_eval-lfw/align_log.csv
        └── V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/{val.jsonl, summary.json, checkpoints/best.pt*}
```
`*` không có trong repo, gửi riêng (5.1). Script `03-app/tools/kiem-checkpoint.py` so SHA-256 với `manifest_24.json` (`120489…ef88`). Danh sách file chính xác của bản rút gọn chốt ở S5 bằng script sao chép + kiểm hash, không chép tay.

### 5.3 Môi trường của Hy
- **Windows**, Codex trong **ChatGPT desktop app** (chế độ Codex). Dùng chế độ **Local**: agent chạy lệnh trên chính máy Hy qua PowerShell, làm việc trực tiếp trên thư mục repo đã clone — cần vì task phải chạy PostgreSQL và máy ảo Android trên máy Hy. Không dùng chế độ Cloud cho các task này.
- **Không cần điện thoại**: Kiosk chạy trên máy ảo Android (Android Studio), camera máy ảo lấy webcam laptop.
- Hub khi dev chạy trên máy Hy bằng **CPU** (đủ cho phát triển). Các bước cần GPU (T02, T13) và buổi demo chạy trên **laptop An**.

### 5.4 Quy ước làm việc qua repo
- Mỗi task một nhánh `task/Txx-<ten>` → Pull Request → An duyệt (mang báo cáo về chat này để đối chiếu) → merge.
- Báo cáo task: `03-app/ket-qua-kiem-thu/<ngày>_Txx/bao-cao.md` + log thật.
- Đề xuất đổi thiết kế: ghi trong báo cáo, **không** sửa `dac-ta-app.md` / `db/` / `ui/` / `openapi/` khi chưa được An duyệt.
- Task nào cần checkpoint mà Hy chưa có → Codex dừng, Hy báo An gửi.

## 6. Đã chốt (An, 14/11/2026)
| Câu hỏi | Trả lời |
|---|---|
| Máy Hy | Windows; Kiosk chạy máy ảo Android, không cần điện thoại |
| Repo | GitHub **public** |
| Checkpoint | Google Drive hoặc zip Zalo, gửi khi cần (từ T01) |
| Màu | Web teal (Canopy), Kiosk lime (Fresh Bloom) |
| Codex | ChatGPT desktop app, chế độ Codex (Local) |
| Skill thứ 5 `datn-integrity` | Bỏ |
| Animation | Làm ngay khi dựng UI: GSAP (web), Reanimated/Software Mansion (kiosk) |
| So sánh mô hình trong app | **Bỏ** — chỉ 1 mô hình V1 s3; so sánh dùng kết quả đã đo trong quyển (đặc tả v1.4.2) |

Còn mở: tên repo (gợi ý `datn-facegate-app`); laptop Hy có webcam để làm camera cho máy ảo không.


## 7. Tự kiểm bộ bàn giao (S6, 14/11/2026)
| Kiểm | Kết quả |
|---|---|
| `schema.sql` + `seed.sql` + `test_constraints.sql` trên PostgreSQL 16 | 44/44 |
| `openapi.yaml` lint (Redocly) | 0 lỗi (còn 4 cảnh báo không ảnh hưởng: thiếu license, server ví dụ, `/health` `/version` không có 4xx) |
| Sinh client TS từ `openapi.yaml` + `tsc --strict` | biên dịch được |
| 31 màn trong đặc tả §9 đều có layout trong `ui/man-hinh/` | đạt |
| 53 endpoint được nhắc trong `ui/`, `plan-codex/`, skill đều có trong `openapi.yaml` | đạt |
| 12 đường dẫn `02-thuc-nghiem/` mà plan/skill nhắc tới đều có trong bản rút gọn | đạt |
| Frontmatter 4 skill (`name` khớp thư mục, có `description`) · 4 file JSON parse được | đạt |
| Tương phản màu 20/20 cặp ≥ 4,5:1 | đạt |
| `kiem-bi-mat.py` trên gói bàn giao | SẠCH |
| `kiem-checkpoint.py`: gói (không có file) → THIẾU; thư mục nghiên cứu → OK, SHA-256 khớp manifest | đạt |
| Gói bàn giao: 89 file app/gốc + 76 file `02-thuc-nghiem` rút gọn (10 MB), tổng ~13 MB | — |
**Chưa kiểm (để Hy/Codex làm):** cài đặt thật trên Windows (T00), mọi phần code.

## 8. Đẩy repo GitHub (S7 — An làm trên Windows)
Gói đã tạo sẵn ở `datn-cv-facerecognition\_ban-giao\datn-facegate-app\` (tạo lại bằng `python 03-app\tools\dong-goi-repo.py <thư mục nghiên cứu> <thư mục ra rỗng>` nếu sửa tài liệu sau này).
```powershell
# 1) Chuyển gói ra ngoài thư mục nghiên cứu (đường dẫn không dấu, không khoảng trắng)
Move-Item "$HOME\Desktop\datn-cv-facerecognition\_ban-giao\datn-facegate-app" "D:\code\datn-facegate-app"
cd D:\code\datn-facegate-app
# 2) Kiểm lần cuối
python 03-app\tools\kiem-bi-mat.py          # phải in SẠCH
# 3) Tạo repo
git init -b main
git add .
git status                                  # nhìn lại: không có .env, *.pt, ảnh khuôn mặt
git commit -m "Handoff: spec, DB, UI design system, API contract, Codex plan"
# 4a) Có GitHub CLI:
gh repo create datn-facegate-app --public --source . --push
# 4b) Không có gh: tạo repo public trống trên github.com rồi
git remote add origin https://github.com/quocanwyf/datn-facegate-app.git
git push -u origin main
```
5) Gửi Hy: link repo + lời nhắn "đọc `README-BAN-GIAO.md`, giao T00 cho Codex".
6) Khi Hy tới T01: gửi `best.pt` (`02-thuc-nghiem\results\V1-s3-Hy\phien-1\r18_uniface_v1_lam0.6_m0.45_s3_e28\checkpoints\best.pt`, 137.372.031 byte) qua Google Drive/Zalo.

**Sau khi bàn giao, mọi sửa tài liệu thiết kế** làm ở thư mục nghiên cứu (nguồn sự thật) trong chat thiết kế, rồi chép sang repo (hoặc An commit thẳng vào repo và chép ngược) — tránh hai bản lệch nhau.
