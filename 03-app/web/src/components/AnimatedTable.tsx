import { useRef } from 'react';
import { Table, type TableProps } from 'antd';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
gsap.registerPlugin(useGSAP);
export function AnimatedTable<Row extends object>(props: TableProps<Row>) {
  const container = useRef<HTMLDivElement>(null);
  useGSAP(() => {
    if (!props.dataSource?.length) return;
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.fromTo('.ant-table-tbody > .ant-table-row:nth-child(-n+10)', { opacity: 0, y: 4 }, { opacity: 1, y: 0, duration: .18, stagger: .02, clearProps: 'all' });
    });
    return () => media.revert();
  }, { scope: container, dependencies: [props.dataSource], revertOnUpdate: true });
  return <div ref={container}><Table<Row> {...props} /></div>;
}
