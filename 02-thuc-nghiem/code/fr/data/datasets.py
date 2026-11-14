"""Dataset train: RecordIO của insightface, thư mục ảnh (id_x/*.jpg), hoặc dữ liệu giả (smoke test).

Tiền xử lý giống insightface arcface_torch & UniFace: RGB, lật ngang ngẫu nhiên (p=0.5),
chuẩn hoá (x/255 − 0.5)/0.5 → [−1, 1]. KHÔNG thêm augmentation khác (đề tài không đi hướng dữ liệu).

B3 (DDP): ``EpochSampler`` trả về cặp ``(chỉ_số_ảnh, cờ_lật)``; cờ lật sinh từ CÙNG generator (seed, epoch)
với hoán vị → mỗi ảnh được lật hay không là cố định theo (seed, epoch), không phụ thuộc số GPU / số worker.
Gọi ``ds[i]`` với số nguyên (notebook, test) vẫn lật ngẫu nhiên bằng np.random như cũ.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset, Sampler

from .recordio import IndexedRecordReader, unpack_record

try:
    import cv2  # nhanh hơn PIL khi giải mã JPEG
    cv2.setNumThreads(0)
except Exception:  # pragma: no cover
    cv2 = None


def decode_image(buf: bytes) -> np.ndarray:
    """bytes JPEG/PNG → ndarray HxWx3 uint8 RGB."""
    if cv2 is not None:
        img = cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("không giải mã được ảnh")
        return img[:, :, ::-1]
    from PIL import Image
    import io
    return np.asarray(Image.open(io.BytesIO(buf)).convert("RGB"))


def _unpack_index(i):
    """``i`` là int (lật ngẫu nhiên np.random) hoặc (int, bool) từ EpochSampler (lật do sampler quyết định)."""
    if isinstance(i, (tuple, list)):
        return int(i[0]), bool(i[1])
    return int(i), None


def to_tensor(img: np.ndarray, flip: bool = False) -> torch.Tensor:
    if flip:
        img = img[:, ::-1, :]
    t = torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float()
    return t.div_(255.0).sub_(0.5).div_(0.5)


class RecordFaceDataset(Dataset):
    """insightface ``faces_*_112x112/train.rec`` (ví dụ CASIA-WebFace)."""

    def __init__(self, root: str, random_flip: bool = True):
        rec, idx = os.path.join(root, "train.rec"), os.path.join(root, "train.idx")
        self.reader = IndexedRecordReader(idx, rec)
        self.random_flip = random_flip
        flag, lab, _ = unpack_record(self.reader.read(0)) if 0 in self.reader.offsets else (0, None, None)
        if flag > 0:
            self.imgidx = np.arange(1, int(lab[0]), dtype=np.int64)
        else:
            self.imgidx = np.array([k for k in self.reader.keys], dtype=np.int64)
        self._num_classes: Optional[int] = None
        prop = os.path.join(root, "property")
        if os.path.exists(prop):  # "num_classes,112,112"
            try:
                self._num_classes = int(open(prop).read().strip().split(",")[0])
            except Exception:
                pass

    def __len__(self):
        return len(self.imgidx)

    def label_of(self, i: int) -> int:
        _, lab, _ = unpack_record(self.reader.read(int(self.imgidx[i])))
        return int(lab[0])

    @property
    def num_classes(self) -> int:
        if self._num_classes is None:   # chậm: quét toàn bộ nhãn (chỉ khi thiếu file property)
            self._num_classes = 1 + max(self.label_of(i) for i in range(len(self)))
        return self._num_classes

    def __getitem__(self, i):
        i, flip = _unpack_index(i)
        _, lab, img = unpack_record(self.reader.read(int(self.imgidx[i])))
        flip = self.random_flip and (np.random.rand() < 0.5 if flip is None else flip)
        return to_tensor(decode_image(img), flip), int(lab[0])


class ImageFolderFaceDataset(Dataset):
    """Thư mục ``root/<id>/*.jpg`` (vd. bản Kaggle yakhyokhuja/webface-112x112). Nhãn = thứ tự tên thư mục."""

    def __init__(self, root: str, random_flip: bool = True):
        classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
        self.samples: List[Tuple[str, int]] = []
        for c, d in enumerate(classes):
            for f in sorted(os.listdir(os.path.join(root, d))):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    self.samples.append((os.path.join(root, d, f), c))
        self.num_classes = len(classes)
        self.random_flip = random_flip

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        i, flip = _unpack_index(i)
        p, c = self.samples[i]
        with open(p, "rb") as f:
            img = decode_image(f.read())
        flip = self.random_flip and (np.random.rand() < 0.5 if flip is None else flip)
        return to_tensor(img, flip), c


class SyntheticFaceDataset(Dataset):
    """Dữ liệu giả cố định theo seed — chỉ để smoke test / đo tốc độ thuần GPU."""

    def __init__(self, num_images: int = 256, num_classes: int = 16, size: int = 112, seed: int = 0):
        g = torch.Generator().manual_seed(seed)
        self.labels = torch.randint(0, num_classes, (num_images,), generator=g)
        self.num_classes = num_classes
        self.size = size
        self.seed = seed

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        i, _ = _unpack_index(i)            # dữ liệu giả: không lật (giữ giống bản cũ)
        g = torch.Generator().manual_seed(self.seed * 100003 + i)
        x = torch.rand(3, self.size, self.size, generator=g) * 2 - 1
        return x, int(self.labels[i])


def build_train_dataset(cfg: dict) -> Dataset:
    kind = cfg.get("type", "rec")
    if kind == "rec":
        return RecordFaceDataset(cfg["root"])
    if kind == "folder":
        return ImageFolderFaceDataset(cfg["root"])
    if kind == "synthetic":
        return SyntheticFaceDataset(int(cfg.get("num_images", 256)), int(cfg.get("num_classes", 16)),
                                    int(cfg.get("size", 112)), int(cfg.get("seed", 0)))
    raise ValueError(kind)


class EpochSampler(Sampler):
    """Hoán vị cố định theo (seed, epoch) → resume giữa epoch tái lập ĐÚNG thứ tự dữ liệu.

    Một "bước" (iteration) = một batch TOÀN CỤC ``batch_size`` (= batch hiệu dụng, vd 512) lấy liên tiếp
    trong hoán vị. Với DDP (world_size = W), tiến trình ``rank`` lấy lát ``[rank·B/W, (rank+1)·B/W)`` của
    MỖI batch toàn cục → hợp các lát của W tiến trình đúng bằng batch của bản 1 GPU ở cùng bước
    (cùng ảnh, cùng cờ lật). Vì vậy đổi 1 ↔ 2 GPU không đổi phân phối dữ liệu theo epoch, và resume
    được chéo số GPU (start_batch đếm theo batch toàn cục).

    Mỗi phần tử trả về: (chỉ_số_ảnh, cờ_lật). Cờ lật sinh SAU hoán vị từ cùng generator, nên hoán vị
    giống hệt bản pilot (bản pilot chỉ trả chỉ số và lật bằng np.random trong worker).
    start_batch: bỏ qua các batch (toàn cục) đã chạy trước khi bị ngắt.
    """

    def __init__(self, n: int, batch_size: int, seed: int, epoch: int = 0, start_batch: int = 0,
                 rank: int = 0, world_size: int = 1):
        if batch_size % world_size:
            raise ValueError(f"batch toàn cục {batch_size} không chia hết cho world_size {world_size}")
        self.n, self.bs, self.seed = n, batch_size, seed
        self.rank, self.world = rank, world_size
        self.local_bs = batch_size // world_size
        self.set_epoch(epoch, start_batch)

    def set_epoch(self, epoch: int, start_batch: int = 0):
        self.epoch, self.start_batch = epoch, start_batch

    def batches_per_epoch(self) -> int:
        return self.n // self.bs  # drop_last

    def global_order(self):
        """(hoán vị đã cắt theo drop_last, cờ lật) của cả epoch — dùng chung cho mọi rank."""
        g = torch.Generator().manual_seed(self.seed * 1000 + self.epoch)
        perm = torch.randperm(self.n, generator=g)[: self.batches_per_epoch() * self.bs]
        flips = torch.rand(perm.numel(), generator=g) < 0.5
        return perm, flips

    def __iter__(self):
        perm, flips = self.global_order()
        nb, B, L = self.batches_per_epoch(), self.bs, self.local_bs
        perm = perm.view(nb, B)[self.start_batch:, self.rank * L:(self.rank + 1) * L].reshape(-1).tolist()
        flips = flips.view(nb, B)[self.start_batch:, self.rank * L:(self.rank + 1) * L].reshape(-1).tolist()
        return iter(zip(perm, flips))

    def __len__(self):
        return (self.batches_per_epoch() - self.start_batch) * self.local_bs
