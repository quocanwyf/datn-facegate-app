"""Đọc file MXNet RecordIO (train.rec / train.idx của insightface) bằng Python thuần — KHÔNG cần mxnet.

Lý do: mxnet đã ngừng phát triển, khó cài trên Python mới (Kaggle/Colab/Windows).

Định dạng (theo dmlc-core recordio + mxnet.recordio.pack/unpack):
  * train.idx: mỗi dòng "<key>\t<offset byte>".
  * Mỗi record trong train.rec:  uint32 magic (0xCED7230A) | uint32 lrec | payload | đệm tới bội số 4.
      lrec: 29 bit thấp = độ dài payload, 3 bit cao = cflag (0 = record nguyên vẹn).
  * payload = IRHeader (struct '<IfQQ': flag, label, id, id2)
              + nếu flag > 0: flag số float32 (nhãn dạng mảng)
              + bytes ảnh đã mã hoá (JPEG/PNG).
  * Record khoá 0 (insightface): flag > 0, label[0] = 1 + số ảnh  →  ảnh có khoá 1 .. label[0]−1.
    (giống dataset.py của insightface arcface_torch và UniFace: imgidx = range(1, int(header.label[0])))

Pilot sẽ kiểm tra thực tế trên file CASIA thật (số lớp kỳ vọng 10,572).
"""
from __future__ import annotations

import os
import struct
from typing import Dict, List, Tuple

import numpy as np

_MAGIC = 0xCED7230A
_IR_FORMAT = "<IfQQ"
_IR_SIZE = struct.calcsize(_IR_FORMAT)


def unpack_record(payload: bytes) -> Tuple[int, np.ndarray, bytes]:
    """Trả về (flag, label_array, image_bytes)."""
    flag, label, _id, _id2 = struct.unpack(_IR_FORMAT, payload[:_IR_SIZE])
    body = payload[_IR_SIZE:]
    if flag > 0:
        labels = np.frombuffer(body[: flag * 4], dtype=np.float32).copy()
        body = body[flag * 4:]
    else:
        labels = np.array([label], dtype=np.float32)
    return flag, labels, body


def pack_record(label, img_bytes: bytes, idx: int = 0) -> bytes:
    """Ngược với unpack_record (dùng cho test / tạo dữ liệu giả). label: số hoặc list số."""
    if np.isscalar(label):
        header = struct.pack(_IR_FORMAT, 0, float(label), idx, 0)
        payload = header + img_bytes
    else:
        arr = np.asarray(label, dtype=np.float32)
        header = struct.pack(_IR_FORMAT, arr.size, 0.0, idx, 0)
        payload = header + arr.tobytes() + img_bytes
    n = len(payload)
    out = struct.pack("<II", _MAGIC, n & ((1 << 29) - 1)) + payload
    pad = (4 - n % 4) % 4
    return out + b"\x00" * pad


class IndexedRecordReader:
    """Đọc ngẫu nhiên theo khoá. An toàn với DataLoader nhiều worker: mỗi tiến trình tự mở file."""

    def __init__(self, idx_path: str, rec_path: str):
        self.idx_path, self.rec_path = idx_path, rec_path
        self.offsets: Dict[int, int] = {}
        with open(idx_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                k, off = line.split("\t")
                self.offsets[int(k)] = int(off)
        self.keys: List[int] = sorted(self.offsets)
        self._fh = None
        self._pid = None

    def _file(self):
        pid = os.getpid()
        if self._fh is None or self._pid != pid:
            self._fh = open(self.rec_path, "rb")
            self._pid = pid
        return self._fh

    def read(self, key: int) -> bytes:
        fh = self._file()
        fh.seek(self.offsets[key])
        magic, lrec = struct.unpack("<II", fh.read(8))
        if magic != _MAGIC:
            raise IOError(f"sai magic tại khoá {key}: {magic:#x}")
        cflag, length = lrec >> 29, lrec & ((1 << 29) - 1)
        if cflag != 0:
            raise IOError(f"record nhiều phần (cflag={cflag}) chưa hỗ trợ — khoá {key}")
        return fh.read(length)

    def __getstate__(self):  # không pickle file handle sang worker
        d = dict(self.__dict__)
        d["_fh"] = None
        d["_pid"] = None
        return d


def write_rec(rec_path: str, idx_path: str, records: List[Tuple[int, bytes]]):
    """records: [(key, record_bytes)] — dùng cho test."""
    with open(rec_path, "wb") as fr, open(idx_path, "w") as fi:
        for key, rb in records:
            fi.write(f"{key}\t{fr.tell()}\n")
            fr.write(rb)
