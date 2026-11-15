import { Text, View } from 'react-native';
import { WifiSlash } from 'phosphor-react-native/src/icons/WifiSlash';
import { WarningCircle } from 'phosphor-react-native/src/icons/WarningCircle';
import { styles, ResearchBanner } from '../components/controls';
import { theme } from '../theme';
import type { Connection } from '../ws/KioskSocket';
export function K11Offline({ connection }: { connection: Connection }) {
  const Icon = connection.unavailable ? WarningCircle : WifiSlash;
  return <View style={[styles.page, { justifyContent: 'center', alignItems: 'center', gap: 32 }]} testID="offline-panel"><Icon size={96} weight="regular" color={theme.color.textSecondary} /><Text style={styles.title}>{connection.unavailable ?? 'Không kết nối được máy chủ'}</Text><Text style={styles.text}>{connection.unavailable ? 'Đang chờ máy chủ sẵn sàng.' : 'Vui lòng báo lễ tân. Đang thử kết nối lại…'}</Text>{!connection.unavailable ? <Text style={styles.muted}>Lần thử: {connection.attempt}</Text> : null}<ResearchBanner /></View>;
}
