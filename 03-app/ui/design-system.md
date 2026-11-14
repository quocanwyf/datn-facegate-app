# DESIGN SYSTEM — APP CHẤM CÔNG & RA VÀO (bản DEMO)
> 14/11/2026, session thiết kế app. Nguồn phong cách: hai UI kit An chọn (`design-ui-kit/`, bản giải nén ở `ui/kit-goc/`):
> **Canopy** (teal) → Web (`/admin` + `/me`) · **Fresh Bloom** (lime) → Kiosk App. Chỉ dùng **phong cách**, không dùng logo/ảnh/nội dung của sản phẩm gốc (như kit đã ghi).
> Đi kèm: `ui/tokens/web-antd-theme.json`, `ui/tokens/web-css-vars.css`, `ui/tokens/kiosk-theme.json`, `ui/tokens/status.json`, `ui/man-hinh/{kiosk,me,admin}.md`.
> Đặc tả màn hình: `dac-ta-app.md` §9 (v1.4.2). **Không thêm màn ngoài §9.**

---

## 1. Nguyên tắc
1. **Một màu nhấn mỗi sản phẩm.** Web: teal `#0E7C74` chỉ cho nút chính, tab đang chọn, rail điều hướng, checkbox. Kiosk: lime `#A3D853` chỉ để tô nền (khung quét, kết quả OK), **không bao giờ là màu chữ**.
2. **Trạng thái chỉ thể hiện bằng bộ màu trạng thái chung** (mục 4) — cùng một ý nghĩa thì cùng một màu ở web và kiosk.
3. **Tách lớp bằng tông màu, không bằng viền**: thẻ trắng trên nền xám nhạt; ô nhập/tiêu đề bảng tô xám.
4. **Tiếng Việt có dấu đầy đủ**: chỉ dùng font có bộ ký tự tiếng Việt (mục 3).
5. **Kiosk đọc được từ 1–2 m**: chữ kết quả ≥ 48 px, tương phản ≥ 4,5:1, mỗi màn một thông điệp.
6. **Chuyển động có mục đích** (mục 7): báo trạng thái, không trang trí; tôn trọng `prefers-reduced-motion` / chế độ giảm chuyển động.
7. **Không hiển thị ảnh khuôn mặt trên Kiosk** (đặc tả §5.9). Web chỉ hiện ảnh mẫu ở W-04, W-08 và crop người lạ ở W-10/W-11.

## 2. Màu
### 2.1 Web (Canopy)
| Vai trò | Token | Hex |
|---|---|---|
| Màu chính | `primary` | `#0E7C74` |
| Chính khi hover/nhấn | `primary-hover` | `#0A5F59` |
| Nền nút mềm / chọn | `primary-soft` | `#DDF1EE` (chữ trên nó: `#0A5F59`) |
| Rail điều hướng | gradient | `#12A08F → #0B7E73` (180°) |
| Nền trang | `bg` | `#F7F9F8` |
| Thẻ / panel | `surface` | `#FFFFFF` |
| Ô nhập, tiêu đề bảng, ô thông tin | `surface-muted` | `#F4F5F4` |
| Dòng đang chọn | `surface-selected` | `#E3EBE9` |
| Đường chia | `border` | `#EDEFEE` |
| Chữ chính / phụ / gợi ý | `text-*` | `#1B2B2A` / `#5F6865` / `#6A726F` |
| Chấm thông báo | `dot` | `#E5484D` |

**Bỏ khỏi bản demo:** khung "glass" mờ và nền ảnh phong cảnh của Canopy (tốn hiệu năng, không giúp nghiệp vụ). Giữ gradient rail và nền `hero-mist` nhẹ cho banner tiêu đề trang.

### 2.2 Kiosk (Fresh Bloom)
| Vai trò | Token | Hex |
|---|---|---|
| Nhấn (chỉ tô nền) | `primary` | `#A3D853` (chữ trên nó: mực `#1A1A18`) |
| Chữ/icon xanh trên nền trắng | `primary-strong` | `#4F7C20` |
| Mực (nút chính, chữ) | `inverse` | `#1A1A18` |
| Amber | `accent` | `#F5A00A` |
| Đỏ | `danger` | `#B5241F` |
| Nền / bề mặt / bề mặt nổi | `bg` / `surface` / `surface-raised` | `#EAE8E4` / `#F1F0ED` / `#FFFFFF` |
| Chữ chính / phụ | `text-*` | `#1A1A18` / `#66635E` |

