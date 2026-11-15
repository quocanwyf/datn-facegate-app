import { useRef, useState } from 'react';
import { Alert, Button, Empty, Input, Pagination, Space } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../api/client';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { FaceImages } from '../../components/FaceImages';
import { QueryState } from '../../components/QueryState';
import { cos, dateTime } from '../../shared/format';
export function FacesPage() {
  const [page, setPage] = useState(1); const [selected, setSelected] = useState<string>();
  const [note, setNote] = useState(''); const [busy, setBusy] = useState(false); const locked = useRef(false);
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const client = useQueryClient();
  const list = useQuery({ queryKey: ['faces', page], queryFn: async ({ signal }) => readResult(await api.GET('/face-profiles', { params: { query: { status: 'PENDING_REVIEW', page, size: 20 } }, signal })) });
  const profile = list.data?.items.find(item => item.id === selected) ?? list.data?.items[0];
  async function review(action: 'approve' | 'reject') {
    if (!profile || locked.current) return;
    locked.current = true; setBusy(true); setError(''); setNotice('');
    try {
      readResult(await api.POST(`/face-profiles/{id}/${action}`, { params: { path: { id: profile.id } }, body: { note: note.trim() || null } }));
      setNotice(action === 'approve' ? 'Đã xác nhận hồ sơ khuôn mặt' : 'Đã từ chối hồ sơ khuôn mặt'); setNote(''); setSelected(undefined);
      await client.invalidateQueries({ queryKey: ['faces'] });
    } catch (failure) { setError(requestMessage(failure)); await list.refetch(); }
    finally { locked.current = false; setBusy(false); }
  }
  return <><PageHero title="Xác nhận khuôn mặt" count={list.data?.total} description="Kiểm tra đủ 5 ảnh mẫu trước khi xác nhận." />
    {error && <Alert className="feedback" type="error" role="alert" message={error} showIcon />}{notice && <Alert className="feedback" type="success" role="status" message={notice} showIcon />}
    <QueryState query={list} />{!list.isPending && !list.isError && <div className="split-layout face-review">
      <section className="content-panel"><h2>Hồ sơ chờ xác nhận</h2>{list.data?.items.length ? list.data.items.map(item => <button disabled={busy} key={item.id} className={`selection-card ${profile?.id === item.id ? 'selected' : ''}`} onClick={() => { setSelected(item.id); setNote(''); }}><b>{item.employee.full_name}</b><span>{item.employee.code} · {dateTime(item.enrolled_at)}</span><span>Người đăng ký: {item.enrolled_by}</span>{item.duplicate_of && <span>⚠ Nghi trùng khuôn mặt</span>}</button>) : <Empty description="Không có hồ sơ chờ xác nhận" />}
        <Pagination current={page} total={list.data?.total} pageSize={20} showSizeChanger={false} onChange={setPage} /></section>
      <section className="content-panel">{profile ? <><h2>{profile.employee.full_name}</h2><p>Đăng ký lúc {dateTime(profile.enrolled_at)} · {profile.enrolled_by}</p><FaceImages key={profile.id} samples={profile.samples} />
        {profile.duplicate_of && <Alert className="feedback" type="warning" showIcon message={`Giống ${profile.duplicate_of.full_name} (cos ${cos(profile.duplicate_score)})`} />}
        <label htmlFor="review-note">Ghi chú {profile.duplicate_of ? '(bắt buộc khi xác nhận nghi trùng)' : ''}</label><Input.TextArea id="review-note" rows={3} value={note} onChange={event => setNote(event.target.value)} disabled={busy} />
        <Space className="section-actions"><Button disabled={busy || !note.trim()} onClick={() => void review('reject')}>Từ chối</Button><Button type="primary" loading={busy} disabled={!!profile.duplicate_of && !note.trim()} onClick={() => void review('approve')}>Xác nhận</Button></Space><p className="muted">Từ chối cần có ghi chú. Hồ sơ chỉ có hiệu lực sau khi Hub cập nhật xong gallery.</p></> : <Empty description="Chọn hồ sơ để xem chi tiết" />}</section>
    </div>}</>;
}
