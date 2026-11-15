import { Text, View } from 'react-native';
import { CheckCircle } from 'phosphor-react-native/src/icons/CheckCircle';
import { HourglassMedium } from 'phosphor-react-native/src/icons/HourglassMedium';
import { fonts, status, theme } from '../theme';
export function K09Sent({ duplicate, declined = false }: { duplicate?: boolean; declined?: boolean }) {
  const Icon = declined ? CheckCircle : HourglassMedium;
  const colors = declined ? { bg: theme.color.bg, fg: theme.color.text } : status.groups.progress.kiosk;
  return <View testID={declined ? 'consent-declined' : 'enroll-sent'} style={{ flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center', padding: 48, gap: 24 }}><Icon size={96} weight="fill" color={colors.fg} /><Text style={{ fontFamily: fonts.semibold, fontSize: 56, color: colors.fg }}>{declined ? 'Đã ghi nhận' : 'Đã gửi đăng ký'}</Text><Text style={{ fontFamily: fonts.medium, fontSize: 28, textAlign: 'center', color: colors.fg }}>{declined ? 'Bạn sẽ chấm công tại quầy lễ tân.' : 'Chờ quản trị xác nhận trước khi dùng để chấm công'}</Text>{duplicate ? <Text style={{ fontFamily: fonts.medium, fontSize: 22, color: colors.fg }}>Lưu ý: khuôn mặt giống một nhân viên khác — quản trị sẽ kiểm tra</Text> : null}</View>;
}