### 2.3 Tương phản đã đo (14/11/2026, script `tools/contrast.py`)
Tất cả **20/20 cặp** dùng trong design system đạt ≥ 4,5:1, ví dụ: chữ trắng trên nút teal 5,06 · chữ `#0A5F59` trên nút mềm 6,40 · mực trên lime 10,38 · chữ trắng trên đỏ `#B5241F` 6,49 · mực trên amber 8,23 · chữ phụ kiosk 4,89 · 7 cặp pill trạng thái web 5,14–7,23. Không dùng các cặp kit đã ghi là trượt (teal-600 trên teal-100, lime/amber làm chữ trên trắng).

## 3. Chữ
| | Web | Kiosk |
|---|---|---|
| Tiêu đề, số lớn | **Be Vietnam Pro** 500/600 | **Inter** 600 (tracking âm) |
| Giao diện, nội dung | **Inter** 400/500 | **Inter** 400/500 |
| Số | `font-variant-numeric: tabular-nums` | như web |

**Vì sao không dùng Poppins như kit Canopy:** Poppins trên Google Fonts chỉ có bộ Latin/Devanagari, phần lớn chữ có dấu tiếng Việt (dải U+1EA0–1EF1, vd. ạ ấ ế ữ) không có → trình duyệt sẽ ghép font khác giữa chữ. Be Vietnam Pro có bộ Vietnamese, cùng dáng hình học. Inter có bộ Vietnamese. Khi cài font phải chọn **subset `vietnamese`** (vd. gói `@fontsource/be-vietnam-pro`, `@fontsource/inter` — chọn file có `vietnamese`).

**Thang chữ web:** display 48 · h1 36 · h2 28 · h3 22 · h4 18 (Be Vietnam Pro 500) · h5 16 / h6 14 (Inter 600) · body 16/14/13 · bảng 13 (tiêu đề cột 12/500) · nhãn 12 · overline 11 (in hoa, chỉ cho nhãn bước) · nút 14/500 · số KPI 28.
**Thang chữ kiosk** (tablet ngang ~1280×800 dp): kết quả tên 56/600 · dòng phụ kết quả 28 · tiêu đề màn 32 · gợi ý trên camera 24/500 · đồng hồ 40/600 tabular · body 18 · nhãn 15/500 · nút 18/600.
Viết hoa đầu câu; ngày `dd/MM/yyyy`, giờ `HH:mm` (24 giờ), múi giờ công ty.

## 4. Bộ màu trạng thái chung (`ui/tokens/status.json`)
Mỗi trạng thái có **pill** (web, nền nhạt + chữ đậm) và **khối kết quả** (kiosk, nền đậm + chữ tương phản). Ý nghĩa gom về 7 nhóm:

| Nhóm | Pill web (nền / chữ) | Kiosk (nền / chữ) | Dùng cho |
|---|---|---|---|
| `success` | `#DDF6DF` / `#256B2F` | `#A3D853` / `#1A1A18` | Kiosk OK · ngày công `NORMAL` · hồ sơ mặt `ACTIVE` · giải trình `APPROVED` · event `MATCH` · thiết bị `ACTIVE` |
| `progress` | `#FCEFB4` / `#7A5B00` | `#F5A00A` / `#1A1A18` | Kiosk ALREADY ("Đã ghi nhận lúc…") · `LATE` · hồ sơ `PENDING_REVIEW` · giải trình `PENDING` · thiết bị `PENDING` |
| `warning` | `#FFF1E0` / `#9A4A00` | — | `EARLY`, `LATE_EARLY`, `MISSING_OUT` (+ cờ nghi quên quét) · event `UNKNOWN` |
| `error` | `#FDECEB` / `#B42318` | `#B5241F` / `#FFFFFF` | Kiosk DENY · `ABSENT` · hồ sơ `REJECTED` · giải trình `REJECTED` · event `DENIED_RULE`, `DENIED_INACTIVE` · NV `TERMINATED` · thiết bị `REVOKED` |
| `danger-strong` | `#FDECEB` / `#B42318` + icon khiên | `#1A1A18` / `#FFFFFF` + viền đỏ 6 px | event / kết quả **SPOOF** (nghi giả mạo) |
| `info` | `#E3F2FD` / `#1767AD` | — | `IN_PROGRESS` · `NOT_STARTED` |
| `new` | `#DFF5F8` / `#0A6670` | — | `LEAVE` · event `MANUAL_ATTENDANCE`, `MANUAL_OPEN` · NV `MANUAL` |
| `neutral` | `#EDEFEE` / `#46504D` | — | `OFF`, `HOLIDAY` · NV `SUSPENDED` · giải trình `CANCELLED` · hồ sơ "chưa có" |

