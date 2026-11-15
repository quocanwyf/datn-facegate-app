"""Một reload không được giải phóng pause của thao tác sinh trắc khác."""
from threading import Event,Lock


class MutationBarrier:
    def __init__(self):
        self.paused=Event()
        self._lock=Lock()
        self._generation=0
        self._pending={}

    def begin(self,key,supersede_prefix=None):
        with self._lock:
            completed={name:token for name,token in self._pending.items() if supersede_prefix and name.startswith(supersede_prefix)}
            self._generation+=1
            self._pending[str(key)]=self._generation
            self.paused.set()
            completed[str(key)]=self._generation
            return completed

    def pending(self,key):
        with self._lock:
            return str(key) in self._pending

    def snapshot(self):
        with self._lock:return self._generation

    def finish_reload(self,generation,completed):
        with self._lock:
            for key,token in completed.items():
                if self._pending.get(str(key))==token:self._pending.pop(str(key))
            ready=not self._pending and generation==self._generation
            if ready:self.paused.clear()
            else:self.paused.set()
            return ready
