import { useFormExitWarning } from '../../shared/useFormExitWarning';
import { useRef } from 'react';
import { Alert, Button, Checkbox, DatePicker, Drawer, Form, Input, Select, Space } from 'antd';
import { useMutation } from '@tanstack/react-query';
import dayjs, { type Dayjs } from 'dayjs';
import { api, type Session } from '../../api/client';
import { readResult, requestMessage } from '../../api/result';
import type { components } from '../../api/schema';

type Employee = components['schemas']['Employee'];
type Fields = Omit<components['schemas']['EmployeeCreate'], 'joined_at'> & { joined_at?: Dayjs | null };

export function EmployeeEditor({ employee, departments, session, onClose, onSaved }: {
  employee?: Employee; departments: components['schemas']['Department'][]; session: Session;
  onClose: () => void; onSaved: (password?: string | null) => void;
}) {
  const [form] = Form.useForm<Fields>();
  useFormExitWarning(form);
  const locked = useRef(false);
  const createAccount = Form.useWatch('create_account', form);
  const mutation = useMutation({ mutationFn: async (values: Fields) => {
    const common = { full_name: values.full_name.trim(), email: values.email?.trim() || null, phone: values.phone?.trim() || null, department_id: values.department_id, joined_at: values.joined_at?.format('YYYY-MM-DD') ?? null };
    const options = { headers: { Authorization: `Bearer ${session.access_token}` }, signal: AbortSignal.timeout(15000) };
    if (employee) { readResult(await api.PATCH('/employees/{id}', { ...options, params: { path: { id: employee.id } }, body: common })); return null; }
    return readResult(await api.POST('/employees', { ...options, body: { ...common, code: values.code.trim(), create_account: values.create_account ?? false } })).temporary_password;
  } });
  const submit = async (values: Fields) => {
    if (locked.current) return;
    locked.current = true;
    try { const password = await mutation.mutateAsync(values); onSaved(password); }
    catch { /* Lỗi hiển thị trong Drawer; giữ lại nội dung để sửa/thử lại. */ }
    finally { locked.current = false; }
  };
  return <Drawer title={employee ? 'Sửa nhân viên' : 'Thêm nhân viên'} open width={480} onClose={() => { if (!locked.current) onClose(); }} maskClosable={!mutation.isPending} closable={!mutation.isPending} keyboard={!mutation.isPending}
    footer={<Space className="drawer-actions"><Button disabled={mutation.isPending} onClick={onClose}>Hủy</Button><Button type="primary" htmlType="submit" form="employee-form" aria-label="Lưu nhân viên" loading={mutation.isPending}>Lưu nhân viên</Button></Space>}>
    {mutation.isError && <Alert role="alert" className="feedback" type="error" showIcon message={requestMessage(mutation.error)} />}
    <Form autoComplete="off" scrollToFirstError id="employee-form" form={form} layout="vertical" requiredMark={false} onFinish={submit} disabled={mutation.isPending} initialValues={employee ? { ...employee, joined_at: employee.joined_at ? dayjs(employee.joined_at) : null } : { create_account: false }}>
      <Form.Item name="code" label="Mã nhân viên" rules={[{ required: true, whitespace: true, message: 'Vui lòng nhập mã nhân viên' }]}><Input variant="filled" disabled={!!employee || mutation.isPending} placeholder="Ví dụ: NV025" /></Form.Item>
      <Form.Item name="full_name" label="Họ và tên" rules={[{ required: true, whitespace: true, message: 'Vui lòng nhập họ và tên' }]}><Input variant="filled" placeholder="Nhập họ và tên đầy đủ" /></Form.Item>
      <Form.Item name="email" label="Email" normalize={(value: string) => value.trim()} rules={[{ type: 'email', message: 'Email không đúng định dạng' }, { required: !!createAccount, message: 'Cần email để tạo tài khoản đăng nhập' }]}><Input variant="filled" inputMode="email" placeholder="ten@congty.vn" /></Form.Item>
      <Form.Item name="phone" label="Số điện thoại"><Input variant="filled" inputMode="tel" placeholder="Nhập số điện thoại" /></Form.Item>
      <Form.Item name="department_id" label="Phòng ban" rules={[{ required: true, message: 'Vui lòng chọn phòng ban' }]}><Select variant="filled" placeholder="Chọn phòng ban" options={departments.map(({ id, name }) => ({ value: id, label: name }))} /></Form.Item>
      <Form.Item name="joined_at" label="Ngày vào làm"><DatePicker variant="filled" format="DD/MM/YYYY" placeholder="Chọn ngày" className="full-width" /></Form.Item>
      {!employee && <Form.Item name="create_account" valuePropName="checked"><Checkbox>Tạo tài khoản đăng nhập</Checkbox></Form.Item>}
      {!employee && createAccount && <Alert type="info" showIcon message="Email nhân viên sẽ là email đăng nhập. Mật khẩu tạm chỉ hiển thị một lần sau khi tạo thành công." />}
    </Form>
  </Drawer>;
}
