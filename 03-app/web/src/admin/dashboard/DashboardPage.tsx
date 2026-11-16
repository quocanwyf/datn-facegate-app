import { AnimatedTable as Table } from '../../components/AnimatedTable';
import { List } from 'antd';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { readResult } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { KpiTile } from '../../components/KpiTile';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { dateTime } from '../../shared/format';
export function DashboardPage() {
  const dashboard = useQuery({ queryKey: ['dashboard'], queryFn: async ({ signal }) => readResult(await api.GET('/dashboard/today', { signal })), refetchInterval: 30000 });
  const events = useQuery({ queryKey: ['recent-events', 10], queryFn: async ({ signal }) => readResult(await api.GET('/events', { params: { query: { page: 1, size: 10 } }, signal })), refetchInterval: 30000 });
  const value = dashboard.data;
  return <><PageHero title={`Tổng quan · ${value?.date.split('-').reverse().join('/') ?? 'Hôm nay'}`} description="Ngày và chỉ số theo múi giờ công ty · Asia/Ho_Chi_Minh" /><QueryState query={dashboard} />
    {value && <><div className="kpi-grid"><KpiTile label="Có mặt" value={value.present} /><KpiTile label="Đi muộn" value={value.late} /><KpiTile label="Chưa đến" value={value.not_arrived} /><KpiTile label="Lượt người lạ hôm nay" value={value.strangers} /></div><div className="split-layout dashboard-grid"><section className="content-panel"><div className="panel-heading"><h2>10 sự kiện mới nhất</h2><Link to="/admin/events">Xem tất cả</Link></div><QueryState query={events} />{!events.isError && <Table rowKey="id" dataSource={events.data?.items} pagination={false} columns={[{ title: 'Giờ', render: (_, event) => dateTime(event.occurred_at) }, { title: 'Cửa', render: (_, event) => event.gate.name }, { title: 'Người', render: (_, event) => event.employee?.full_name || 'Người lạ' }, { title: 'Kết quả', render: (_, event) => <StatusPill domain="recognition_event.result" value={event.result} /> }]} />}</section><section className="content-panel"><h2>Cần xử lý</h2><List dataSource={[{ label: 'Khuôn mặt chờ xác nhận', count: value.pending_face_profiles, to: '/admin/faces' }, { label: 'Giải trình chờ', count: value.pending_requests, to: '/admin/requests' }, { label: 'Cảnh báo chưa xử lý', count: value.open_alerts, to: '/admin/monitor' }, { label: 'Thiết bị mất kết nối', count: value.devices_offline, to: '/admin/gates' }]} renderItem={item => <List.Item><Link to={item.to}>{item.label}</Link><b>{item.count ?? 0}</b></List.Item>} /></section></div></>}
  </>;
}
