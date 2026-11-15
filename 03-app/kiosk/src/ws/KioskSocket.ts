import { hubMessage } from './protocol.ts';
import type { Config, FrameMode, HubMessage } from './protocol';

export interface Transport {
  onopen: (() => void) | null;
  onmessage: ((event: { data: unknown }) => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  send(data: string | ArrayBuffer): void;
  close(): void;
}
export interface Clock {
  now(): number;
  setTimeout(callback: () => void, delay: number): unknown;
  clearTimeout(timer: unknown): void;
}
const systemClock: Clock = { now: () => Date.now(), setTimeout: (callback, delay) => setTimeout(callback, delay), clearTimeout: timer => clearTimeout(timer as ReturnType<typeof setTimeout>) };
export type Connection = { connected: boolean; offline: boolean; attempt: number; unavailable?: string };
type Callbacks = { onMessage(message: HubMessage): void; onConnection(value: Connection): void; onRevoked(): void };
const backoff = [1000, 2000, 4000, 8000, 15000];

export class KioskSocket {
  private transport?: Transport;
  private generation = 0;
  private started = false;
  private connected = false;
  private offline = false;
  private captureEnabled = true;
  private unavailable?: string;
  private retryIndex = 0;
  private seq = 0;
  private awaiting?: { seq: number; mode: FrameMode['mode'] };
  private holdUntil = 0;
  private nextFrameAt = 0;
  private lastSentAt = -Infinity;
  private retryTimer?: unknown;
  private graceTimer?: unknown;
  private watchdog?: unknown;
  private pingTimer?: unknown;
  config?: Config;
  private readonly url: string;
  private readonly token: string;
  private readonly factory: (url: string) => Transport;
  private readonly callbacks: Callbacks;
  private readonly clock: Clock;

