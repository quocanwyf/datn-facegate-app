"""Tiện ích DDP (DistributedDataParallel) — chạy được cả 1 tiến trình (python train.py) lẫn torchrun.

    torchrun --standalone --nproc_per_node=2 train.py --config ...      # Kaggle "GPU T4 x2"
    python train.py --config ...                                        # 1 GPU / CPU (như bản pilot)

torchrun đặt biến môi trường RANK, WORLD_SIZE, LOCAL_RANK. Không có các biến này → chế độ 1 tiến trình,
mọi hàm dưới đây trở thành no-op, hành vi giống hệt bản pilot.
Backend: NCCL khi có CUDA, Gloo khi chạy CPU (dùng cho unit test DDP trên máy không có GPU).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import torch
import torch.distributed as dist


@dataclass
class DistInfo:
    enabled: bool
    rank: int
    world_size: int
    local_rank: int

    @property
    def is_main(self) -> bool:
        return self.rank == 0


def init_distributed(device_pref: str = "auto") -> DistInfo:
    if "RANK" not in os.environ or int(os.environ.get("WORLD_SIZE", "1")) <= 1:
        return DistInfo(False, 0, 1, 0)
    rank, world, local = int(os.environ["RANK"]), int(os.environ["WORLD_SIZE"]), int(os.environ["LOCAL_RANK"])
    use_cuda = torch.cuda.is_available() and device_pref != "cpu"
    if use_cuda:
        torch.cuda.set_device(local)
    if not dist.is_initialized():
        dist.init_process_group(backend="nccl" if use_cuda else "gloo")
    return DistInfo(True, rank, world, local)


def barrier(di: DistInfo):
    if di.enabled:
        dist.barrier()


def all_reduce_mean(x: float, di: DistInfo, device) -> float:
    """Trung bình một số thực giữa các tiến trình (chỉ để GHI LOG, không ảnh hưởng gradient)."""
    if not di.enabled:
        return float(x)
    t = torch.tensor([float(x)], dtype=torch.float64 if device.type == "cpu" else torch.float32, device=device)
    dist.all_reduce(t, op=dist.ReduceOp.SUM)
    return float(t.item()) / di.world_size


def all_gather_cat(t: torch.Tensor, di: DistInfo) -> torch.Tensor:
    """Nối tensor (cùng kích thước) của mọi tiến trình theo thứ tự rank → giống batch toàn cục của bản 1 GPU."""
    if not di.enabled:
        return t
    out = [torch.empty_like(t) for _ in range(di.world_size)]
    dist.all_gather(out, t.contiguous())
    return torch.cat(out)


@torch.no_grad()
def average_bn_buffers(module: torch.nn.Module, di: DistInfo):
    """Lấy TRUNG BÌNH running_mean / running_var của mọi lớp BatchNorm giữa các GPU (trước val / ghi checkpoint).
    Lý do: train dùng broadcast_buffers=False nên mỗi GPU cập nhật running stats trên micro-batch của riêng nó;
    nếu chỉ dùng của rank 0 thì ước lượng dựa trên một nửa dữ liệu. Trung bình 2 GPU gần với bản 1 GPU hơn
    (vẫn không bit-exact: thứ tự cập nhật trung bình trượt khác). Không ảnh hưởng tới gradient/trọng số."""
    if not di.enabled:
        return
    for m in module.modules():
        if isinstance(m, torch.nn.modules.batchnorm._BatchNorm) and m.track_running_stats:
            for b in (m.running_mean, m.running_var):
                if b is not None:
                    dist.all_reduce(b, op=dist.ReduceOp.SUM)
                    b.div_(di.world_size)


def cleanup(di: DistInfo):
    if di.enabled and dist.is_initialized():
        dist.destroy_process_group()
