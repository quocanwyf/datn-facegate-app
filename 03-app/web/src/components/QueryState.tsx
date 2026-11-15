import { Button, Result, Skeleton } from 'antd';
import { HttpError, requestMessage } from '../api/result';
export function QueryState({ query }: { query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown } }) {
  if (query.isPending) return <Skeleton active aria-label="Đang tải…" />;
  if (query.isError) return <Result status={query.error instanceof HttpError && query.error.status === 403 ? '403' : 'error'} title="Không tải được dữ liệu" subTitle={requestMessage(query.error)} extra={<Button onClick={() => query.refetch()}>Thử lại</Button>} />;
  return null;
}
