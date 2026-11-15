import { useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
export function KpiTile({ label, value }: { label: string; value: number }) {
  const number = useRef<HTMLSpanElement>(null);
  useGSAP(() => { const media = gsap.matchMedia(); media.add('(prefers-reduced-motion: no-preference)', () => { gsap.fromTo(number.current, { textContent: 0 }, { textContent: value, snap: { textContent: 1 }, duration: .6 }); }); return () => media.revert(); }, { scope: number, dependencies: [value], revertOnUpdate: true });
  return <div className="kpi-tile"><span>{label}</span><b><span ref={number}>{value}</span></b></div>;
}
