import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Host, TextInput, useNativeState } from '@expo/ui';
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { fonts, theme } from '../theme';
import { styles } from './controls';

export function PairingCode({ value, onChange, error, editable }: { value: string; onChange: (value: string) => void; error: string; editable: boolean }) {
  const nativeValue = useNativeState(value); const [focused, setFocused] = useState(false);
  const reduced = useReducedMotion(); const x = useSharedValue(0);
  useEffect(() => { nativeValue.value = value; }, [nativeValue, value]);
  useEffect(() => { if (error && !reduced) x.set(withRepeat(withSequence(withTiming(8, { duration: 25 }), withTiming(-8, { duration: 50 }), withTiming(0, { duration: 25 })), 3, false)); return () => cancelAnimation(x); }, [error, reduced, x]);
  const shake = useAnimatedStyle(() => ({ transform: [{ translateX: x.get() }] }));
  return <Animated.View style={[styles.field, shake]}><Text style={styles.label}>Mã ghép 6 số</Text><View style={{ height: 56 }}>
    <Host colorScheme="light" style={StyleSheet.absoluteFill}><TextInput testID="pair-code" accessibilityLabel="Mã ghép 6 số" value={nativeValue} editable={editable} keyboardType="number-pad" inputMode="numeric" maxLength={6} caretHidden autoComplete="off" autoCorrect={false} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} onChangeText={text => { const code = text.replace(/\D/g, '').slice(0, 6); nativeValue.value = code; onChange(code); }} textStyle={{ color: 'transparent', fontFamily: fonts.medium, fontSize: 28 }} style={{ width: '100%', height: 56 }} /></Host>
    <View pointerEvents="none" accessible={false} style={[StyleSheet.absoluteFill, { flexDirection: 'row', gap: 8, opacity: editable ? 1 : .6 }]}>{[0, 1, 2, 3, 4, 5].map(index => <View key={index} style={{ flex: 1, height: 56, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.color.surface, borderRadius: theme.radius.md, borderWidth: 1, borderColor: focused && index === Math.min(value.length, 5) ? theme.color.primary : theme.color.border }}><Text accessible={false} style={{ color: theme.color.text, fontFamily: fonts.medium, fontSize: 28, fontVariant: ['tabular-nums'] }}>{value[index] ?? ''}</Text></View>)}</View>
  </View></Animated.View>;
}
