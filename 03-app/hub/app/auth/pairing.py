"""Khóa lượt thử ghép theo IP — quyết định người dùng ngày 15/11/2026."""
from dataclasses import dataclass
import asyncio
from threading import Lock
import time
from app.errors import ApiError


@dataclass
class AttemptState:
    failures: int = 0
    locked_until: float = 0


class PairingAttempts:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._states = {}
        self._lock = Lock()
        self._guards = {}

    def serial(self, ip):
        # Các request cùng IP không được xen kẽ check/sai/thành công.
        with self._lock:
            return self._guards.setdefault(ip, asyncio.Lock())

    def _state(self, ip):
        state = self._states.get(ip)
        if state and state.locked_until and self.clock() >= state.locked_until:
            del self._states[ip]
            state = None
        return state

    def check(self, ip):
        with self._lock:
            state = self._state(ip)
            if state and state.locked_until > self.clock():
                raise self.locked_error()

    def failed(self, ip):
        with self._lock:
            state = self._state(ip)
            if state is None:
                state = self._states[ip] = AttemptState()
            state.failures += 1
            if state.failures >= 5:
                if not state.locked_until:
                    state.locked_until = self.clock() + 600
                raise self.locked_error()
        raise ApiError(404, 'PAIRING_INVALID', 'Mã ghép không đúng.')

    def succeeded(self, ip):
        with self._lock:
            self._states.pop(ip, None)

    @staticmethod
    def locked_error():
        return ApiError(429, 'PAIRING_LOCKED', 'Đã nhập sai 5 lần. Lượt thử từ máy này bị khóa trong 10 phút.')
