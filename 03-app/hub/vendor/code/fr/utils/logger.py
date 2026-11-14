"""Ghi log CSV (mỗi log_every bước) + JSONL (eval, sự kiện). Mở ở chế độ append → resume ghi tiếp."""
import csv
import json
import os
import time


class CSVLogger:
    def __init__(self, path: str, fields):
        self.path, self.fields = path, list(fields)
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        self._f = open(path, "a", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._f, fieldnames=self.fields, extrasaction="ignore")
        if new:
            self._w.writeheader()
            self._f.flush()

    def log(self, row: dict):
        self._w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in row.items()})
        self._f.flush()

    def close(self):
        self._f.close()


def append_jsonl(path: str, obj: dict):
    obj = dict(obj)
    obj.setdefault("time", time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
