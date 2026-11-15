import { ActivityIndicator, FlatList, Text, View } from 'react-native';
import type { components } from '../api/schema';
import { ErrorNotice, Field, PillButton, styles } from '../components/controls';
import { fonts } from '../theme';
import { StatusChip } from '../components/status-chip';
export function K06Pick({ employees, loading, error, query, remaining, onQuery, onPick, onCancel, onRetry }: { employees: components['schemas']['KioskEmployee'][]; loading: boolean; error: string; query: string; remaining: string; onQuery: (value: string) => void; onPick: (employee: components['schemas']['KioskEmployee']) => void; onCancel: () => void; onRetry: () => void }) {
  return <View style={styles.page}><View style={styles.row}><PillButton title="← Thoát" secondary onPress={onCancel} /><Text style={[styles.title, { flex: 1 }]}>Chọn nhân viên</Text><Text style={styles.muted}>Phiên còn {remaining}</Text></View>
    <Field label="Tìm tên hoặc mã nhân viên" value={query} onChange={onQuery} testID="employee-search" /><ErrorNotice message={error} />{error ? <PillButton title="Thử lại" onPress={onRetry} secondary /> : null}
    {loading ? <ActivityIndicator /> : <FlatList data={employees} keyExtractor={item => item.id} keyboardShouldPersistTaps="handled" contentContainerStyle={{ gap: 12 }} renderItem={({ item }) => <View style={[styles.card, { borderRadius: 24, padding: 20 }]}><View style={styles.row}><View style={{ flex: 1, gap: 8 }}><Text style={[styles.text, { fontFamily: fonts.semibold }]}>{item.full_name}</Text><Text style={styles.muted}>{item.code} · {item.department_name}</Text><StatusChip domain="face_profile.status" value={item.face_profile_status} /></View><PillButton title="Chọn" secondary onPress={() => onPick(item)} testID={`employee-${item.code}`} /></View></View>} ListEmptyComponent={error ? undefined : <Text style={styles.text}>Không tìm thấy nhân viên</Text>} />}
  </View>;
}
