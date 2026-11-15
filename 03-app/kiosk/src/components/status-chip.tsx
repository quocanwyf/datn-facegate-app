import { Text, View } from 'react-native';
import { fonts, status, statusLabel, theme } from '../theme';

export function StatusChip({ domain, value, large = false }: { domain: 'face_profile.status' | 'attendance_day.status'; value?: string | null; large?: boolean }) {
  const entry = (status.enums[domain] as Record<string, { group: string } | string>)[value ?? 'NONE'];
  const group = typeof entry === 'object' ? entry.group : 'neutral';
  const colors = (status.groups as Record<string, { kiosk?: { bg: string; fg: string } }>)[group]?.kiosk ?? { bg: theme.color.surface, fg: theme.color.textSecondary };
  return <View style={{ alignSelf: large ? 'center' : 'flex-start', backgroundColor: colors.bg, borderColor: colors.fg, borderWidth: 1, borderRadius: theme.radius.full, paddingVertical: large ? 8 : 5, paddingHorizontal: large ? 18 : 12 }}><Text style={{ fontFamily: fonts.medium, fontSize: large ? theme.type.body.size : 15, color: colors.fg }}>{statusLabel(domain, value)}</Text></View>;
}
