import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Animated, { cancelAnimation, Easing, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { fonts, theme } from '../theme';
export function ScanFrame({ tracking, checking }: { tracking: boolean; checking: boolean }) {
  const reduced = useReducedMotion(); const y = useSharedValue(0); const border = useSharedValue(theme.color.frameIdle); const [height, setHeight] = useState(400);
  useEffect(() => {
    border.set(withTiming(tracking ? theme.color.frameTracking : theme.color.frameIdle, { duration: reduced ? 0 : 200 }));
    y.set(0); if (checking && !reduced) y.set(withRepeat(withTiming(height - 48, { duration: 1600, easing: Easing.linear }), -1, false));
    return () => { cancelAnimation(y); cancelAnimation(border); };
  }, [tracking, checking, height, reduced, y, border]);
  const frameStyle = useAnimatedStyle(() => ({ borderColor: border.get() })); const lineStyle = useAnimatedStyle(() => ({ transform: [{ translateY: y.get() }] }));
  return <Animated.View pointerEvents="none" style={[local.frame, frameStyle]} onLayout={event => setHeight(event.nativeEvent.layout.height)}>{checking && !reduced ? <Animated.View style={[local.line, lineStyle]}><LinearGradient colors={[`${theme.color.primary}00`, `${theme.color.primary}66`]} style={{ flex: 1 }} /></Animated.View> : null}</Animated.View>;
}
function Dot({ filled }: { filled: boolean }) {
  const scale = useSharedValue(1); const reduced = useReducedMotion();
  useEffect(() => { if (filled && !reduced) scale.set(withSequence(withTiming(1.3, { duration: 100 }), withTiming(1, { duration: 100 }))); return () => cancelAnimation(scale); }, [filled, reduced, scale]);
  const style = useAnimatedStyle(() => ({ transform: [{ scale: scale.get() }] }));
  return <Animated.View style={[local.dot, { backgroundColor: filled ? theme.color.primary : theme.color.frameIdle }, style]} />;
}
export function ProgressDots({ accepted }: { accepted: number }) { return <View style={local.progress}><View style={{ flexDirection: 'row', gap: 12 }}>{[0, 1, 2, 3, 4].map(index => <Dot key={index} filled={accepted > index} />)}</View><Text style={local.progressText}>Mẫu {accepted}/5</Text></View>; }
const local = StyleSheet.create({ frame: { position: 'absolute', left: '29%', top: '12%', width: '42%', height: '65%', borderWidth: theme.size.frameBorder, borderRadius: theme.radius.frame, overflow: 'hidden' }, line: { position: 'absolute', top: 0, left: 0, right: 0, height: 48 }, dot: { width: 20, height: 20, borderRadius: 10 }, progress: { alignItems: 'center', gap: 12, backgroundColor: theme.color.scrim, padding: 16, borderRadius: 24 }, progressText: { color: theme.color.onInverse, fontSize: 18, fontFamily: fonts.medium } });