  constructor(hub: string, token: string, callbacks: Callbacks, factory: (url: string) => Transport, clock: Clock = systemClock) {
    this.url = hub.replace(/\/$/, '').replace(/^http/, 'ws') + '/api/v1/ws/kiosk';
    this.token = token; this.callbacks = callbacks; this.factory = factory; this.clock = clock;
  }
  start() {
    if (this.started) return;
    this.started = true; this.retryIndex = 0; this.connect();
  }
  stop() {
    this.started = false; this.generation++; this.connected = false; this.awaiting = undefined;
    this.clear('retryTimer'); this.clear('graceTimer'); this.clear('watchdog'); this.clear('pingTimer');
    this.transport?.close(); this.transport = undefined; this.config = undefined;
    this.holdUntil = 0; this.nextFrameAt = 0; this.lastSentAt = -Infinity; this.offline = false; this.unavailable = undefined;
  }
  restart() { this.stop(); this.start(); }
  setCaptureEnabled(enabled: boolean) { this.captureEnabled = enabled; }
  canSend(mode: FrameMode['mode'] = 'recognize') {
    return this.started && this.connected && this.captureEnabled && !!this.config && !this.awaiting && !(this.unavailable && mode === 'recognize') && this.clock.now() >= Math.max(this.holdUntil, this.nextFrameAt);
  }
  sendFrame(jpeg: ArrayBuffer, mode: FrameMode = { mode: 'recognize' }): boolean {
    if (!this.canSend(mode.mode) || !jpeg.byteLength) return false;
    const seq = ++this.seq;
    this.awaiting = { seq, mode: mode.mode };
    this.lastSentAt = this.clock.now(); this.nextFrameAt = this.lastSentAt + 1000 / this.config!.max_fps;
    try {
      // Cặp header/binary được gửi đồng bộ, không chen ping hoặc await vào giữa.
      this.transport!.send(JSON.stringify({ type: 'frame', seq, ...mode })); this.transport!.send(jpeg);
      return true;
    } catch { this.lost(false); return false; }
  }
  private clear(key: 'retryTimer' | 'graceTimer' | 'watchdog' | 'pingTimer') {
    if (this[key] !== undefined) this.clock.clearTimeout(this[key]); this[key] = undefined;
  }
  private publish() { this.callbacks.onConnection({ connected: this.connected, offline: this.offline, attempt: this.retryIndex, unavailable: this.unavailable }); }
  private connect() {
    if (!this.started) return;
    const generation = ++this.generation;
    this.connected = false; this.config = undefined; this.seq = 0; this.awaiting = undefined; this.publish();
    this.armWatchdog();
    let socket: Transport;
    try { socket = this.factory(this.url); } catch { this.lost(false); return; }
    this.transport = socket;
    const current = () => this.started && generation === this.generation;
    socket.onopen = () => {
      if (!current()) return;
      try { socket.send(JSON.stringify({ type: 'auth', device_token: this.token, app_version: '1.0.0' })); this.lastSentAt = this.clock.now(); this.ping(); }
      catch { this.lost(false); }
    };
    socket.onmessage = event => { if (current()) this.receive(event.data); };
    socket.onclose = () => { if (current()) this.lost(false); };
    socket.onerror = () => { if (current()) this.lost(false); };
  }
  private armWatchdog() {
    this.clear('watchdog');
    this.watchdog = this.clock.setTimeout(() => { this.watchdog = undefined; if (this.started) this.lost(true); }, 15000);
  }
  private ping() {
    this.clear('pingTimer');
    const delay = Math.max(1, 10000 - (this.clock.now() - this.lastSentAt));
    this.pingTimer = this.clock.setTimeout(() => {
      this.pingTimer = undefined;
      if (!this.started || !this.transport) return;
      if (this.clock.now() - this.lastSentAt >= 10000) {
        try { this.transport.send(JSON.stringify({ type: 'ping' })); this.lastSentAt = this.clock.now(); }
        catch { this.lost(false); return; }
      }
      this.ping();
    }, delay);
  }
  private receive(data: unknown) {
    const message = hubMessage(data); if (!message) return;
    this.armWatchdog();
    if (message.type === 'config') {
      this.config = message; this.connected = true; this.offline = false; this.unavailable = undefined; this.retryIndex = 0;
      this.clear('graceTimer'); this.clear('retryTimer'); this.publish();
    } else if (message.type === 'error' && ['DEVICE_REVOKED', 'TOKEN_INVALID'].includes(message.code)) {
      this.stop(); this.callbacks.onRevoked(); return;
    } else if (message.type === 'state' || message.type === 'result' || message.type === 'enroll_progress') {
      if (message.seq !== this.awaiting?.seq) return;
      this.awaiting = undefined;
      if (message.type === 'state' && message.state === 'BUSY') this.nextFrameAt = Math.max(this.nextFrameAt, this.clock.now() + 200);
      if (message.type === 'result') this.holdUntil = this.clock.now() + this.config!.result_display_sec * 1000;
    } else if (message.type === 'enroll_done') {
      if (this.awaiting?.mode !== 'enroll') return;
      this.awaiting = undefined; this.captureEnabled = false;
    } else if (message.type === 'error') {
      if (message.seq !== undefined && message.seq !== this.awaiting?.seq) return;
      if (message.seq !== undefined && message.seq === this.awaiting?.seq) this.awaiting = undefined;
      if (['RECOGNITION_UNAVAILABLE', 'MODEL_NOT_VERIFIED'].includes(message.code)) { this.unavailable = message.message; this.publish(); }
    }
    this.callbacks.onMessage(message);
  }
  private lost(immediate: boolean) {
    if (!this.started) return;
    this.generation++; this.connected = false; this.config = undefined; this.awaiting = undefined;
    this.clear('watchdog'); this.clear('pingTimer');
    const socket = this.transport; this.transport = undefined; socket?.close();
    if (immediate) { this.offline = true; this.clear('graceTimer'); }
    else if (!this.offline && this.graceTimer === undefined) {
      this.graceTimer = this.clock.setTimeout(() => { this.graceTimer = undefined; if (this.started && !this.connected) { this.offline = true; this.publish(); } }, 3000);
    }
    this.publish();
    if (this.retryTimer !== undefined) return;
    const delay = backoff[Math.min(this.retryIndex, backoff.length - 1)]!;
    this.retryIndex++;
    this.retryTimer = this.clock.setTimeout(() => { this.retryTimer = undefined; this.connect(); }, delay);
  }
}
