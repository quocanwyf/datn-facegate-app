import { Tag } from 'antd';
import { statusInfo, type StatusDomain } from '../theme/status';
export function StatusPill({ domain, value }: { domain: StatusDomain; value?: string | null }) {
  const { label, bg, fg } = statusInfo(domain, value);
  return <Tag className="status-pill" bordered={false} style={{ background: bg, color: fg }}>{label}</Tag>;
}
