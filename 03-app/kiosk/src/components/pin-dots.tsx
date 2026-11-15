import { useEffect } from 'react';
import { View } from 'react-native';
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { theme } from '../theme';

function PinDot({ filled }: { filled: boolean }) {
  const reduced = useReducedMotion(); const scale = useSharedValue(1);
  useEffect(() => { if (filled && !reduced) scale.set(withSequence(withTiming(1.25, { duration: 100 }), withTiming(1, { duration: 100 }))); return () => cancelAnimation(scale); }, [filled, reduced, scale]);
  const style = useAnimatedStyle(() => ({ transform: [{ scale: scale.get() }] }));
  return <Animated.View style={[{ width: 20, height: 20, borderRadius: 10, backgroundColor: filled ? theme.color.inverse : theme.color.border }, style]} />;
}
export function PinDots({ count, error }: { count: number; error: string }) {
  const reduced = useReducedMotion(); const x = useSharedValue(0);
  useEffect(() => { if (error && !reduced) x.set(withRepeat(withSequence(withTiming(8, { duration: 25 }), withTiming(-8, { duration: 50 }), withTiming(0, { duration: 25 })), 3, false)); return () => cancelAnimation(x); }, [error, reduced, x]);
  const style = useAnimatedStyle(() => ({ transform: [{ translateX: x.get() }] }));
  return <Animated.View style={style}><View style={{ flexDirection: 'row', alignItems: 'center', gap: 16 }} accessibilityLabel={`Đã nhập ${count} trên 4 số`}>{[0, 1, 2, 3].map(index => <PinDot key={index} filled={count > index} />)}</View></Animated.View>;
}
