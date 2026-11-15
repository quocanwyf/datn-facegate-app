import test from 'node:test';
import assert from 'node:assert/strict';
import { KioskSocket } from './KioskSocket.ts';
import type { Clock, Connection, Transport } from './KioskSocket.ts';
import type { Config, HubMessage } from './protocol.ts';
class FakeClock implements Clock {
  time = 0; serial = 0; timers = new Map<number, { at: number; callback: () => void }>();
  now() { return this.time; }
  setTimeout(callback: () => void, delay: number) { const id = ++this.serial; this.timers.set(id, { at: this.time + delay, callback }); return id; }
  clearTimeout(timer: unknown) { this.timers.delete(timer as number); }
  tick(delay: number) {
    const target = this.time + delay;
    while (true) {
      const next = [...this.timers.entries()].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
      if (!next) break;
      this.time = next[1].at; this.timers.delete(next[0]); next[1].callback();
    }
    this.time = target;
  }
}
class FakeSocket implements Transport {
  onopen: (() => void) | null = null; onmessage: ((event: { data: unknown }) => void) | null = null;
  onerror: (() => void) | null = null; onclose: (() => void) | null = null;
  sent: (string | ArrayBuffer)[] = []; closed = false;
  send(value: string | ArrayBuffer) { this.sent.push(value); }
  close() { this.closed = true; this.onclose?.(); }
  emit(value: unknown) { this.onmessage?.({ data: JSON.stringify(value) }); }
}
const config: Config = { type: 'config', gate: { id: 'gate', name: 'Cửa kiểm thử', mode: 'ACCESS_ONLY' }, research_banner: 'Bản trình diễn nghiên cứu', max_fps: 4, frame_long_side: 640, jpeg_quality: 80, result_display_sec: 3, server_time: '2026-11-15T12:00:00+07:00' };
const jpeg = new ArrayBuffer(8);
function setup() {
  const clock = new FakeClock(); const sockets: FakeSocket[] = []; const times: number[] = []; const urls: string[] = [];
  const states: Connection[] = []; const messages: HubMessage[] = []; let revoked = 0;
  const client = new KioskSocket('http://10.0.2.2:8000/', 'test-token', { onMessage: value => messages.push(value), onConnection: value => states.push(value), onRevoked: () => revoked++ }, url => { urls.push(url); times.push(clock.now()); const socket = new FakeSocket(); sockets.push(socket); return socket; }, clock);
  client.start(); const socket = sockets[0]!;
  const ready = () => { socket.onopen?.(); socket.emit(config); };
  return { client, clock, socket, sockets, times, urls, states, messages, ready, revoked: () => revoked };
}
test('auth là message đầu, token không nằm trên URL; không gửi trước config', () => {
  const s = setup(); assert.equal(s.client.sendFrame(jpeg), false); s.socket.onopen?.();
  assert.equal(s.urls[0], 'ws://10.0.2.2:8000/api/v1/ws/kiosk');
  assert.deepEqual(JSON.parse(s.socket.sent[0] as string), { type: 'auth', device_token: 'test-token', app_version: '1.0.0' });
  assert.equal(s.client.canSend(), false); s.socket.emit(config); assert.equal(s.client.canSend(), true);
});
test('header/binary liền nhau; chỉ một frame chờ; config/pong/seq khác không nhả khóa', () => {
  const s = setup(); s.ready(); assert.equal(s.client.sendFrame(jpeg), true);
  assert.deepEqual(JSON.parse(s.socket.sent[1] as string), { type: 'frame', seq: 1, mode: 'recognize' }); assert.equal(s.socket.sent[2], jpeg);
  s.clock.tick(1000); s.socket.emit(config); s.socket.emit({ type: 'pong' }); s.socket.emit({ type: 'state', seq: 99, state: 'NO_FACE' });
  assert.equal(s.client.sendFrame(jpeg), false); s.socket.emit({ type: 'state', seq: 1, state: 'NO_FACE' }); assert.equal(s.client.sendFrame(jpeg), true);
});
test('tuân thủ max_fps và BUSY ít nhất 200ms sau ACK', () => {
  const s = setup(); s.ready(); s.client.sendFrame(jpeg); s.clock.tick(100); s.socket.emit({ type: 'state', seq: 1, state: 'BUSY' });
  s.clock.tick(199); assert.equal(s.client.canSend(), false); s.clock.tick(1); assert.equal(s.client.sendFrame(jpeg), true);
  s.socket.emit({ type: 'state', seq: 2, state: 'CHECKING' }); s.clock.tick(249); assert.equal(s.client.canSend(), false); s.clock.tick(1); assert.equal(s.client.canSend(), true);
});
test('không gửi frame trong 3s hiện kết quả, kể cả có config mới', () => {
  for (const seconds of [1, 5]) {
    const s = setup(); s.ready(); s.client.sendFrame(jpeg); s.socket.emit({ type: 'result', seq: 1, result: 'OK', door: 'OPEN', message: 'Mời vào' });
    s.socket.emit({ ...config, result_display_sec: seconds });
    s.clock.tick(2999); assert.equal(s.client.sendFrame(jpeg), false); s.clock.tick(1); assert.equal(s.client.canSend(), true);
  }
});
test('enroll_progress nhả đúng seq; enroll_done không seq chỉ nhận khi chờ enroll', () => {
  const s = setup(); s.ready(); const mode = { mode: 'enroll', enroll_session_id: 'session', employee_id: 'employee' } as const;
  s.client.sendFrame(jpeg, mode); s.socket.emit({ type: 'enroll_progress', seq: 1, accepted: 4, total: 5 }); s.clock.tick(250); assert.equal(s.client.sendFrame(jpeg, mode), true);
  s.socket.emit({ type: 'enroll_done', profile_id: 'profile', profile_status: 'PENDING_REVIEW', duplicate_warning: false }); assert.equal(s.client.canSend('enroll'), false);
  assert.equal(s.messages.at(-1)?.type, 'enroll_done');
});
test('error frame giải phóng đúng seq; NO_GALLERY không biến thành DENY', () => {
  const s = setup(); s.ready(); s.client.sendFrame(jpeg); s.socket.emit({ type: 'error', seq: 99, code: 'FRAME_DECODE_FAILED', message: 'Bỏ khung' }); s.clock.tick(250); assert.equal(s.client.canSend(), false);
  s.socket.emit({ type: 'error', seq: 1, code: 'FRAME_DECODE_FAILED', message: 'Bỏ khung' }); assert.equal(s.client.sendFrame(jpeg), true);
  s.socket.emit({ type: 'state', seq: 2, state: 'NO_GALLERY' }); assert.equal(s.messages.at(-1)?.type, 'state');
});
test('gallery lỗi dừng recognize, giữ ping; config phục hồi mới cho gửi', () => {
  const s = setup(); s.ready(); s.client.sendFrame(jpeg); s.socket.emit({ type: 'error', seq: 1, code: 'RECOGNITION_UNAVAILABLE', message: 'Tạm ngưng nhận dạng' }); s.clock.tick(10000);
  assert.equal(s.client.sendFrame(jpeg), false); assert.equal(JSON.parse(s.socket.sent.at(-1) as string).type, 'ping');
  s.socket.emit(config); assert.equal(s.client.canSend(), true);
});

