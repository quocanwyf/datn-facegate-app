import tokens from './status.json';
export const statusMaps = tokens.enums;
export type StatusDomain = keyof typeof statusMaps;
export function statusInfo(domain: StatusDomain, value: string | null | undefined) {
  const entries = statusMaps[domain] as Record<string, { group: string; label_vi: string } | string>;
  const candidate = entries[value ?? 'NONE'];
  const entry = typeof candidate === 'object' ? candidate : undefined;
  const colors = tokens.groups[(entry?.group ?? 'neutral') as keyof typeof tokens.groups].web;
  return { label: entry?.label_vi ?? '—', ...colors };
}
