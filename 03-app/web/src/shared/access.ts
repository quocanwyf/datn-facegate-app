import type { User } from '../api/client';
export function canAdmin(user: User) {
  return user.roles.some(({ role }) => ['OWNER', 'HR', 'SECURITY', 'MANAGER'].includes(role));
}
export function adminHome(user: User) {
  if (user.roles.some(({ role }) => role === 'OWNER' || role === 'HR')) return '/admin';
  return user.roles.some(({ role }) => role === 'SECURITY') ? '/admin/monitor' : '/admin/attendance';
}
