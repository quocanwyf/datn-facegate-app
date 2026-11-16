"""Timing nội bộ opt-in; không lưu khung/bbox/embedding hay thêm trường giao thức."""
from contextlib import contextmanager
import time
import torch


class FrameTiming:
    def __init__(self, device):
        self.device = torch.device(device)
        self.values = {}
        self.sync()
        self.begin = time.perf_counter()

    def sync(self):
        if self.device.type == 'cuda': torch.cuda.synchronize(self.device)

    @contextmanager
    def stage(self, name):
        self.sync(); begin = time.perf_counter()
        try:
            yield
        finally:
            self.sync(); self.values[name] = (time.perf_counter()-begin)*1000

    def finish(self):
        self.sync()
        return dict(stages_ms=self.values, total_ms=(time.perf_counter()-self.begin)*1000)