test('khung gửi giữa chu kỳ không làm ping trễ tới 20s và rớt timeout Hub', () => {
  const s = setup(); s.ready(); s.clock.tick(1000); s.client.sendFrame(jpeg);
  s.socket.emit({ type: 'state', seq: 1, state: 'NO_FACE' });
  s.clock.tick(9999); assert.equal(s.socket.sent.length, 3);
  s.clock.tick(1); assert.equal(JSON.parse(s.socket.sent.at(-1) as string).type, 'ping');
  assert.equal(s.clock.now(), 11000);
});
test('disconnect chưa đủ 3s không hiện offline; nối lại trước mốc không nháy K11', () => {
  const s = setup(); s.ready(); s.socket.close(); assert.equal(s.states.at(-1)?.offline, false);
  s.clock.tick(1000); const next = s.sockets[1]!; next.onopen?.(); next.emit(config); s.clock.tick(2000);
  assert.equal(s.states.some(value => value.offline), false); assert.equal(s.client.canSend(), true);
});
test('disconnect kéo dài hiện offline đúng 3s', () => {
  const s = setup(); s.ready(); s.socket.close(); s.clock.tick(2999); assert.equal(s.states.at(-1)?.offline, false); s.clock.tick(1); assert.equal(s.states.at(-1)?.offline, true);
});
test('im lặng 15s hiện offline ngay, không cộng thêm 3s; pong reset watchdog', () => {
  const s = setup(); s.ready(); s.clock.tick(10000); s.socket.emit({ type: 'pong' }); s.clock.tick(14999); assert.equal(s.states.at(-1)?.offline, false);
  s.clock.tick(1); assert.equal(s.states.at(-1)?.offline, true); assert.equal(s.clock.now(), 25000);
});
test('retry 1/2/4/8/15/15s, một socket mỗi lượt', () => {
  const s = setup(); s.ready(); s.socket.close();
  for (const delay of [1000, 2000, 4000, 8000, 15000, 15000]) { const count = s.sockets.length; s.clock.tick(delay - 1); assert.equal(s.sockets.length, count); s.clock.tick(1); s.sockets.at(-1)!.onerror?.(); }
  assert.deepEqual(s.times, [0, 1000, 3000, 7000, 15000, 30000, 45000]);
});
test('thu hồi token dừng mọi timer và báo xóa token; callback socket cũ bị bỏ', () => {
  const s = setup(); s.ready(); s.socket.emit({ type: 'error', code: 'DEVICE_REVOKED', message: 'Thu hồi' }); s.clock.tick(60000);
  assert.equal(s.revoked(), 1); assert.equal(s.sockets.length, 1); assert.equal(s.clock.timers.size, 0); assert.equal(s.client.canSend(), false);
  s.socket.emit(config); assert.equal(s.client.canSend(), false);
});
test('tắt capture và restart bỏ phiên/seq cũ, không gửi khi đang thao tác form', () => {
  const s = setup(); s.ready(); s.client.setCaptureEnabled(false); assert.equal(s.client.sendFrame(jpeg), false); s.client.restart();
  const next = s.sockets[1]!; next.onopen?.(); next.emit(config); s.socket.emit({ type: 'result', seq: 1, result: 'DENY', reason: 'UNKNOWN', door: 'DENY', message: 'Bỏ' });
  assert.equal(s.client.canSend(), false); s.client.setCaptureEnabled(true); assert.equal(s.client.sendFrame(jpeg), true); assert.equal(JSON.parse(next.sent[1] as string).seq, 1);
});
