import { AnimatedTable as Table } from '../../components/AnimatedTable';
import { useState } from 'react';
import { DatePicker, Input, Select } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { operations } from '../../api/schema';
import { readResult } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { dateTime } from '../../shared/format';
const labels: Record<string, string> = { EMPLOYEE_CREATE: 'Thêm nhân viên', EMPLOYEE_UPDATE: 'Sửa nhân viên', EMPLOYEE_SUSPEND: 'Tạm khóa nhân viên', EMPLOYEE_REACTIVATE: 'Mở khóa nhân viên', EMPLOYEE_TERMINATE: 'Nhân viên nghỉ việc', FACE_APPROVE: 'Xác nhận khuôn mặt', FACE_REJECT: 'Từ chối khuôn mặt', FACE_DELETE: 'Xoá khuôn mặt', DEPARTMENT_CREATE: 'Thêm phòng ban', DEPARTMENT_UPDATE: 'Sửa phòng ban', USER_CREATE: 'Thêm tài khoản', USER_UPDATE: 'Sửa tài khoản', USER_ROLES_UPDATE: 'Cập nhật vai trò', USER_PIN_UPDATE: 'Đổi PIN Kiosk', USER_PASSWORD_RESET: 'Đặt lại mật khẩu', GATE_CREATE: 'Thêm cửa', GATE_UPDATE: 'Sửa cửa', GATE_POLICY_UPDATE: 'Sửa phòng ban được phép', DEVICE_CREATE: 'Thêm thiết bị', DEVICE_REVOKE: 'Thu hồi thiết bị', SETTINGS_UPDATE: 'Cấu hình nhận dạng' };
type Filters = NonNullable<operations['getAuditLogs']['parameters']['query']>;
export function AuditPage() {
  const [filters, setFilters] = useState<Filters>({ page: 1, size: 20 });
  const logs = useQuery({ queryKey: ['audit', filters], queryFn: async ({ signal }) => readResult(await api.GET('/audit-logs', { params: { query: filters }, signal })) });
  const users = useQuery({ queryKey: ['audit-users'], queryFn: async () => readResult(await api.GET('/users', { params: { query: { size: 100 } } })) });
  return <><PageHero title="Nhật ký thao tác" count={logs.data?.total} description="Theo dõi người thực hiện và đối tượng thay đổi." /><section className="content-panel"><div className="employee-filters"><DatePicker.RangePicker showTime format="DD/MM/YYYY HH:mm" onChange={range => setFilters(previous => ({ ...previous, page: 1, from_ts: range?.[0]?.toISOString(), to_ts: range?.[1]?.toISOString() }))} /><Select aria-label="Người thực hiện" allowClear placeholder="Người thực hiện" options={users.data?.items.map(item => ({ value: item.id, label: item.email }))} onChange={value => setFilters(previous => ({ ...previous, page: 1, actor_user_id: value }))} /><Input.Search aria-label="Lọc hành động" placeholder="Mã hành động…" onSearch={value => setFilters(previous => ({ ...previous, page: 1, action: value || undefined }))} /></div><QueryState query={logs} />
    <Table rowKey="id" dataSource={logs.data?.items} scroll={{ x: 800 }} pagination={{ current: filters.page, pageSize: 20, total: logs.data?.total, showSizeChanger: false, onChange: page => setFilters(previous => ({ ...previous, page })) }} columns={[{ title: 'Thời gian', render: (_, item) => dateTime(item.at) }, { title: 'Người / thiết bị', render: (_, item) => item.actor || item.actor_device || 'Hệ thống' }, { title: 'Hành động', render: (_, item) => labels[item.action] ?? item.action }, { title: 'Đối tượng', render: (_, item) => <span>{item.entity}<br /><small>{item.entity_id}</small></span> }]} expandable={{ expandedRowRender: item => <dl>{Object.entries(item.detail ?? {}).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === 'string' ? value : JSON.stringify(value)}</dd></div>)}</dl>, rowExpandable: item => !!item.detail }} /></section></>;
}
