from collections import Counter
from concurrent.futures import Future
from queue import Queue
from threading import Lock, Thread


class Busy(RuntimeError):
    code = 'BUSY'


class InferenceWorker:
    """Mọi handler/initializer chạy trên một thread, không chạy trong event loop."""
    def __init__(self, handlers=None, initializer=None):
        self._handlers = dict(handlers or {})
        self._initializer = initializer
        self._queue = Queue()
        self._pending = Counter()
        self._lock = Lock()
        self._closed = False
        self.ready = Future()
        self._thread = Thread(target=self._run, name='facegate-inference', daemon=True)
        self._thread.start()

    def submit(self, kind, payload, *, device_id=None) -> Future:
        future = Future()
        with self._lock:
            if self._closed:
                future.set_exception(RuntimeError('Worker đã đóng'))
            elif device_id is not None and self._pending[device_id] >= 2:
                future.set_exception(Busy('Thiết bị đã có 2 khung chờ'))
            else:
                if device_id is not None:
                    self._pending[device_id] += 1
                self._queue.put((kind, payload, future, device_id))
        return future

    def _run(self):
        try:
            if self._initializer:
                self._handlers.update(self._initializer())
            self.ready.set_result(True)
        except Exception as error:
            self.ready.set_exception(error)
        while True:
            item = self._queue.get()
            if item is None:
                return
            kind, payload, future, device_id = item
            with self._lock:
                if device_id is not None:
                    self._pending[device_id] -= 1
                    if not self._pending[device_id]:
                        del self._pending[device_id]
            if not future.set_running_or_notify_cancel():
                continue
            try:
                self.ready.result()
                result = self._handlers[kind](payload)
                future.set_result(result)
            except Exception as error:
                future.set_exception(error)

    def close(self, timeout=10):
        with self._lock:
            if not self._closed:
                self._closed = True
                self._queue.put(None)
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise TimeoutError('Worker chưa kết thúc')
