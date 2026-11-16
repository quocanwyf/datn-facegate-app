import { useEffect, useState } from 'react';
import { api } from '../../api/client';
export function EventSnapshot({ id, size = 96 }: { id: string; size?: number }) {
  const [url, setUrl] = useState(''); const [error, setError] = useState(false);
  useEffect(() => {
    let active = true, objectUrl = ''; const abort = new AbortController(); setUrl(''); setError(false);
    void api.GET('/events/{id}/snapshot', { params: { path: { id } }, parseAs: 'blob', signal: abort.signal }).then(result => {
      if (!active) return;
      if (result.response.ok && result.data) { objectUrl = URL.createObjectURL(result.data); setUrl(objectUrl); } else setError(true);
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; abort.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [id]);
  return error ? <span className="muted">Ảnh không còn</span> : url ? <img className="alert-snapshot" src={url} width={size} height={size} alt="Ảnh cảnh báo người lạ" onError={() => setError(true)} /> : <span className="muted">Đang tải ảnh…</span>;
}
