import type { ReactNode } from 'react';
import { Breadcrumb, Typography } from 'antd';
export function PageHero({ title, count, description, action }: { title: string; count?: number; description?: string; action?: ReactNode }) {
  return <section className="page-hero">
    <div><Breadcrumb items={[{ title: 'Quản trị' }, { title }]} /><h1>{title} {count !== undefined && <span className="hero-count">{count}</span>}</h1><Typography.Text type="secondary">{description}</Typography.Text></div>
    {action}
  </section>;
}
