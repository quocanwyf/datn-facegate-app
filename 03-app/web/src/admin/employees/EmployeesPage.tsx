import { useRef, useState, useEffect } from 'react';
import { Alert, Button, Dropdown, Empty, Input, Modal, Result, Select, Space, Table, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { MoreHorizontal, Plus, RotateCw, Users } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { api, type Session } from '../../api/client';
import { HttpError, readResult, requestMessage } from '../../api/result';
import type { components, operations } from '../../api/schema';
import { PageHero } from '../../components/PageHero';
import { StatusPill } from '../../components/StatusPill';
import { statusInfo, type StatusDomain } from '../../theme/status';
import { EmployeeEditor } from './EmployeeEditor';

type Employee = components['schemas']['Employee'];
type Filters = NonNullable<operations['getEmployees']['parameters']['query']>;
const statusOptions = <V extends string,>(domain: StatusDomain, values: readonly V[]) => values.map(value => ({ value, label: statusInfo(domain, value).label }));

export function EmployeesPage({ session }: { session: Session }) {
  const navigate = useNavigate(); const client = useQueryClient();
  const canWrite = session.user.roles.some(({ role }) => role === 'OWNER' || role === 'HR');
  const [filters, setFilters] = useState<Filters>({ page: 1, size: 20 });
  const [search, setSearch] = useState('');
  const [editor, setEditor] = useState<Employee | 'new' | null>(null);
  const [terminate, setTerminate] = useState<Employee | null>(null);
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null);
  const [notice, setNotice] = useState('');
  const actionLocked = useRef(false);
  const tableContainer = useRef<HTMLDivElement>(null);
  const headers = { Authorization: `Bearer ${session.access_token}` };
  const key = ['employees', session.user.id];
  useEffect(() => {
    const timer = setTimeout(() => { setFilters(previous => previous.q === (search.trim() || undefined) ? previous : { ...previous, q: search.trim() || undefined, page: 1 }); }, 300);
    return () => clearTimeout(timer);
  }, [search]);
  const employees = useQuery({ queryKey: [...key, filters], queryFn: async ({ signal }) => readResult(await api.GET('/employees', { headers, params: { query: filters }, signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]) })) });
  const departments = useQuery({ queryKey: ['departments', session.user.id], queryFn: async ({ signal }) => readResult(await api.GET('/departments', { headers, signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]) })) });
  const changeState = useMutation({ mutationFn: async ({ employee, action }: { employee: Employee; action: 'suspend' | 'reactivate' | 'terminate' }) =>
    readResult(await api.POST(`/employees/{id}/${action}`, { headers, params: { path: { id: employee.id } }, signal: AbortSignal.timeout(15000) })) });
  const updateFilters = (value: Partial<Filters>) => setFilters(previous => ({ ...previous, ...value, page: 1 }));
  const performAction = async (employee: Employee, action: 'suspend' | 'reactivate' | 'terminate') => {
    if (!canWrite || actionLocked.current) return;
    actionLocked.current = true; setNotice('');
    try {
      await changeState.mutateAsync({ employee, action });
      setTerminate(null);
      setNotice(action === 'suspend' ? 'Đã tạm khóa nhân viên' : action === 'reactivate' ? 'Đã mở khóa nhân viên' : 'Đã chuyển nhân viên sang nghỉ việc');
      await client.invalidateQueries({ queryKey: key });
    } catch { /* Chỉ báo thành công khi Hub xác nhận; lỗi giữ trong bảng/hộp thoại. */ }
    finally { actionLocked.current = false; }
  };
  useGSAP(() => {
    if (!employees.data || employees.isFetching) return;
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => { gsap.fromTo('.ant-table-tbody > .ant-table-row:nth-child(-n+10)', { opacity: 0, y: 4 }, { opacity: 1, y: 0, duration: .18, stagger: .02, clearProps: 'all' }); });
    return () => media.revert();
  }, { scope: tableContainer, dependencies: [employees.data, employees.isFetching], revertOnUpdate: true });
  const columns: TableColumnsType<Employee> = [
    { title: 'Mã', dataIndex: 'code', width: 100, render: value => <span className="employee-code">{value}</span> },
    { title: 'Họ tên', dataIndex: 'full_name', width: 195, render: (value, employee) => <Button className="employee-name" type="link" onClick={() => navigate(`/admin/employees/${employee.id}`)}>{value}</Button> },
    { title: 'Phòng ban', dataIndex: 'department_name', width: 160, render: (value, employee) => value || departments.data?.find(({ id }) => id === employee.department_id)?.name || '—' },
    { title: 'Trạng thái', width: 145, render: (_, employee) => <StatusPill domain="employee.status" value={employee.status} /> },
    { title: 'Phương thức', width: 140, render: (_, employee) => <StatusPill domain="employee.attendance_method" value={employee.attendance_method} /> },
    { title: 'Hồ sơ khuôn mặt', width: 155, render: (_, employee) => <StatusPill domain="face_profile.status" value={employee.face_profile_status} /> },
    { title: 'Ngày vào làm', width: 130, render: (_, employee) => employee.joined_at ? dayjs(employee.joined_at).format('DD/MM/YYYY') : '—' },
    ...(canWrite ? [{ title: '', key: 'actions', width: 56, render: (_: unknown, employee: Employee) => <span onClick={event => event.stopPropagation()}><Dropdown trigger={['click']} menu={{ items: [ { key: 'edit', label: 'Sửa' }, ...(employee.status !== 'TERMINATED' ? [{ key: employee.status === 'SUSPENDED' ? 'reactivate' : 'suspend', label: employee.status === 'SUSPENDED' ? 'Mở khóa' : 'Tạm khóa' }, { key: 'terminate', label: 'Nghỉ việc', danger: true }] : []) ], onClick: ({ key: action }) => { changeState.reset(); if (action === 'edit') setEditor(employee); else if (action === 'terminate') setTerminate(employee); else if (action === 'suspend' || action === 'reactivate') void performAction(employee, action); } }}><Button type="text" aria-label={`Thao tác ${employee.code}`} disabled={changeState.isPending} icon={<MoreHorizontal size={20} />} /></Dropdown></span> }] : []),
  ];
  const departmentOptions = departments.data?.filter(({ id }) => canWrite || session.user.roles.some(grant => grant.role === 'MANAGER' && grant.scope_department_id === id)).map(({ id, name }) => ({ value: id, label: name })) ?? [];
  const filterActive = !!(filters.q || filters.department_id || filters.status || filters.attendance_method || filters.face_profile_status);
  return <>
    <PageHero title="Nhân viên" count={employees.isError ? undefined : employees.data?.total} description="Quản lý hồ sơ và trạng thái làm việc của nhân viên." action={canWrite && <Button type="primary" icon={<Plus size={18} />} onClick={() => setEditor('new')}>Thêm nhân viên</Button>} />
    {!canWrite && <Alert className="feedback" type="info" showIcon message="Bạn chỉ có quyền xem nhân viên thuộc phòng ban mình quản lý." />}
    {notice && <Alert className="feedback" role="status" type="success" showIcon message={notice} closable onClose={() => setNotice('')} />}
    {changeState.isError && !terminate && <Alert className="feedback" role="alert" type="error" showIcon message={requestMessage(changeState.error)} />}
    <section className="content-panel employees-panel" aria-label="Danh sách nhân viên">
      <div className="panel-heading"><div><Users size={18} /><h2>Danh sách nhân viên</h2></div><Button type="text" icon={<RotateCw size={16} />} aria-label="Làm mới" loading={employees.isFetching} onClick={() => { void employees.refetch(); void departments.refetch(); }}>Làm mới</Button></div>
      <div className="employee-filters">
        <Input.Search className="employee-search" variant="filled" aria-label="Tìm nhân viên theo tên hoặc mã" placeholder="Tìm tên hoặc mã nhân viên" value={search} onChange={event => setSearch(event.target.value)} allowClear onSearch={value => updateFilters({ q: value.trim() || undefined })} />
        <Select aria-label="Lọc phòng ban" variant="filled" placeholder="Phòng ban" allowClear value={filters.department_id} loading={departments.isPending} disabled={departments.isError} options={departmentOptions} onChange={value => updateFilters({ department_id: value })} />
        <Select<Filters['status']> aria-label="Lọc trạng thái" variant="filled" placeholder="Trạng thái" allowClear value={filters.status} options={statusOptions('employee.status', ['ACTIVE', 'SUSPENDED', 'TERMINATED'] as const)} onChange={value => updateFilters({ status: value })} />
        <Select<Filters['attendance_method']> aria-label="Lọc phương thức" variant="filled" placeholder="Phương thức" allowClear value={filters.attendance_method} options={statusOptions('employee.attendance_method', ['FACE', 'MANUAL'] as const)} onChange={value => updateFilters({ attendance_method: value })} />
        <Select<Filters['face_profile_status']> aria-label="Lọc hồ sơ khuôn mặt" variant="filled" placeholder="Hồ sơ khuôn mặt" allowClear value={filters.face_profile_status} options={statusOptions('face_profile.status', ['NONE', 'PENDING_REVIEW', 'ACTIVE', 'REJECTED'] as const)} onChange={value => updateFilters({ face_profile_status: value })} />
        {filterActive && <Button type="link" onClick={() => { setSearch(''); setFilters({ page: 1, size: 20 }); }}>Xóa bộ lọc</Button>}
      </div>
      {departments.isError && <Alert className="feedback" type="warning" showIcon message="Không tải được phòng ban" description={requestMessage(departments.error)} action={<Button onClick={() => void departments.refetch()}>Thử lại</Button>} />}
      {employees.isError ? <Result status={employees.error instanceof HttpError && employees.error.status === 403 ? '403' : 'error'} title={employees.error instanceof HttpError && employees.error.status === 403 ? 'Bạn không có quyền xem trang này' : 'Không tải được danh sách nhân viên'} subTitle={requestMessage(employees.error)} extra={<Button onClick={() => void employees.refetch()}>Thử lại</Button>} /> : <div ref={tableContainer}>
        <Table<Employee> rowKey="id" columns={columns} dataSource={employees.data?.items ?? []} loading={employees.isFetching} size="middle" scroll={{ x: 1080 }} pagination={{ current: filters.page, pageSize: 20, total: employees.data?.total ?? 0, showSizeChanger: false, showTotal: (total, range) => `${range[0]}–${range[1]} / ${total} nhân viên`, onChange: page => setFilters(previous => ({ ...previous, page })) }}
          locale={{ emptyText: employees.isPending ? 'Đang tải nhân viên…' : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={filterActive ? 'Không tìm thấy nhân viên phù hợp' : 'Chưa có nhân viên'} /> }} onRow={employee => ({ onClick: () => navigate(`/admin/employees/${employee.id}`) })} />
      </div>}
    </section>
    {canWrite && editor && <EmployeeEditor employee={editor === 'new' ? undefined : editor} departments={departments.data ?? []} session={session} onClose={() => setEditor(null)} onSaved={password => { setNotice(editor === 'new' ? 'Đã thêm nhân viên' : 'Đã cập nhật nhân viên'); setEditor(null); setTemporaryPassword(password ?? null); void client.invalidateQueries({ queryKey: key }); }} />}
    <Modal title="Xác nhận nghỉ việc" open={!!terminate} okText="Xác nhận nghỉ việc" cancelText="Hủy" okButtonProps={{ danger: true, 'aria-label': 'Xác nhận nghỉ việc' }} confirmLoading={changeState.isPending} cancelButtonProps={{ disabled: changeState.isPending }} closable={!changeState.isPending} maskClosable={!changeState.isPending} keyboard={!changeState.isPending} onCancel={() => { if (!actionLocked.current) setTerminate(null); }} onOk={() => { if (terminate) void performAction(terminate, 'terminate'); }}>
      {changeState.isError && <Alert className="feedback" role="alert" type="error" showIcon message={requestMessage(changeState.error)} />}
      <p>Chuyển {terminate?.full_name} sang Đã nghỉ việc? Toàn bộ ảnh mẫu và đặc trưng khuôn mặt sẽ bị xoá ngay. Dữ liệu chấm công được giữ lại.</p>
    </Modal>
    <Modal title="Tài khoản đã được tạo" open={temporaryPassword !== null} onCancel={() => setTemporaryPassword(null)} footer={<Button type="primary" onClick={() => setTemporaryPassword(null)}>Đã lưu mật khẩu</Button>}>
      <Space direction="vertical"><Alert type="warning" showIcon message="Mật khẩu tạm chỉ hiển thị một lần. Hãy lưu và gửi riêng cho nhân viên." /><Typography.Text strong>{temporaryPassword}</Typography.Text></Space>
    </Modal>
  </>;
}