Nhãn tiếng Việt của mọi giá trị enum: `ui/tokens/status.json` (`label_vi`). **Không** tự đặt nhãn khác trong code.

## 5. Khoảng cách, bo góc, bóng
| | Web | Kiosk |
|---|---|---|
| Đơn vị | 4 px; thang 4·8·12·16·20·24·32·40·48·64 | 4 px; như web + 80·96 |
| Lề nội dung | 24–32 px | 32 px |
| Bo góc | ô nhập 8 · nút 12 · thẻ 16 · banner 20 · pill trạng thái 6 | nút **tròn hẳn (pill)** · thẻ 24 · sheet 32 · khung quét 44 |
| Bóng | rất nhẹ, tối đa `0 4px 8px /.04, 0 16px 40px -12px /.08` (modal) | tối đa `0 12px 32px -8px /.06, 0 24px 64px -12px /.08` |
| Chiều cao điều khiển | 32 / 40 / 44 (đăng nhập) ; ô nhập nhãn-trong 56 | nút 52–64 ; ô PIN 72 |

## 6. Component
### 6.1 Web — dùng **Ant Design 5** + theme `web-antd-theme.json`
Quy tắc: **dùng component AntD có sẵn**, chỉ chỉnh bằng theme token; chỉ viết component riêng khi AntD không có.

| Nhu cầu | Component AntD | Ghi chú phong cách Canopy |
|---|---|---|
| Khung trang | `Layout` + `Sider` (64 px, thu gọn icon) + `Header` 64 px | Sider nền gradient teal, icon trắng, mục đang chọn = ô trắng bo 12, icon teal |
| Banner tiêu đề | riêng: `PageHero` (breadcrumb + tiêu đề + số đếm xám) | nền `hero-mist` nhạt, bo 20, cao 120–160 |
| Bảng | `Table` (size middle, hàng 48) | tiêu đề cột nền `surface-muted`; không viền dọc; dòng chọn `surface-selected` |
| Lọc | `Input.Search`, `Select`, `DatePicker.RangePicker`, `Segmented`, chip lọc = `Tag.CheckableTag` | ô nhập tô xám, không viền |
| Trạng thái | riêng: `StatusPill` (đọc `status.json`) | bo 6, cao 24, chữ 12/500 |
| Biểu mẫu | `Form` dọc, `Input`, `Select`, `TimePicker`, `Switch`, `Checkbox` | tối đa rộng 480 trong `Drawer`/`Modal` |
| Thông báo | `message`, `notification`, `Modal.confirm` | xác nhận thao tác nguy hiểm (nghỉ việc, xoá dữ liệu khuôn mặt) |
| Thẻ số | riêng: `KpiTile` (số Be Vietnam Pro 28 + nhãn 12) | nền `surface-muted`, bo 12 |
| Lịch tháng | `Calendar` (fullscreen=false ở `/me`) | ô ngày tô theo nhóm trạng thái |
| Tab | `Tabs` | gạch chân teal 2 px |
| Trống / lỗi / đang tải | `Empty`, `Result`, `Skeleton`, `Spin` | chữ tiếng Việt, kèm nút hành động |

Locale: `ConfigProvider locale={viVN}` + dayjs `vi`. Icon: **Lucide** (`lucide-react`) 20 px nét 1,5; rail dùng 24 px.

