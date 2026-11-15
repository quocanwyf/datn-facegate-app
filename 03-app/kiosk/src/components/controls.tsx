import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { Button, Host, Text as NativeText, TextInput, useNativeState } from '@expo/ui';
import { fonts, theme } from '../theme';

export function PillButton({ title, onPress, disabled, busy, secondary, danger, testID, style }: { title: string; onPress: () => void; disabled?: boolean; busy?: boolean; secondary?: boolean; danger?: boolean; testID?: string; style?: StyleProp<ViewStyle> }) {
  const background = danger ? theme.color.danger : secondary ? theme.color.surfaceRaised : theme.color.inverse;
  const foreground = danger ? theme.color.onDanger : secondary ? theme.color.text : theme.color.onInverse;
  return <View style={[styles.button, { backgroundColor: background, borderRadius: theme.radius.full }, secondary ? theme.shadow['1'] : undefined, style]}><Host style={{ flex: 1 }} colorScheme="light"><Button variant="text" label={busy ? 'Đang gửi…' : title} onPress={onPress} disabled={disabled || busy} testID={testID} style={{ width: '100%', height: '100%', borderRadius: theme.radius.full, backgroundColor: background }}><NativeText textStyle={{ fontFamily: fonts.semibold, fontSize: theme.type.button.size, color: foreground }}>{busy ? 'Đang gửi…' : title}</NativeText></Button></Host>{busy ? <ActivityIndicator style={styles.spinner} color={foreground} /> : null}</View>;
}
export function Field({ label, value, onChange, numeric, testID, maxLength, editable = true }: { label: string; value: string; onChange: (value: string) => void; numeric?: boolean; testID?: string; maxLength?: number; editable?: boolean }) {
  const nativeValue = useNativeState(value);
  useEffect(() => { nativeValue.value = value; }, [nativeValue, value]);
  return <View style={styles.field}><Text style={styles.label}>{label}</Text><Host style={{ height: 56 }} colorScheme="light"><TextInput accessibilityLabel={label} testID={testID} value={nativeValue} onChangeText={text => { nativeValue.value = text; onChange(text); }} editable={editable} autoCapitalize="none" autoCorrect={false} autoComplete="off" keyboardType={numeric ? 'number-pad' : 'default'} inputMode={numeric ? 'numeric' : 'text'} maxLength={maxLength} style={{ width: '100%', height: 56, borderRadius: theme.radius.md, paddingHorizontal: 16, paddingVertical: 14, backgroundColor: theme.color.surface }} textStyle={{ fontFamily: fonts.regular, fontSize: theme.type.body.size, color: theme.color.text }} /></Host></View>;
}
export function ErrorNotice({ message }: { message?: string }) { return message ? <Text accessibilityRole="alert" style={styles.error}>{message}</Text> : null; }
export function ResearchBanner({ text = 'Bản trình diễn nghiên cứu – không dùng thương mại' }: { text?: string }) { return <View style={styles.banner}><Text style={styles.bannerText}>{text}</Text></View>; }
export const styles = StyleSheet.create({
  button: { height: theme.size.buttonHeight, minWidth: 180 }, spinner: { position: 'absolute', left: 16, top: 18 },
  field: { gap: 8, width: '100%' }, label: { fontFamily: fonts.medium, fontSize: 15, color: theme.color.textSecondary },
  error: { color: theme.color.danger, fontFamily: fonts.medium, fontSize: 17, lineHeight: 25 },
  banner: { alignSelf: 'flex-end', paddingVertical: 8, paddingHorizontal: 16, backgroundColor: theme.color.surfaceRaised, borderRadius: theme.radius.sm }, bannerText: { fontFamily: fonts.regular, fontSize: theme.type.banner.size, color: theme.color.textSecondary },
  title: { fontFamily: fonts.semibold, fontSize: theme.type.screenTitle.size, letterSpacing: theme.type.screenTitle.letterSpacing, color: theme.color.text },
  text: { fontFamily: fonts.regular, fontSize: theme.type.body.size, lineHeight: 28, color: theme.color.text },
  muted: { fontFamily: fonts.regular, fontSize: 16, color: theme.color.textSecondary },
  card: { backgroundColor: theme.color.surfaceRaised, borderRadius: theme.radius.xl, padding: 32, gap: 20 },
  page: { flex: 1, backgroundColor: theme.color.bg, padding: 32, gap: 24 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 16 },
});
