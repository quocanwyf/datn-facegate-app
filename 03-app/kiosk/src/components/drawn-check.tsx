import { useEffect } from 'react';
import Svg, { Circle, Path } from 'react-native-svg';
import Animated, { cancelAnimation, useAnimatedProps, useReducedMotion, useSharedValue, withTiming } from 'react-native-reanimated';

const AnimatedPath = Animated.createAnimatedComponent(Path);
// Hình học tương ứng CheckCircle Fill của Phosphor, tách nét ✓ để vẽ trên UI thread.
export function DrawnCheck({ foreground, background }: { foreground: string; background: string }) {
  const reduced = useReducedMotion(); const offset = useSharedValue(reduced ? 0 : 114);
  useEffect(() => { offset.set(withTiming(0, { duration: reduced ? 0 : 320 })); return () => cancelAnimation(offset); }, [offset, reduced]);
  const animatedProps = useAnimatedProps(() => ({ strokeDashoffset: offset.get() }));
  return <Svg width={96} height={96} viewBox="0 0 256 256" accessibilityLabel="Thành công"><Circle cx={128} cy={128} r={104} fill={foreground} /><AnimatedPath d="M88 136 L112 160 L168 104" fill="none" stroke={background} strokeWidth={16} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={[114, 114]} animatedProps={animatedProps} /></Svg>;
}