### 6.2 Kiosk — React Native + theme `kiosk-theme.json`
| Component | Mô tả |
|---|---|
| `ScanFrame` | khung oval bo 44, viền 4 px; IDLE: trắng 60%; TRACKING: lime; vệt quét (gradient lime 0→40%) chạy dọc 1,6 s lặp |
| `HintBar` | thanh mờ đen 60% phía dưới khung, chữ trắng 24/500, nội dung theo `state` |
| `ResultPanel` | khối toàn màn hình theo nhóm success / progress / error / danger-strong; icon lớn 96, tên 56/600, dòng phụ 28 |
| `ClockBadge` | giờ lớn 40 tabular + tên cửa + chấm kết nối (xanh/đỏ) |
| `ResearchBanner` | dải nhỏ góc dưới: "Bản trình diễn nghiên cứu – không dùng thương mại" (chữ 13, nền trắng 70%) |
| `PinPad` | 12 phím tròn 80 px, chấm PIN 4 ô |
| `PillButton` | inverse (mực, chữ trắng) cho hành động chính; secondary (trắng, bóng 1); danger (đỏ) |
| `ProgressDots` | 5 chấm tiến độ chụp mẫu (lime khi xong) |
| `SearchPill` + `ListRow` | tìm và chọn NV (K-06) |

Icon kiosk: **Phosphor** (`phosphor-react-native`) — Regular cho giao diện, Fill cho icon kết quả.

## 7. Chuyển động
**Web — GSAP** (skill `gsap` của greensock/gsap-skills; dùng `@gsap/react` `useGSAP`):
| Chỗ | Hiệu ứng | Thời lượng |
|---|---|---|
| Chuyển trang | nội dung fade + trượt lên 8 px | 280 ms, `power2.out` |
| Danh sách/bảng nạp xong | các hàng xuất hiện lệch nhau (stagger 20 ms, tối đa 10 hàng đầu) | 180 ms |
| KPI (W-02) | đếm số từ 0 tới giá trị khi mở trang | 600 ms |
| **W-10 Giám sát** | event mới trượt vào đầu danh sách + nháy nền theo nhóm màu 1 lần; cảnh báo SPOOF rung nhẹ 2 lần | 320 ms |
| E-02 Hôm nay | thẻ giờ vào/ra "lật" khi có lượt chấm mới | 400 ms |
| Hover/nhấn | để AntD tự xử lý (không thêm GSAP) | — |
Không dùng GSAP cho bảng/biểu mẫu thường ngoài các chỗ trên.

**Kiosk — Reanimated** (skill animations trong `react-native-best-practices` của Software Mansion):
| Chỗ | Hiệu ứng | Thời lượng |
|---|---|---|
| `ScanFrame` IDLE → TRACKING | viền đổi màu trắng → lime + co nhẹ 0,98 | 200 ms, easing nhấn `(.3,0,0,1.2)` |
| Vệt quét | chạy dọc lặp | 1,6 s |
| OK | `ResultPanel` phóng từ 0,9 → 1 + dấu ✓ vẽ nét | 320 ms |
| DENY / SPOOF | rung ngang ±12 px 3 lần | 300 ms |
| ALREADY | fade in | 200 ms |
| Hết 3 s | panel mờ dần về K-02 | 320 ms |
| Chụp mẫu (K-08) | chấm tiến độ "bung" khi nhận mẫu | 200 ms |
Bật **giảm chuyển động** của hệ điều hành → bỏ rung/phóng, chỉ đổi màu.

## 8. Âm thanh (Kiosk)
3 âm ngắn ≤ 0,5 s: OK (2 nốt đi lên), DENY/SPOOF (1 nốt trầm), ALREADY (1 nốt nhẹ). File tự tạo hoặc nguồn có giấy phép tự do; ghi nguồn trong `kiosk/assets/sounds/NGUON.md`.

## 9. Mẫu mô tả một màn hình (`ui/man-hinh/*.md`)
Mỗi màn có đúng các mục: **Mục đích · Vai trò · Bố cục (vùng từ trên xuống / trái sang phải) · Thành phần · Dữ liệu (endpoint/WS) · Hành động · Trạng thái (đang tải / trống / lỗi / không có quyền) · Chuyển động · Chữ hiển thị chính (tiếng Việt)**.
