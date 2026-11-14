# Nguồn skill ngoài — T00

Ngày lấy: 14/11/2026. Cài bằng skill-installer, pin theo commit; giữ nguyên nội dung upstream. Các skill mới sẽ được Codex khám phá ở lượt kế tiếp; có thể đọc file trực tiếp khi cần trước thời điểm đó.

Theo SKILLS-NGOAI.md: bỏ qua nhóm openai/skills (playwright, screenshot, security review) vì README tại commit 49f948faa9258a0c61caceaf225e179651397431 công bố repository deprecated ([README đã đối chiếu](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md)). Không tìm nguồn thay thế. Playwright package đã dùng trong web không đồng nghĩa đã cài skill.

| Repo | Commit | Đường dẫn đã cài | Giấy phép nguồn |
|---|---|---|---|
| fastapi/fastapi | 5758a9c8347d911444dca97a55b708cc4a8de4f8 | .agents/skills/fastapi | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) |
| supabase/agent-skills | c9be0e931b7930f7d02126d04774d904c381e7d7 | .agents/skills/supabase-postgres-best-practices | [MIT](https://github.com/supabase/agent-skills/blob/main/LICENSE) |
| vercel-labs/agent-skills | 1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62 | .agents/skills/react-best-practices<br>.agents/skills/web-design-guidelines<br>.agents/skills/react-native-skills | react-best-practices/react-native-skills khai báo MIT trong frontmatter; web-design-guidelines không khai báo license riêng, giữ [nguồn](https://github.com/vercel-labs/agent-skills/tree/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62) để đối chiếu |
| greensock/gsap-skills | aed9cfd3277740755f6bfc1155c7aa645403b760 | .agents/skills/gsap-core<br>.agents/skills/gsap-frameworks<br>.agents/skills/gsap-performance<br>.agents/skills/gsap-plugins<br>.agents/skills/gsap-react<br>.agents/skills/gsap-scrolltrigger<br>.agents/skills/gsap-timeline<br>.agents/skills/gsap-utils | [MIT](https://github.com/greensock/gsap-skills/blob/main/LICENSE) |
| expo/skills | 7582922d039d5a96dc574757d399d22d56370f2b | .agents/skills/eas-app-stores<br>.agents/skills/eas-hosting<br>.agents/skills/eas-observe<br>.agents/skills/eas-simulator<br>.agents/skills/eas-update-insights<br>.agents/skills/eas-update<br>.agents/skills/eas-workflows<br>.agents/skills/expo-animation<br>.agents/skills/expo-app-clip<br>.agents/skills/expo-brownfield<br>.agents/skills/expo-data-fetching<br>.agents/skills/expo-design-system<br>.agents/skills/expo-dev-client<br>.agents/skills/expo-dom<br>.agents/skills/expo-examples<br>.agents/skills/expo-module<br>.agents/skills/expo-native-ui<br>.agents/skills/expo-overview<br>.agents/skills/expo-project-structure<br>.agents/skills/expo-router<br>.agents/skills/expo-ui<br>.agents/skills/expo-upgrade<br>.agents/skills/expo-web-to-native | [MIT](https://github.com/expo/skills/blob/main/LICENSE) |
| software-mansion-labs/skills | 43cde80af628d103647c13bde07975d0b21b8419 | .agents/skills/react-native-best-practices | [MIT theo frontmatter SKILL.md](https://github.com/software-mansion-labs/skills/blob/43cde80af628d103647c13bde07975d0b21b8419/skills/react-native-best-practices/SKILL.md) |

react-native-skills là thư mục upstream của bộ Vercel React Native nêu trong kế hoạch; không đổi tên skill hoặc tìm bộ thay thế. GSAP và Expo được cài theo các thư mục hiện có trong bộ chính thức, không cài skill nội bộ .claude/experiments.

Log discovery/cài đặt: 03-app/ket-qua-kiem-thu/2026-11-14_T00/skill-sources.json, skill-install-results.json và install-*.log. Không sửa hướng dẫn/nguồn chuẩn khi cài.
