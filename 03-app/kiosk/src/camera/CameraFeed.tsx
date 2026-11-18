import { useEffect, useRef, useState } from 'react';
import { AppState, Linking, StyleSheet, Text, View } from 'react-native';
import { Camera, useCameraDevice, useCameraPermission, type CameraRef } from 'react-native-vision-camera';
import type { Image } from 'react-native-nitro-image';
import { PillButton, styles } from '../components/controls';
import { theme } from '../theme';
import type { KioskSocket } from '../ws/KioskSocket';
import type { FrameMode, FrameState } from '../ws/protocol';

export function CameraFeed({ socket, mode, active, captureEnabled = true, bbox, onSent }: { socket: KioskSocket; mode: FrameMode; active: boolean; captureEnabled?: boolean; bbox?: FrameState['bbox']; onSent?: (at: number) => void }) {
  const device = useCameraDevice('front'); const permission = useCameraPermission(); const camera = useRef<CameraRef>(null);
  const [ready, setReady] = useState(false); const [foreground, setForeground] = useState(AppState.currentState === 'active'); const [error, setError] = useState('');
  const [imageSize, setImageSize] = useState({ width: 640, height: 400 }); const [viewSize, setViewSize] = useState({ width: 1, height: 1 });
  const modeKey = mode.mode === 'enroll' ? `${mode.enroll_session_id}/${mode.employee_id}` : 'recognize';
  const modeRef = useRef(mode); modeRef.current = mode;
  const currentScope = useRef(modeKey); currentScope.current = modeKey;
  const canCapture = active && foreground && captureEnabled;
  const activeRef = useRef(canCapture); activeRef.current = canCapture;
  useEffect(() => { const subscription = AppState.addEventListener('change', state => setForeground(state === 'active')); return () => subscription.remove(); }, []);
  useEffect(() => {
    let cancelled = false; let timer: ReturnType<typeof setTimeout>;
    async function capture() {
      if (cancelled) return;
      const config = socket.config;
      if (canCapture && ready && !error && camera.current && config && socket.canSend(modeRef.current.mode)) {
        const capturedMode = modeRef.current;
        let snapshot: Image | undefined; let resized: Image | undefined;
        try {
          snapshot = await camera.current.takeSnapshot();
          const scale = Math.min(1, config.frame_long_side / Math.max(snapshot.width, snapshot.height));
          resized = await snapshot.resizeAsync(Math.max(1, Math.round(snapshot.width * scale)), Math.max(1, Math.round(snapshot.height * scale)));
          const encoded = await resized.toEncodedImageDataAsync('jpg', config.jpeg_quality);
          if (!cancelled && activeRef.current && currentScope.current === modeKey && socket.sendFrame(encoded.buffer, capturedMode)) {
            setImageSize({ width: encoded.width, height: encoded.height });
            onSent?.(Date.now());
            if (capturedMode.mode === 'enroll') return;
          }
        } catch { if (!cancelled) setError('Không lấy được khung camera. Vui lòng thử lại.'); }
        finally { resized?.dispose(); snapshot?.dispose(); }
      }
      if (!cancelled) timer = setTimeout(() => void capture(), 50);
    }
    void capture(); return () => { cancelled = true; clearTimeout(timer); };
  }, [socket, modeKey, canCapture, ready, error, onSent]);
  if (!permission.hasPermission) return <View style={local.permission}><Text style={styles.title}>Cần quyền camera</Text><Text style={styles.text}>Cho phép camera để ghép thiết bị và quét khuôn mặt.</Text><PillButton title={permission.canRequestPermission ? 'Cấp quyền camera' : 'Mở cài đặt'} onPress={() => { void (permission.canRequestPermission ? permission.requestPermission() : Linking.openSettings()); }} /></View>;
  if (!device) return <View style={local.permission}><Text style={styles.title}>Không tìm thấy camera trước</Text><Text style={styles.text}>Kiểm tra camera của tablet hoặc máy ảo.</Text></View>;
  return <View style={StyleSheet.absoluteFill} onLayout={event => setViewSize(event.nativeEvent.layout)}>
    <Camera ref={camera} style={StyleSheet.absoluteFill} device={device} isActive={active && foreground && !error} mirrorMode="on" onPreviewStarted={() => setReady(true)} onPreviewStopped={() => setReady(false)} onError={() => setError('Không mở được camera. Kiểm tra quyền và thử lại.')} />
    {bbox && !error ? <View pointerEvents="none" style={{ position: 'absolute', left: bbox[0] / imageSize.width * viewSize.width, top: bbox[1] / imageSize.height * viewSize.height, width: bbox[2] / imageSize.width * viewSize.width, height: bbox[3] / imageSize.height * viewSize.height, borderColor: theme.color.primary, borderWidth: 1 }} /> : null}
    {error ? <View style={local.permission}><Text style={styles.text}>{error}</Text><PillButton title="Thử camera lại" onPress={() => setError('')} /></View> : null}
  </View>;
}
const local = StyleSheet.create({ permission: { flex: 1, backgroundColor: theme.color.bg, justifyContent: 'center', alignItems: 'center', gap: 24, padding: 32 } });
