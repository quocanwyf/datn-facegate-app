import { useEffect, useState } from 'react';
import { Alert, Image, Skeleton } from 'antd';
import { api } from '../api/client';
import type { components } from '../api/schema';
import { cos } from '../shared/format';
function SampleImage({ id }: { id: string }) {
  const [url, setUrl] = useState(''); const [error, setError] = useState(false);
  useEffect(() => {
    const abort = new AbortController(); let objectUrl = '';
    api.GET('/face-samples/{id}/image', { params: { path: { id } }, parseAs: 'blob', signal: AbortSignal.any([abort.signal, AbortSignal.timeout(15000)]) }).then(({ data, response }) => {
      if (!response.ok || !data) throw new Error();
      if (abort.signal.aborted) return;
      objectUrl = URL.createObjectURL(data); setUrl(objectUrl);
    }).catch(() => { if (!abort.signal.aborted) setError(true); });
    return () => { abort.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [id]);
  return error ? <Alert type="error" message="Không tải được ảnh mẫu" /> : url ? <Image src={url} width={224} height={224} alt="Ảnh mẫu đăng ký khuôn mặt" /> : <Skeleton.Image active />;
}
export function FaceImages({ samples }: { samples: components['schemas']['FaceSample'][] }) {
  return <Image.PreviewGroup><div className="face-grid">{samples.map(sample => <figure key={sample.id}><SampleImage id={sample.id} /><figcaption>Phát hiện {cos(sample.det_score)} · Độ nghiêng {cos(sample.yaw_ratio)}</figcaption></figure>)}</div></Image.PreviewGroup>;
}
