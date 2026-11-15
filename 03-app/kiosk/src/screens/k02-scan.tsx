import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CameraFeed } from '../camera/CameraFeed';
import { ErrorNotice, PillButton, ResearchBanner, styles } from '../components/controls';
import { ProgressDots, ScanFrame } from '../components/scan-frame';
import { fonts, hint, theme, time } from '../theme';
import type { KioskSocket } from '../ws/KioskSocket';
import type { Config, FrameMode, FrameState, Progress } from '../ws/protocol';
const poses = ['Nhìn thẳng', 'Hơi quay sang trái', 'Hơi quay sang phải', 'Hơi ngẩng đầu', 'Hơi cúi đầu'];
const reasons: Record<string, string> = { NO_FACE: 'Không thấy khuôn mặt', MULTI_FACE: 'Có nhiều khuôn mặt trong khung', TOO_SMALL: 'Khuôn mặt quá nhỏ — lại gần hơn', POSE: 'Nghiêng quá nhiều — nhìn theo hướng dẫn', SPOOF: 'Không xác thực được khuôn mặt thật', TOO_SIMILAR: 'Tư thế gần giống mẫu trước — đổi hướng một chút' };
export function K02Scan({ socket, config, connected, state, onEnroll, onSent, enroll, progress, error, onCancel, onRetry }: { socket: KioskSocket; config: Config; connected: boolean; state?: FrameState; onEnroll: () => void; onSent: (at: number) => void; enroll?: Extract<FrameMode, { mode: 'enroll' }>; progress?: Progress; error?: string; onCancel: () => void; onRetry: () => void }) {
  const insets = useSafeAreaInsets();
  const [now, setNow] = useState(Date.now()); const [serverOffset, setServerOffset] = useState(0);
  useEffect(() => { const offset = Date.parse(config.server_time) - Date.now(); setServerOffset(Number.isFinite(offset) ? offset : 0); }, [config.server_time]);
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  const accepted = progress?.accepted ?? 0;
  const text = enroll ? progress?.reason ? reasons[progress.reason] : poses[Math.min(accepted, 4)] : hint(state?.state ?? 'NO_FACE');
  return <View style={{ flex: 1, backgroundColor: theme.color.inverse }}>
    <CameraFeed socket={socket} mode={enroll ?? { mode: 'recognize' }} active={connected && !error} bbox={state?.bbox} onSent={onSent} />
    <ScanFrame tracking={enroll ? accepted > 0 : ['CHECKING', 'HOLD_STILL'].includes(state?.state ?? '')} checking={state?.state === 'CHECKING'} />
    <View style={local.clock}><Text style={local.time}>{time(new Date(now + serverOffset).toISOString())}</Text><Text style={local.gate}>{config.gate.name}</Text><View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}><View style={[local.connection, { backgroundColor: connected ? theme.color.connOk : theme.color.accent }]} /><Text style={local.small}>{connected ? 'Đã kết nối Hub' : 'Đang nối lại…'}</Text></View></View>
    {enroll ? <><View style={local.cancel}><PillButton title="Huỷ" secondary onPress={onCancel} /></View><View style={local.progress}><ProgressDots accepted={accepted} /></View></> : <Pressable accessibilityRole="button" accessibilityLabel="Giữ 3 giây để mở chế độ đăng ký" testID="enroll-entry" onLongPress={onEnroll} delayLongPress={3000} style={local.secret} />}
    <View style={local.hint}><Text style={local.hintText}>{text ?? 'Nhìn trực tiếp vào camera'}</Text>{error ? <View style={[styles.card, { padding: 16 }]}><ErrorNotice message={error} /><PillButton title="Thử đăng ký lại" onPress={onRetry} /></View> : null}</View>
    <View style={[local.research, { bottom: 20 + insets.bottom, right: 24 + insets.right }]}><ResearchBanner text={config.research_banner} /></View>
  </View>;
}
export const K08Enroll = K02Scan;
const local = StyleSheet.create({ clock: { position: 'absolute', left: 32, top: 24, backgroundColor: theme.color.scrim, borderRadius: 24, padding: 20, gap: 8 }, time: { color: theme.color.onInverse, fontSize: theme.type.clock.size, fontFamily: fonts.semibold, fontVariant: ['tabular-nums'] }, gate: { color: theme.color.onInverse, fontFamily: fonts.medium, fontSize: 18 }, small: { color: theme.color.onInverse, fontSize: 14, fontFamily: fonts.regular }, connection: { width: 9, height: 9, borderRadius: 5 }, secret: { position: 'absolute', right: 0, top: 0, width: 96, height: 96 }, cancel: { position: 'absolute', left: 32, top: 190 }, progress: { position: 'absolute', top: 24, alignSelf: 'center' }, hint: { position: 'absolute', left: '22%', right: '22%', bottom: '12%', backgroundColor: theme.color.scrim, padding: 20, borderRadius: 24, alignItems: 'center', gap: 12 }, hintText: { fontFamily: fonts.medium, fontSize: theme.type.hint.size, color: theme.color.onInverse, textAlign: 'center' }, research: { position: 'absolute', bottom: 20, right: 24 } });
