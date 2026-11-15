import { useFormExitWarning } from '../../shared/useFormExitWarning';
import { AnimatedTable as Table } from '../../components/AnimatedTable';
import { useRef, useState } from 'react';
import { Alert, Button, Drawer, Form, Input, Modal, Select, Space, Tabs, Tag } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { api, type Session } from '../../api/client';
import type { components } from '../../api/schema';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { statusInfo } from '../../theme/status';
import { dateTime } from '../../shared/format';
type User = components['schemas']['User']; type Department = components['schemas']['Department'];
type Fields = components['schemas']['UserCreate'] & components['schemas']['UserUpdate'] & { pin?: string };
export function OrganizationPage({ session }: { session: Session }) {
  const owner = session.user.roles.some(grant => grant.role === 'OWNER');
  const [page, setPage] = useState(1); const [q, setQ] = useState('');
  const users = useQuery({ queryKey: ['users', page, q], queryFn: async () => readResult(await api.GET('/users', { params: { query: { page, size: 20, q: q || undefined } } })) });
  const directory = useQuery({ queryKey: ['user-directory'], queryFn: async () => {
    const all: User[] = []; let page = 1;
    while (true) { const result = readResult(await api.GET('/users', { params: { query: { page, size: 100 } } })); all.push(...result.items); if (all.length >= result.total || !result.items.length) return all; page++; }
  } });
  const departments = useQuery({ queryKey: ['departments', session.user.id], queryFn: async () => readResult(await api.GET('/departments')) });
  const [department, setDepartment] = useState<Department | 'new' | null>(null); const [editor, setEditor] = useState<User | 'new' | null>(null);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const locked = useRef(false);
  const [password, setPassword] = useState<string>(); const [confirmation, setConfirmation] = useState<User>();
  const [form] = Form.useForm<Fields>(); const [departmentForm] = Form.useForm<components['schemas']['DepartmentInput']>();
  useFormExitWarning(form, !!editor); useFormExitWarning(departmentForm, !!department);
  const roles = Form.useWatch('roles', form) as components['schemas']['RoleGrant'][] | undefined;
  async function run(action: () => Promise<unknown>) {
    if (locked.current) return; locked.current = true; setBusy(true); setError('');
    try { await action(); await Promise.all([users.refetch(), departments.refetch(), directory.refetch()]); } catch (failure) { setError(requestMessage(failure)); } finally { locked.current = false; setBusy(false); }
  }
  function openUser(value: User | 'new') { setError(''); setEditor(value); form.resetFields(); form.setFieldsValue(value === 'new' ? { roles: [{ role: 'EMPLOYEE' }], status: 'ACTIVE' } : { ...value, employee_id: value.employee?.id }); }
  async function saveUser(values: Fields) {
    await run(async () => {
      if (!editor) return;
      if (editor === 'new') { const result = readResult(await api.POST('/users', { body: { email: values.email.trim(), roles: values.roles, employee_id: values.employee_id || null } })); setPassword(result.temporary_password); }
      else {
        readResult(await api.PATCH('/users/{id}', { params: { path: { id: editor.id } }, body: { status: values.status } }));
        readResult(await api.PUT('/users/{id}/roles', { params: { path: { id: editor.id } }, body: { roles: values.roles } }));
        if (values.pin) readResult(await api.PUT('/users/{id}/kiosk-pin', { params: { path: { id: editor.id } }, body: { pin: values.pin } }));
      }
      setEditor(null); form.resetFields();
    });
  }
  const canManage = (user: User) => owner || !user.roles.some(grant => grant.role === 'OWNER');
  const deptOptions = departments.data?.map(item => ({ value: item.id, label: item.name })) ?? [];
  return <><PageHero title="Phòng ban & tài khoản" description="Phân quyền theo trách nhiệm và phòng ban." />{error && !editor && !department && <Alert className="feedback" type="error" role="alert" message={error} />}
    <section className="content-panel"><Tabs items={[
      { key: 'departments', label: 'Phòng ban', children: <><Button type="primary" onClick={() => { setError(''); setDepartment('new'); departmentForm.resetFields(); }}>Thêm phòng ban</Button><QueryState query={departments} /><Table rowKey="id" dataSource={departments.data} pagination={false} columns={[{ title: 'Tên phòng ban', dataIndex: 'name' }, { title: 'Số nhân viên', dataIndex: 'employee_count' }, { title: 'Quản lý', render: (_, row) => directory.data?.filter(user => user.roles.some(grant => grant.role === 'MANAGER' && grant.scope_department_id === row.id)).map(user => user.email).join(', ') || '—' }, { title: 'Thao tác', render: (_, row) => <Button onClick={() => { setError(''); setDepartment(row); departmentForm.setFieldsValue(row); }}>Sửa phòng ban {row.name}</Button> }]} /></> },
      { key: 'users', label: 'Tài khoản', children: <><Space className="section-actions"><Input.Search aria-label="Tìm tài khoản" placeholder="Tìm email…" onSearch={value => { setQ(value); setPage(1); }} /><Button type="primary" onClick={() => openUser('new')}>Thêm tài khoản</Button></Space><QueryState query={users} /><Table<User> rowKey="id" scroll={{ x: 900 }} dataSource={users.data?.items} pagination={{ current: page, pageSize: 20, total: users.data?.total, showSizeChanger: false, onChange: setPage }} columns={[{ title: 'Email', dataIndex: 'email' }, { title: 'Nhân viên', render: (_, user) => user.employee?.full_name || '—' }, { title: 'Vai trò', render: (_, user) => user.roles.map((grant, index) => <Tag key={index}>{statusInfo('user_role.role', grant.role).label}{grant.scope_department_id ? ` · ${departments.data?.find(item => item.id === grant.scope_department_id)?.name ?? '—'}` : ''}</Tag>) }, { title: 'Trạng thái', render: (_, user) => user.status === 'ACTIVE' ? 'Hoạt động' : 'Vô hiệu hoá' }, { title: 'Đăng nhập cuối', render: (_, user) => dateTime(user.last_login_at) }, { title: 'Thao tác', render: (_, user) => canManage(user) ? <Button onClick={() => openUser(user)}>Sửa tài khoản {user.email}</Button> : 'Chỉ Chủ doanh nghiệp được sửa' }]} /></> },
    ]} /></section>
    <Modal open={!!department} title={department === 'new' ? 'Thêm phòng ban' : 'Sửa phòng ban'} okText="Lưu phòng ban" cancelText="Hủy" confirmLoading={busy} onOk={() => departmentForm.submit()} onCancel={() => { if (!busy) setDepartment(null); }}>{error && <Alert type="error" role="alert" message={error} />}<Form autoComplete="off" scrollToFirstError form={departmentForm} layout="vertical" disabled={busy} onFinish={values => void run(async () => { if (!department) return; readResult(department === 'new' ? await api.POST('/departments', { body: values }) : await api.PATCH('/departments/{id}', { params: { path: { id: department.id } }, body: values })); setDepartment(null); })}><Form.Item name="name" label="Tên phòng ban" rules={[{ required: true, whitespace: true, message: 'Nhập tên phòng ban' }]}><Input /></Form.Item></Form></Modal>
    <Drawer width={480} title={editor === 'new' ? 'Thêm tài khoản' : 'Sửa tài khoản'} open={!!editor} onClose={() => { if (!busy) { setEditor(null); form.resetFields(); } }} maskClosable={!busy} footer={<Button type="primary" loading={busy} onClick={() => form.submit()}>Lưu tài khoản</Button>}>
      {error && <Alert type="error" role="alert" message={error} />}<Form autoComplete="off" scrollToFirstError form={form} layout="vertical" disabled={busy} onFinish={values => void saveUser(values)}>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Nhập email hợp lệ' }]}><Input disabled={editor !== 'new'} autoComplete="off" spellCheck={false} /></Form.Item>
        {editor !== 'new' && <Form.Item name="status" label="Trạng thái"><Select options={[{ value: 'ACTIVE', label: 'Hoạt động' }, { value: 'DISABLED', label: 'Vô hiệu hoá' }]} /></Form.Item>}
        <Form.List name="roles" rules={[{ validator: async (_, value) => { if (!value?.length) throw new Error('Chọn ít nhất một vai trò'); } }]}>{(fields, { add, remove }, { errors }) => <><h3>Vai trò</h3>{fields.map(field => <div key={field.key} className="role-row"><Form.Item name={[field.name, 'role']} label="Vai trò" rules={[{ required: true }]}><Select onChange={() => form.setFieldValue(['roles', field.name, 'scope_department_id'], null)} options={(['OWNER', 'HR', 'SECURITY', 'EMPLOYEE', 'MANAGER'] as const).filter(role => owner || role !== 'OWNER').map(role => ({ value: role, label: statusInfo('user_role.role', role).label }))} /></Form.Item>{roles?.[field.name]?.role === 'MANAGER' && <Form.Item name={[field.name, 'scope_department_id']} label="Phòng ban quản lý" rules={[{ required: true, message: 'Chọn phòng ban' }]}><Select options={deptOptions} /></Form.Item>}<Button danger onClick={() => remove(field.name)}>Bỏ vai trò</Button></div>)}<Form.ErrorList errors={errors} /><Button onClick={() => add({ role: 'EMPLOYEE' })}>Thêm vai trò</Button></>}</Form.List>
        {editor && editor !== 'new' && roles?.some(grant => ['OWNER', 'HR'].includes(grant.role)) && <Form.Item name="pin" label="PIN Kiosk mới (4 số)" rules={[{ pattern: /^\d{4}$/, message: 'PIN gồm đúng 4 chữ số' }]}><Input.Password inputMode="numeric" autoComplete="new-password" maxLength={4} /></Form.Item>}
      </Form>{editor && editor !== 'new' && <Button danger className="section-actions" onClick={() => setConfirmation(editor)}>Đặt lại mật khẩu</Button>}
    </Drawer>
    <Modal title="Đặt lại mật khẩu" open={!!confirmation} okText="Đặt lại mật khẩu" cancelText="Hủy" confirmLoading={busy} onCancel={() => { if (!busy) setConfirmation(undefined); }} onOk={() => void run(async () => { if (!confirmation) return; const result = readResult(await api.POST('/users/{id}/reset-password', { params: { path: { id: confirmation.id } } })); setPassword(result.temporary_password); setConfirmation(undefined); })}><p>Thu hồi các phiên làm mới và tạo mật khẩu tạm cho {confirmation?.email}?</p></Modal>
    <Modal open={!!password} title="Mật khẩu tạm — chỉ hiện một lần" onCancel={() => setPassword(undefined)} footer={<Button onClick={() => setPassword(undefined)}>Đã lưu mật khẩu</Button>}><Alert type="warning" message="Gửi mật khẩu riêng cho người dùng; cần đổi ở lần đăng nhập đầu." /><p>{password}</p></Modal>
  </>;
}
