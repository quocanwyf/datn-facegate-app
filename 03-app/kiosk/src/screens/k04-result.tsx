import { useEffect } from 'react';
import { StyleSheet, Text } from 'react-native';
import { CheckCircle } from 'phosphor-react-native/src/icons/CheckCircle';
import { ClockCounterClockwise } from 'phosphor-react-native/src/icons/ClockCounterClockwise';
import { DoorOpen } from 'phosphor-react-native/src/icons/DoorOpen';
import { Prohibit } from 'phosphor-react-native/src/icons/Prohibit';
import { ShieldWarning } from 'phosphor-react-native/src/icons/ShieldWarning';
import { XCircle } from 'phosphor-react-native/src/icons/XCircle';
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { fonts, status, theme, time } from '../theme';
import type { Result } from '../ws/protocol';
import { DrawnCheck } from '../components/drawn-check';
import { StatusChip } from '../components/status-chip';
export function K04Result({ result, seconds }: { result: Result; seconds: number }) {
  const reduced = useReducedMotion(); const scale = useSharedValue(result.result === 'OK' && !reduced ? .9 : 1); const x = useSharedValue(0); const remaining = useSharedValue(1);
  const opacity = useSharedValue(result.result === 'ALREADY' && !reduced ? 0 : 1);
  const ok = useAudioPlayer(require('../../assets/sounds/ok.wav')); const deny = useAudioPlayer(require('../../assets/sounds/deny.wav')); const already = useAudioPlayer(require('../../assets/sounds/already.wav'));
  const player = result.result === 'OK' ? ok : result.result === 'ALREADY' ? already : deny;
  const audio = useAudioPlayerStatus(player);
  const key = result.result === 'DENY' ? `DENY:${result.reason}` : result.result;
  const candidate = (status.enums['kiosk.display'] as Record<string, { group: string } | string>)[key];
  const entry = typeof candidate === 'object' ? candidate : undefined;
  const colors = (status.groups as Record<string, { kiosk?: { bg: string; fg: string } }>)[entry?.group ?? 'error']?.kiosk ?? { bg: theme.color.danger, fg: theme.color.onDanger };
  useEffect(() => {
    scale.set(withTiming(1, { duration: reduced ? 0 : 320 })); remaining.set(withTiming(0, { duration: seconds * 1000 }));
    opacity.set(withSequence(withTiming(1, { duration: result.result === 'ALREADY' && !reduced ? 200 : 0 }), withDelay(Math.max(0, seconds * 1000 - 320 - (result.result === 'ALREADY' && !reduced ? 200 : 0)), withTiming(reduced ? 1 : 0, { duration: reduced ? 0 : 320 }))));
    if (result.result === 'DENY' && !reduced) x.set(withRepeat(withSequence(withTiming(12, { duration: 25 }), withTiming(-12, { duration: 50 }), withTiming(0, { duration: 25 })), 3, false));
    return () => { cancelAnimation(scale); cancelAnimation(x); cancelAnimation(remaining); cancelAnimation(opacity); };
  }, [result, seconds, reduced, scale, x, remaining, opacity]);
  useEffect(() => {
    if (!audio.isLoaded) return;
    let active = true; player.volume = .35;
    void player.seekTo(0).then(() => { if (active) player.play(); }).catch(() => {});
    return () => { active = false; };
  }, [player, audio.isLoaded]);
  const panelStyle = useAnimatedStyle(() => ({ opacity: opacity.get() }));
  const animated = useAnimatedStyle(() => ({ transform: [{ scale: scale.get() }, { translateX: x.get() }] })); const countdown = useAnimatedStyle(() => ({ transform: [{ scaleX: remaining.get() }] }));
  const Icon = result.result === 'ALREADY' ? ClockCounterClockwise : result.result === 'OK' ? result.attendance?.kind === 'NONE' ? DoorOpen : CheckCircle : result.reason === 'SPOOF' ? ShieldWarning : result.reason === 'RULE' || result.reason === 'INACTIVE' ? Prohibit : XCircle;
  const headline = result.employee?.name ?? (result.reason === 'SPOOF' ? 'Không thể xác thực' : 'Không nhận diện được');
  const detail = result.result === 'ALREADY' ? `Đã ghi nhận lúc ${time(result.attendance?.time)}` : result.result === 'OK' ? result.attendance?.kind === 'IN' ? `Vào ${time(result.attendance.time)}` : result.attendance?.kind === 'OUT' ? `Ra ${time(result.attendance.time)}` : 'Mời vào' : result.reason === 'RULE' ? 'Bạn không được phép vào khu vực này' : result.reason === 'INACTIVE' ? 'Tài khoản đang tạm khoá' : result.reason === 'SPOOF' ? 'Vui lòng nhìn trực tiếp vào camera' : 'Vui lòng liên hệ lễ tân';
  return <Animated.View testID="result-panel" style={[local.panel, { backgroundColor: colors.bg, borderColor: result.reason === 'SPOOF' ? theme.color.danger : colors.bg, borderWidth: result.reason === 'SPOOF' ? 6 : 0 }, panelStyle]}>
    <Animated.View style={[local.body, animated]}>
      {Icon === CheckCircle ? <DrawnCheck foreground={colors.fg} background={colors.bg} /> : <Icon size={96} color={colors.fg} weight="fill" />}
      <Text style={[local.name, { color: colors.fg }]}>{headline}</Text>
      {result.employee ? <Text style={[local.code, { color: colors.fg }]}>{result.employee.code}</Text> : null}
      <Text style={[local.detail, { color: colors.fg }]}>{detail}</Text>
      {result.result === 'OK' && result.attendance?.kind !== 'NONE' && result.attendance?.status ? <StatusChip domain="attendance_day.status" value={result.attendance.status} large /> : null}
    </Animated.View>
    <Animated.View style={[local.countdown, { backgroundColor: colors.fg }, countdown]} />
  </Animated.View>;
}
const local = StyleSheet.create({ panel: { flex: 1, justifyContent: 'center', alignItems: 'center' }, body: { alignItems: 'center', gap: 20, padding: 48 }, name: { fontFamily: fonts.semibold, fontSize: 56, letterSpacing: -1.2, textAlign: 'center' }, detail: { fontSize: 28, fontFamily: fonts.medium, textAlign: 'center' }, code: { fontSize: 22, fontFamily: fonts.medium }, countdown: { position: 'absolute', left: 0, bottom: 0, right: 0, height: 6, transformOrigin: 'left' } });
