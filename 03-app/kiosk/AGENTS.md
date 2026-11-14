# AGENTS.md — Kiosk App (Expo + React Native)

Đọc thêm skill `kiosk-ws-protocol`, `api-contract` và skill ngoài: bộ `expo/skills`, `vercel-react-native-skills`, animations (Software Mansion) — xem `03-app/SKILLS-NGOAI.md`.

## Stack
Expo SDK mới nhất ổn định (**dev build**, không dùng Expo Go vì cần native camera) · TypeScript strict · `react-native-vision-camera` (camera + đọc QR) · `react-native-reanimated` · `expo-secure-store` · `expo-av` hoặc `expo-audio` (âm thanh) · `expo-font` + `@expo-google-fonts/inter` · `phosphor-react-native` · client REST sinh từ `openapi.yaml` (`openapi-typescript` + `openapi-fetch`).

## Chạy trên máy ảo Android (không cần điện thoại)
1. Android Studio → Device Manager → tạo AVD **tablet ngang** (vd. Pixel Tablet, API 34+).
2. Sửa AVD → Advanced → **Camera Front = Webcam0** (lấy webcam laptop), Camera Back = Emulated.
3. Hub chạy trên cùng máy: địa chỉ từ máy ảo là `http://10.0.2.2:8000`.
4. Cho phép HTTP thường (bản demo): cấu hình `usesCleartextTraffic` qua config plugin `expo-build-properties` (android).
5. `npx expo prebuild` → `npx expo run:android`.

## Cấu trúc
```
kiosk/src/
  api/        # schema.d.ts (sinh tự động), rest.ts
  ws/         # KioskSocket: auth, dừng-và-chờ, ping, nối lại lùi dần
  camera/     # chụp khung → JPEG cạnh dài 640, q80 (theo config từ Hub)
  screens/    # K01Pair, K02Scan, K04Result, K05Pin, K06Pick, K07Consent, K08Enroll, K09Sent, K11Offline
  theme/      # = 03-app/ui/tokens/kiosk-theme.json, status.json
  components/ # ScanFrame, HintBar, ResultPanel, ClockBadge, PinPad, PillButton, ProgressDots, ResearchBanner
```

## Luật
1. Theo đúng giao thức `03-app/openapi/ws-protocol.md`: auth bằng message đầu, **dừng-và-chờ** (không gửi khung mới khi chưa nhận phản hồi), không gửi khung trong lúc hiện kết quả.
2. **Không hiển thị ảnh khuôn mặt** ở bất kỳ màn nào (chỉ preview camera trực tiếp).
3. Không xử lý AI trên máy: Kiosk chỉ chụp, nén, gửi; mọi quyết định do Hub.
4. Token thiết bị lưu `expo-secure-store`; bị `DEVICE_REVOKED` → xoá, về K-01.
5. Theme + nhãn trạng thái chỉ lấy từ `theme/` (bản sao `ui/tokens/`). Lime chỉ tô nền, chữ trên lime là mực.
6. Animation theo `design-system.md` §7 bằng Reanimated (chạy trên UI thread); tôn trọng giảm chuyển động của hệ thống.
7. Mỗi màn theo `03-app/ui/man-hinh/kiosk.md`.
