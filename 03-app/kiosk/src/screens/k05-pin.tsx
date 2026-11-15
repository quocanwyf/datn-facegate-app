import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import type { components } from '../api/schema';
import { ErrorNotice, PillButton, styles } from '../components/controls';
import { PinDots } from '../components/pin-dots';
type Enroller = components['schemas']['Enroller'];
export function K05Pin({ people, loading, error, busy, onRetry, onCancel, onSubmit }: { people: Enroller[]; loading: boolean; error: string; busy: boolean; onRetry: () => void; onCancel: () => void; onSubmit: (id: string, pin: string) => Promise<void> }) {
  const [selected, setSelected] = useState<string>(); const [pin, setPin] = useState(''); const idle = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const pinRef = useRef(''); const submitting = useRef(false);
  function activity() { clearTimeout(idle.current); idle.current = setTimeout(onCancel, 30000); }
  useEffect(() => { idle.current = setTimeout(onCancel, 30000); return () => clearTimeout(idle.current); }, [onCancel]);
  async function press(value: string) {
    activity(); if (busy || submitting.current) return;
    if (value === 'Huỷ') { onCancel(); return; }
    if (value === 'Xoá') { pinRef.current = pinRef.current.slice(0, -1); setPin(pinRef.current); return; }
    if (!selected || pinRef.current.length >= 4) return;
    const next = pinRef.current + value; pinRef.current = next; setPin(next);
    if (next.length === 4) { submitting.current = true; try { await onSubmit(selected, next); } finally { pinRef.current = ''; setPin(''); submitting.current = false; } }
  }
  return <View style={[styles.page, local.columns]}><View style={{ flex: 1, gap: 20 }}><Text style={styles.title}>Chế độ đăng ký</Text><Text style={styles.text}>Chọn tài khoản và nhập PIN Kiosk 4 số của bạn.</Text>
    {loading ? <ActivityIndicator /> : <FlatList data={people} keyExtractor={item => item.user_id} contentContainerStyle={{ gap: 12 }} renderItem={({ item }) => <PillButton title={item.name} secondary={selected !== item.user_id} disabled={busy} onPress={() => { if (submitting.current) return; activity(); setSelected(item.user_id); pinRef.current = ''; setPin(''); }} testID={`enroller-${item.user_id}`} />} ListEmptyComponent={error ? undefined : <Text style={styles.muted}>Chưa có tài khoản có PIN. Liên hệ Chủ doanh nghiệp.</Text>} />}
    <ErrorNotice message={error} />{error ? <PillButton title="Thử lại danh sách" secondary onPress={onRetry} disabled={busy} /> : null}<PillButton title="Huỷ" secondary onPress={onCancel} disabled={busy} />
  </View><View style={local.right}><PinDots count={pin.length} error={error} />
    {busy ? <ActivityIndicator /> : null}<View style={local.pad}>{['1','2','3','4','5','6','7','8','9','Xoá','0','Huỷ'].map(value => <PillButton key={value} title={value} secondary disabled={busy || !selected && /^\d$/.test(value)} onPress={() => void press(value)} style={local.key} testID={`pin-${value}`} />)}</View>
  </View></View>;
}
const local = StyleSheet.create({ columns: { flexDirection: 'row', gap: 64, padding: 48 }, right: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 32 }, pad: { flexDirection: 'row', flexWrap: 'wrap', width: 288, gap: 16 }, key: { width: 80, height: 80, minWidth: 80 }, dot: { width: 20, height: 20, borderRadius: 10 } });
