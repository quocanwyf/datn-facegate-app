import type { components } from '../api/schema';
// Nguồn giao thức: 03-app/openapi/ws-protocol.md §1, không chứa ảnh trả về.
export type Config = { type: 'config'; gate: Pick<components['schemas']['KioskGate'], 'id' | 'name' | 'mode'>; research_banner: string; max_fps: number; frame_long_side: number; jpeg_quality: number; result_display_sec: number; server_time: string };
export type Result = { type: 'result'; seq: number; result: 'OK' | 'ALREADY' | 'DENY'; reason?: 'UNKNOWN' | 'SPOOF' | 'RULE' | 'INACTIVE'; employee?: { name: string; code: string }; attendance?: { kind: 'IN' | 'OUT' | 'NONE'; time?: string; status?: components['schemas']['AttendanceStatus'] }; door: 'OPEN' | 'DENY'; message: string };
export type FrameState = { type: 'state'; seq: number; state: 'NO_FACE' | 'TOO_FAR' | 'LOOK_STRAIGHT' | 'HOLD_STILL' | 'CHECKING' | 'BUSY' | 'NO_GALLERY'; bbox?: [number, number, number, number]; frames_in_window?: number };
export type Progress = { type: 'enroll_progress'; seq: number; accepted: number; total: number; reason?: 'NO_FACE' | 'MULTI_FACE' | 'TOO_SMALL' | 'POSE' | 'SPOOF' | 'TOO_SIMILAR' };
export type Done = { type: 'enroll_done'; profile_id: string; profile_status: 'PENDING_REVIEW'; duplicate_warning: boolean };
export type HubError = { type: 'error'; code: string; message: string; seq?: number };
export type HubMessage = Config | Result | FrameState | Progress | Done | HubError | { type: 'pong' };
export type FrameMode = { mode: 'recognize' } | { mode: 'enroll'; enroll_session_id: string; employee_id: string };

export function hubMessage(data: unknown): HubMessage | undefined {
  if (typeof data !== 'string') return;
  let value: unknown;
  try { value = JSON.parse(data); } catch { return; }
  if (!value || typeof value !== 'object' || !('type' in value)) return;
  const message = value as HubMessage;
  if (message.type === 'config') {
    if (!message.gate?.id || !message.gate.name || !['ATTENDANCE_ACCESS', 'ACCESS_ONLY'].includes(message.gate.mode) || !Number.isFinite(message.max_fps) || message.max_fps <= 0 || !Number.isFinite(message.frame_long_side) || message.frame_long_side <= 0 || !Number.isFinite(message.jpeg_quality) || message.jpeg_quality < 1 || message.jpeg_quality > 100 || !Number.isFinite(message.result_display_sec) || message.result_display_sec <= 0) return;
  } else if (message.type === 'state' || message.type === 'result' || message.type === 'enroll_progress') {
    if (!Number.isInteger(message.seq)) return;
    if (message.type === 'state' && !['NO_FACE', 'TOO_FAR', 'LOOK_STRAIGHT', 'HOLD_STILL', 'CHECKING', 'BUSY', 'NO_GALLERY'].includes(message.state)) return;
    if (message.type === 'result' && (!['OK', 'ALREADY', 'DENY'].includes(message.result) || message.result === 'DENY' && !['UNKNOWN', 'SPOOF', 'RULE', 'INACTIVE'].includes(message.reason ?? ''))) return;
    if (message.type === 'enroll_progress' && (!Number.isInteger(message.accepted) || message.accepted < 0 || message.accepted > 5 || message.total !== 5)) return;
  } else if (!['error', 'enroll_done', 'pong'].includes(message.type)) return;
  if (message.type === 'error' && (typeof message.code !== 'string' || typeof message.message !== 'string' || message.seq !== undefined && !Number.isInteger(message.seq))) return;
  if (message.type === 'enroll_done' && (typeof message.profile_id !== 'string' || message.profile_status !== 'PENDING_REVIEW' || typeof message.duplicate_warning !== 'boolean')) return;
  return message;
}
