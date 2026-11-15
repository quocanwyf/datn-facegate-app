import theme from './kiosk-theme.json';
import status from './status.json';
export { theme, status };
export const fonts = { regular: 'Inter_400Regular', medium: 'Inter_500Medium', semibold: 'Inter_600SemiBold' };
export function statusLabel(domain: keyof typeof status.enums, value?: string | null) {
  const entry = (status.enums[domain] as Record<string, { label_vi: string } | string>)[value ?? 'NONE'];
  return typeof entry === 'object' ? entry.label_vi : '—';
}
export function hint(value: string) { return (status.kiosk_state_hint_vi as Record<string, string>)[value] ?? value; }
export function time(value?: string) { return value ? new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)) : '—'; }
