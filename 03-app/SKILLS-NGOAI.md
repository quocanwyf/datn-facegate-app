# SKILL NGOÀI CHO CODEX — danh sách và cách cài (task T00)
> Nguồn: nghiên cứu của An `03-app/setup-skill-repo/Skill repo cho dự án Chấm công + Ra vào (Codex).md` (14/11/2026). Codex đọc skill trong `.agents/skills/` của từng cấp thư mục từ thư mục đang làm việc lên tới gốc repo (tài liệu Codex, đã đối chiếu 14/11/2026).
> **Skill riêng của dự án** (đã commit sẵn): `hub-rules`, `api-contract`, `kiosk-ws-protocol`, `cham-cong-vn`.

## Cách cài (Codex làm ở T00, trên máy Hy)
1. Trong Codex (chế độ Local, thư mục gốc repo), gọi skill hệ thống `$skill-installer` cho từng dòng bảng dưới, yêu cầu **cài vào `.agents/skills/` của repo** (không cài vào thư mục người dùng) để mọi người clone repo đều có.
2. Trước khi cài từ `openai/skills`: mở README của repo đó xem còn hoạt động hay đã chuyển chỗ (có nguồn nói đã ngừng phát triển — **chưa xác minh**). Repo nào không còn / không có skill đúng tên → **bỏ qua, ghi vào báo cáo T00**, không tìm skill thay thế.
3. Sau khi cài: mỗi skill là một thư mục có `SKILL.md` (frontmatter `name`, `description`). Ghi vào `.agents/skills/NGUON.md`: tên skill · repo · đường dẫn · commit/ngày lấy · giấy phép.
4. Khởi động lại Codex để nhận skill mới; commit thư mục `.agents/skills/`.

## Danh sách
| # | Skill | Repo (đường dẫn) | Dùng ở | Ghi chú |
|---|---|---|---|---|
| 1 | playwright | `openai/skills` | T07, T10–T12 (E2E web) | |
| 2 | screenshot(s) | `openai/skills` | T07–T12, T15 (chụp màn kiểm tra + tư liệu quyển) | |
| 3 | security review | `openai/skills` | T06, T14 (JWT, RBAC, device token, dữ liệu khuôn mặt) | |
| 4 | fastapi | `fastapi/fastapi` (skill trong repo chính thức) | T03–T06, T09, T11 | |
| 5 | supabase-postgres-best-practices | `supabase/agent-skills` → `skills/supabase-postgres-best-practices` | T03 | Bỏ qua phần RLS (dự án phân quyền ở API) |
| 6 | react-best-practices | `vercel-labs/agent-skills` → `skills/react-best-practices` | T07, T10–T12 | Bỏ qua luật RSC/SSR (Vite SPA) |
| 7 | web-design-guidelines | `vercel-labs/agent-skills` | T07, T10–T12 | |
| 8 | gsap (bộ chính thức) | `greensock/gsap-skills` | T07, T11, T12 | Chỉ ở các chỗ `ui/design-system.md` §7 |
| 9 | bộ skill Expo | `expo/skills` | T08 | Có bản cho Codex |
| 10 | vercel-react-native-skills | `vercel-labs/agent-skills` | T08 | |
| 11 | react-native-best-practices (phần animations) | `software-mansion-labs/skills` → `skills/react-native-best-practices` | T08 | Reanimated cho Kiosk |

Không cài skill `create-plan`: plan đã có sẵn trong `03-app/plan-codex/`.
