import { useEffect, useRef, useState } from 'react';
import { AppState, Linking, ScrollView, Text, View } from 'react-native';
import { Camera, useCameraDevice, useCameraPermission } from 'react-native-vision-camera';
import { useBarcodeScannerOutput } from 'react-native-vision-camera-barcode-scanner';
import { ErrorNotice, Field, PillButton, ResearchBanner, styles } from '../components/controls';
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withTiming } from 'react-native-reanimated';
import { PairingCode } from '../components/pairing-code';

export function K01Pair({ onPair, busy, error }: { onPair: (hub: string, code: string) => void; busy: boolean; error: string }) {
  const [hub, setHub] = useState('http://10.0.2.2:8000'); const [code, setCode] = useState('');
  const permission = useCameraPermission(); const device = useCameraDevice('front'); const lastQr = useRef('');
  const [foreground, setForeground] = useState(AppState.currentState === 'active');
  const [cameraError, setCameraError] = useState(false);
  useEffect(() => { const listener = AppState.addEventListener('change', state => { setForeground(state === 'active'); if (state === 'active') setCameraError(false); }); return () => listener.remove(); }, []);
  const reduced = useReducedMotion(); const opacity = useSharedValue(0);
  useEffect(() => { opacity.set(withTiming(1, { duration: reduced ? 0 : 200 })); return () => cancelAnimation(opacity); }, [opacity, reduced]);
  const cardMotion = useAnimatedStyle(() => ({ opacity: opacity.get() }));
  const barcode = useBarcodeScannerOutput({ barcodeFormats: ['qr-code'], onBarcodeScanned: values => {
    for (const value of values) {
      const raw = value.rawValue; value.dispose(); if (!raw || raw === lastQr.current || busy) continue;
      try { const data: unknown = JSON.parse(raw); if (data && typeof data === 'object' && 'hub' in data && 'code' in data && typeof data.hub === 'string' && typeof data.code === 'string' && /^\d{6}$/.test(data.code)) { lastQr.current = raw; setHub(data.hub); setCode(data.code); onPair(data.hub, data.code); } } catch { /* QR không thuộc FaceGate không gửi lên Hub. */ }
    }
  }, onError: () => { /* Vẫn cho nhập tay khi đọc QR không được. */ } });
  return <ScrollView style={styles.page} contentContainerStyle={{ alignItems: 'center', paddingBottom: 32, gap: 24 }} keyboardShouldPersistTaps="handled" contentInsetAdjustmentBehavior="automatic">
    <Animated.View style={[styles.card, { width: 560, maxWidth: '100%', marginTop: 16 }, cardMotion]}>
      <Text style={styles.title}>Ghép thiết bị</Text><Text style={styles.text}>Quét mã QR hoặc nhập mã do Chủ doanh nghiệp tạo trên trang quản trị.</Text>
      <View style={{ height: 240, width: 320, alignSelf: 'center', overflow: 'hidden', borderRadius: 16 }}>
        {permission.hasPermission && device ? cameraError ? <PillButton title="Thử camera lại" secondary onPress={() => setCameraError(false)} /> : <Camera style={{ flex: 1 }} device={device} outputs={[barcode]} isActive={!busy && foreground} onError={() => setCameraError(true)} mirrorMode="auto" /> : <PillButton title={permission.canRequestPermission ? 'Cho phép camera quét QR' : 'Mở cài đặt camera'} secondary onPress={() => { void (permission.canRequestPermission ? permission.requestPermission() : Linking.openSettings()); }} />}
      </View><Text style={[styles.muted, { textAlign: 'center' }]}>hoặc nhập tay</Text>
      <Field label="Địa chỉ Hub" value={hub} onChange={setHub} editable={!busy} testID="pair-hub" />
      <PairingCode value={code} onChange={setCode} editable={!busy} error={error} />
      <ErrorNotice message={error} /><PillButton title="Ghép thiết bị" busy={busy} disabled={code.length !== 6 || !hub.trim()} onPress={() => onPair(hub, code)} testID="pair-submit" />
    </Animated.View><ResearchBanner />
  </ScrollView>;
}
