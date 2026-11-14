# Skill repo cho dự án Chấm công + Ra vào (Codex)

Nov 14, 2026 · @an

Claude lên plan, Codex code chính. Mọi repo dưới đây theo chuẩn Agent Skills (file `SKILL.md`), nên Codex dùng được trực tiếp. Skill để trong thư mục `.agents/skills/` của repo thì cả nhóm chạy Codex đều có. Hướng dẫn chính thức: [Using skills in Codex](https://developers.openai.com/codex/skills).

## 1. Dùng chung (UI, kiểm thử, viết skill)

Kho chính là openai/skills, kho chính thức của OpenAI cho Codex. Codex đã có sẵn skill-creator và skill-installer, nên không cần lấy skill-creator của Anthropic.

| Repo | Skill | Dùng cho |
| --- | --- | --- |
| [openai/skills](https://github.com/openai/skills) | playwright | Kiểm thử Web Admin và trang `/me` |
| [openai/skills](https://github.com/openai/skills) | screenshot(s) | Chụp màn hình UI để kiểm tra |
| [openai/skills](https://github.com/openai/skills) | security review | Rà JWT, RBAC, token thiết bị, dữ liệu sinh trắc |
| [openai/skills](https://github.com/openai/skills/tree/main/skills/.experimental/create-plan) | create-plan (experimental) | Lập kế hoạch trước khi code |

Có nguồn ghi openai/skills đã ngừng phát triển, chuyển sang kho OpenAI Plugins. Trước khi dùng, nên mở README xem link mới.

## 2. Hub (FastAPI + PyTorch + PostgreSQL)

| Repo | Skill | Dùng cho |
| --- | --- | --- |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) ([trang skill](https://claudemarketplaces.com/skills/fastapi/fastapi/fastapi)) | fastapi | Code FastAPI và Pydantic theo bản mới nhất, skill nằm trong repo chính thức |
| [supabase/agent-skills](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices) | supabase-postgres-best-practices | Index, kiểu dữ liệu, schema, kết nối cho Postgres nói chung |

Phần RLS của skill Postgres có thể bỏ qua, vì dự án phân quyền bằng RBAC ở tầng API. SQLAlchemy 2, Alembic, PyTorch và APScheduler chưa có skill chính thức đáng tin, nên các luật này ghi vào skill riêng (mục 5) và `hub/AGENTS.md`.

## 3. Web (/admin và /me: React 18 + Vite + Ant Design)

| Repo | Skill | Dùng cho |
| --- | --- | --- |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | react-best-practices | Hiệu năng React; bỏ qua các luật RSC/SSR vì Vite là SPA |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | web-design-guidelines | Rà UI và accessibility |
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | gsap (bộ chính thức) | Animation web: màn giám sát realtime, trang So sánh mô hình, màn check-in ở `/me` |

Các màn bảng và biểu mẫu của admin dùng hiệu ứng có sẵn của Ant Design là đủ. Ant Design chưa có skill chính thức, nên quy ước (theme token, locale `vi_VN`, ưu tiên Table/Form của AntD) ghi vào `web/AGENTS.md`.

## 4. Kiosk (Expo dev build + React Native)

| Repo | Skill | Dùng cho |
| --- | --- | --- |
| [expo/skills](https://github.com/expo/skills) | bộ skill chính thức của Expo | Build, debug, nâng cấp SDK, deploy; có bản cho Codex |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | vercel-react-native-skills | Best practices để app React Native và Expo chạy mượt |
| [software-mansion-labs/skills](https://github.com/software-mansion-labs/skills/tree/main/skills/react-native-best-practices/references/animations) | animations (trong react-native-best-practices) | Animation cho Kiosk, vai trò như GSAP bên web: Reanimated 4, Gesture Handler, SVG |

Software Mansion là đội làm ra Reanimated, nên skill animation này theo đúng cách dùng thư viện của họ. Dùng cho khung oval quét mặt, hiệu ứng ✓ khi nhận diện đúng, rung khi bị từ chối và chuyển màn mượt. react-native-vision-camera chưa có skill chính thức, nên cấu hình camera và cách gửi khung hình ghi vào `kiosk/AGENTS.md`.

## 5. Skill riêng của dự án (tự viết)

Các luật riêng của đặc tả không repo nào có sẵn. Viết bằng skill-creator có sẵn trong Codex, để trong `.agents/skills/` của repo.

| Skill | Nội dung |
| --- | --- |
| hub-rules | R-21: event loop không bao giờ chạy PyTorch, mọi việc suy luận đi qua hàng đợi tới một worker. Không sửa `vendor/`, phải qua `test_vendor_hash.py`. `recognition_event` chỉ thêm, `attendance_day` tính lại bằng `recompute_day` |
| api-contract | `openapi/openapi.yaml` là nguồn gốc. Client TS cho web và kiosk sinh từ file này, không viết type tay |
| kiosk-ws-protocol | Gửi khung kiểu dừng-và-chờ, định dạng message WSS, xử lý mất kết nối |
| cham-cong-vn | Ca cố định, ngày lễ VN, giải trình, chấm công hộ, cột trong file Excel tháng |

Thêm một `AGENTS.md` ở gốc `03-app/` và một file trong mỗi thư mục `hub/`, `web/`, `kiosk/`. Codex đọc file này mỗi lần làm việc trong thư mục đó, nên đây là chỗ ghi các luật quan trọng nhất.
