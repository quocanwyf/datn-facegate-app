export const companyTimezone = 'Asia/Ho_Chi_Minh';
export function dateTime(value?: string | null) {
  return value ? new Intl.DateTimeFormat('vi-VN', { timeZone: companyTimezone, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)) : '—';
}
export const cos = (value?: number | null) => value == null ? '—' : value.toLocaleString('vi-VN', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
