"""Train nhận dạng khuôn mặt: iResNet + head (softmax / cosface / arcface / uniface / bce / sphereface2).

Ví dụ:
    python train.py --config configs/tk1/e28/r18_arcface_m0.5_s1.yaml                  # 1 GPU (hoặc CPU)
    torchrun --standalone --nproc_per_node=2 train.py --config configs/tk1/e28/...      # DDP 2 GPU (Kaggle T4 x2)
    python train.py --config ... --set train.max_iters=300 run_name=thu
    python train.py --config ... --resume auto        # tự tìm <output_dir>/<run_name>/checkpoints/last.pt

Thuật ngữ: "iteration"/"step" = MỘT bước tối ưu với batch hiệu dụng TOÀN CỤC
    eff_batch = train.global_batch (nếu có) hoặc micro_batch × accum_steps (cách ghi cũ, bản pilot).
Mỗi tiến trình (GPU) xử lý eff_batch / W ảnh mỗi bước, chia thành các micro-batch ``micro_batch`` ảnh
→ số bước tích luỹ trên mỗi GPU = eff_batch / (W · micro_batch).

DDP — vì sao kết quả tương đương bản 1 GPU (giải thích chi tiết trong README, mục B3):
  * Dữ liệu: EpochSampler chia MỖI batch toàn cục thành W lát liên tiếp → cùng ảnh, cùng cờ lật ở cùng bước.
  * Gradient: loss mỗi micro-batch nhân n_micro / (eff_batch / W); DDP lấy TRUNG BÌNH gradient của W tiến
    trình → tổng = Σ_mọi ảnh ∂loss/(eff_batch), đúng bằng bản 1 GPU.
  * BatchNorm: giữ micro_batch như bản 1 GPU → mỗi lần forward BN thấy đúng micro_batch ảnh (không SyncBN).
  * Head (W, b của UniFace/SphereFace2/BCE) nằm TRONG mô-đun DDP → gradient của b (tham số chung) được
    all-reduce như mọi tham số; mọi GPU khởi tạo giống nhau (DDP phát từ rank 0) và nhận cùng cập nhật
    → b đồng bộ tuyệt đối. Biến thể r < 1 (lấy mẫu lớp): nhãn được all_gather → mọi GPU chọn cùng tập lớp.
  * Clip gradient, GradScaler, momentum theo hàng (UniFace r): chạy SAU all-reduce trên gradient giống hệt
    nhau → quyết định giống nhau ở mọi GPU.
Validation (data.val.enabled): tách CASIA theo DANH TÍNH (fr/data/casia_split.py) — ~5% người làm val, phần còn
lại train (nhãn đánh lại). Mỗi ``eval.val_every_epochs`` epoch đo TAR@FAR trên mọi cặp ảnh val; giữ
checkpoint ``best.pt`` theo ``eval.best_metric`` (mặc định tar@far=0.001). Tập test (.bin) không dùng để chọn gì.
Đầu ra (chỉ rank 0 ghi) trong <output_dir>/<run_name>/:
    config.yaml, run_info.json, train_log.csv, val.jsonl, val_images.csv, eval.jsonl (.bin, nếu bật),
    events.jsonl, summary.json, checkpoints/last.pt (mỗi ckpt_every_iters bước + cuối mỗi epoch),
    checkpoints/best.pt (best trên validation), checkpoints/epoch_XX.pt (backbone+head).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fr.backbones import get_backbone                          # noqa: E402
from fr.data import casia_split as CS                         # noqa: E402
from fr.data.datasets import EpochSampler, build_train_dataset  # noqa: E402
from fr.eval.val_casia import evaluate_val, load_val_u8         # noqa: E402
from fr.eval.verification import evaluate_bins                  # noqa: E402
from fr.heads import UnifiedCEHead, build_head                  # noqa: E402
from fr.utils import dist as D                                  # noqa: E402
from fr.utils.checkpoint import load_checkpoint, save_checkpoint  # noqa: E402
from fr.utils.config import code_fingerprint, config_fingerprint, dump_config, load_config  # noqa: E402
from fr.utils.logger import CSVLogger, append_jsonl             # noqa: E402
from fr.utils.seed import rng_state, set_rng_state, set_seed, worker_init_fn  # noqa: E402

LOG_FIELDS = ["global_step", "epoch", "step_in_epoch", "lr", "loss", "b", "t_eq23", "t_eq30", "t_sf2",
              "cos_pos_mean", "cos_neg_max_mean", "grad_norm", "amp_scale", "sec_per_iter",
              "img_per_sec", "data_wait_frac", "n_iters_window", "vram_alloc_max_mb", "vram_reserved_max_mb"]


def lr_at(cfg_train: dict, global_step: int, steps_per_epoch: int) -> float:
    """LR theo bước: warmup tuyến tính (tuỳ chọn) rồi giảm ×gamma tại các epoch trong lr_steps.

    lr_steps tính theo EPOCH (epoch_f = global_step / steps_per_epoch) — KHÔNG phụ thuộc max_iters,
    nên chạy thử ngắn (max_iters) không làm "co" lịch LR (đã kiểm: test_lr_schedule_independent_of_max_iters).
    Mặc định giống UniFace/CASIA: lr 0.1, ÷10 ở epoch 16 và 24, 28 epoch, batch hiệu dụng 512."""
    epoch_f = global_step / steps_per_epoch
    lr = cfg_train["lr"] * (cfg_train["lr_gamma"] ** sum(epoch_f >= s for s in cfg_train["lr_steps"]))
    w = cfg_train.get("warmup_epochs", 0) or 0
    if w > 0 and epoch_f < w:
        lr *= max(epoch_f / w, 1e-3)
    return lr


def pick_device(name: str, di: D.DistInfo) -> torch.device:
    if name == "cpu" or (name == "auto" and not torch.cuda.is_available()):
        return torch.device("cpu")
    if name == "auto" or name == "cuda":
        return torch.device("cuda", di.local_rank)
    return torch.device(name)


def batch_plan(tc: dict, world: int):
    """→ (eff_batch toàn cục, ảnh mỗi GPU mỗi bước, micro_batch, số bước tích luỹ mỗi GPU)."""
    micro = int(tc["micro_batch"])
    eff = int(tc["global_batch"]) if tc.get("global_batch") else micro * int(tc["accum_steps"])
    if eff % world:
        raise ValueError(f"batch hiệu dụng {eff} không chia hết cho số GPU {world}")
    local = eff // world
    if local % micro:
        raise ValueError(f"ảnh mỗi GPU mỗi bước ({local}) không chia hết cho micro_batch {micro}")
    return eff, local, micro, local // micro


def prewarm_file(path: str, chunk_mb: int = 64) -> dict:
    """Đọc tuần tự toàn bộ file một lần để hệ điều hành đưa vào page cache (RAM).

    Lý do (B3, lỗi đo tốc độ pilot): /kaggle/input được nạp "lười"; lần đọc NGẪU NHIÊN đầu tiên rất chậm
    (pilot 1: 88–175 ảnh/s, data_wait 0.58–0.81 ở iter 20–220), khi file đã nằm trong cache thì
    loader đạt ≥ 389 ảnh/s (data_wait ≈ 0). Đọc tuần tự 1 lần trước khi train rẻ hơn nhiều so với để
    300 iteration đầu chờ dữ liệu. Bỏ qua nếu file lớn hơn ~80% RAM còn trống (cache sẽ bị đẩy ra)."""
    size = os.path.getsize(path)
    avail = None
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                avail = int(line.split()[1]) * 1024
    except OSError:
        pass
    if avail is not None and size > 0.8 * avail:
        return {"file": path, "bytes": size, "skipped": f"file {size / 2**30:.1f} GB > 80% RAM trống {avail / 2**30:.1f} GB"}
    t0 = time.time()
    with open(path, "rb", buffering=0) as f:
        while f.read(chunk_mb * 2 ** 20):
            pass
    dt = time.time() - t0
    return {"file": path, "bytes": size, "seconds": dt, "MB_per_s": size / 2 ** 20 / max(dt, 1e-9)}


def dataset_labels(ds) -> np.ndarray:
    """Nhãn từng ảnh của dataset gốc (RecordIO: chỉ đọc header; dữ liệu giả / thư mục: có sẵn)."""
    if hasattr(ds, "reader"):
        return CS.scan_labels(ds)
    if hasattr(ds, "labels"):
        return np.asarray(ds.labels, dtype=np.int64)
    return np.asarray([c for _, c in ds.samples], dtype=np.int64)


def val_images_u8(ds, positions) -> torch.Tensor:
    if hasattr(ds, "reader"):
        return load_val_u8(ds, positions)
    xs = [ds[(int(p), False)][0] for p in positions]          # dữ liệu giả: float [−1,1] → uint8
    return torch.stack([((x * 0.5 + 0.5) * 255).round().clamp(0, 255).to(torch.uint8) for x in xs])


class TrainModule(torch.nn.Module):
    """backbone + head trong MỘT mô-đun để DDP all-reduce gradient của cả hai (gồm b của head)."""

    def __init__(self, backbone, head):
        super().__init__()
        self.backbone, self.head = backbone, head

    def forward(self, x, y):
        return self.head(self.backbone(x), y)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", nargs="*", default=[], help="ghi đè: khoa.con=giatri")
    ap.add_argument("--resume", default=None, help="đường dẫn checkpoint, hoặc 'auto'")
    ap.add_argument("--eval_only", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.config, args.set)
    tc = cfg["train"]
    di = D.init_distributed(tc.get("device", "auto"))
    main_proc = di.is_main
    run_dir = os.path.join(cfg["output_dir"], cfg["run_name"])
    ckpt_dir = os.path.join(run_dir, "checkpoints")
    if main_proc:
        os.makedirs(ckpt_dir, exist_ok=True)
    D.barrier(di)
    resume_path = args.resume
    if resume_path == "auto":
        cand = os.path.join(ckpt_dir, "last.pt")
        resume_path = cand if os.path.exists(cand) else None

    if any(s >= int(tc["epochs"]) for s in tc["lr_steps"]):
        raise ValueError(f"lr_steps {tc['lr_steps']} phải < epochs {tc['epochs']}")
    set_seed(int(cfg["seed"]), bool(tc["deterministic"]))
    device = pick_device(tc.get("device", "auto"), di)
    amp = bool(tc["amp"]) and device.type == "cuda"

    def event(obj):
        if main_proc:
            append_jsonl(os.path.join(run_dir, "events.jsonl"), obj)

    # ---------------- data
    if cfg["data"].get("prewarm") and cfg["data"].get("type", "rec") == "rec":
        if di.local_rank == 0:          # 1 lần mỗi máy (page cache dùng chung giữa các tiến trình)
            pw = prewarm_file(os.path.join(cfg["data"]["root"], "train.rec"))
            event({"event": "prewarm", **pw})
            print("[prewarm]", json.dumps(pw, ensure_ascii=False), flush=True)
        D.barrier(di)
    dataset = build_train_dataset(cfg["data"])
    vcfg = cfg["data"].get("val") or {}
    val_split, val_imgs, val_labels = None, None, None
    if vcfg.get("enabled"):
        base = dataset
        t0 = time.time()
        labels_all = dataset_labels(base)
        n_total = int(base.num_classes)
        val_ids = CS.resolve_val_ids(vcfg, n_total)
        sp = CS.build_split(labels_all, val_ids, int(vcfg.get("max_per_id", CS.DEFAULT_MAX_PER_ID)),
                            int(vcfg.get("seed", CS.DEFAULT_SEED)))
        dataset = CS.RelabeledSubset(base, sp["train_pos"], sp["train_labels"], sp["num_train_classes"])
        val_split = {**CS.split_summary(sp), "n_classes_total": n_total, "n_val_ids": len(val_ids),
                     "val_ids_sha256": CS.ids_sha256(val_ids), "seconds": time.time() - t0}
        if main_proc:
            CS.write_val_images(os.path.join(run_dir, "val_images.csv"), base, sp) if hasattr(base, "reader") else None
            val_imgs, val_labels = val_images_u8(base, sp["val_pos"]), sp["val_labels"]
            event({"event": "val_split", **val_split})
            print("[val_split]", json.dumps(val_split, ensure_ascii=False), flush=True)
    num_classes = int(dataset.num_classes)
    eff_batch, local_batch, micro, accum = batch_plan(tc, di.world_size)
    sampler = EpochSampler(len(dataset), eff_batch, seed=int(cfg["seed"]), rank=di.rank, world_size=di.world_size)
    steps_per_epoch = sampler.batches_per_epoch()
    if steps_per_epoch == 0:
        raise ValueError("dataset nhỏ hơn batch hiệu dụng")
    nw_total = int(cfg["data"]["num_workers"])
    nw = cfg["data"].get("workers_per_rank")
    nw = int(nw) if nw is not None else (max(1, nw_total // di.world_size) if nw_total > 0 else 0)

    # ---------------- model
    backbone = get_backbone(cfg["model"]["backbone"], cfg["model"]["emb_dim"], cfg["model"]["dropout"], fp16=amp).to(device)
    head = build_head(cfg["head"], num_classes, cfg["model"]["emb_dim"]).to(device)
    params = list(backbone.parameters()) + list(head.parameters())
    opt = torch.optim.SGD(params, lr=tc["lr"], momentum=tc["momentum"], weight_decay=tc["weight_decay"])
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    gen_partial = torch.Generator().manual_seed(int(cfg["seed"]) + 7)

    epoch, step_in_epoch, global_step = 0, 0, 0
    best_key = cfg["eval"].get("best_metric", "tar@far=0.001")
    best = {"metric": best_key, "value": -1.0, "epoch": None, "global_step": None}
    if resume_path:
        ck = load_checkpoint(resume_path)
        backbone.load_state_dict(ck["backbone"])
        head.load_state_dict(ck["head"])
        opt.load_state_dict(ck["optimizer"])
        scaler.load_state_dict(ck["scaler"])
        epoch, step_in_epoch, global_step = ck["epoch"], ck["step_in_epoch"], ck["global_step"]
        set_rng_state(ck["rng"])
        gen_partial.set_state(ck["gen_partial"])
        best = ck.get("best", best)
        event({"event": "resume", "from": resume_path, "epoch": epoch, "step_in_epoch": step_in_epoch,
               "global_step": global_step, "world_size": di.world_size,
               "world_size_saved": ck.get("world_size", 1)})
        if main_proc:
            print(f"[resume] {resume_path}: epoch={epoch} step_in_epoch={step_in_epoch} global_step={global_step}")
    elif main_proc:
        dump_config(cfg, os.path.join(run_dir, "config.yaml"))

    model = TrainModule(backbone, head)
    if di.enabled:
        # broadcast_buffers=False: buffer BN (running mean/var) của mỗi GPU tự cập nhật trên micro-batch của nó;
        # trước mỗi lần val/eval/ghi checkpoint lấy TRUNG BÌNH giữa các GPU (D.average_bn_buffers). Buffer
        # partial_index của UniFace đổi kích thước mỗi bước nên không được để DDP phát lại.
        model = torch.nn.parallel.DistributedDataParallel(
            model, device_ids=[di.local_rank] if device.type == "cuda" else None, broadcast_buffers=False)

    info = {
        "python": platform.python_version(), "torch": torch.__version__, "device": str(device),
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "gpu_total_mem_mb": (torch.cuda.get_device_properties(device).total_memory / 2 ** 20) if device.type == "cuda" else None,
        "gpu_count": torch.cuda.device_count(), "world_size": di.world_size, "amp": amp,
        "num_images": len(dataset), "num_classes": num_classes, "effective_batch": eff_batch,
        "per_gpu_batch": local_batch, "micro_batch": micro, "accum_steps_per_gpu": accum,
        "workers_per_rank": nw, "steps_per_epoch": steps_per_epoch,
        "lr_steps_epochs": list(tc["lr_steps"]), "lr_steps_iters": [int(s * steps_per_epoch) for s in tc["lr_steps"]],
        "total_iters": int(tc["epochs"]) * steps_per_epoch,
        "val_split": val_split, "best_metric": best_key if val_split else None,
        "config_fingerprint": config_fingerprint(cfg),
        "code_fingerprint": code_fingerprint(os.path.dirname(os.path.abspath(__file__))),
        "params_backbone_M": sum(p.numel() for p in backbone.parameters()) / 1e6,
        "params_head_M": sum(p.numel() for p in head.parameters()) / 1e6,
        "head": repr(head),
    }
    if main_proc:
        with open(os.path.join(run_dir, "run_info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        print(json.dumps(info, indent=2, ensure_ascii=False))

    def do_eval(tag):
        """Chỉ rank 0 đánh giá (các rank khác chờ ở barrier)."""
        ec = cfg["eval"]
        rec = None
        D.average_bn_buffers(backbone, di)
        if main_proc and ec.get("bin_dir"):
            t0 = time.time()
            res = evaluate_bins(backbone, ec["bin_dir"], ec["bins"], device, int(ec["batch_size"]), amp)
            rec = {"tag": tag, "global_step": global_step, "epoch": epoch, "results": res,
                   "eval_seconds": time.time() - t0}
            if hasattr(head, "threshold_stats"):
                rec["threshold"] = head.threshold_stats()
            append_jsonl(os.path.join(run_dir, "eval.jsonl"), rec)
            print("[eval]", json.dumps(rec, ensure_ascii=False), flush=True)
        D.barrier(di)
        return rec

    def do_val(tag):
        """Validation (rank 0) + cập nhật best.pt. Trả về bản ghi (rank 0) hoặc None."""
        rec = None
        D.average_bn_buffers(backbone, di)     # BN running stats = trung bình mọi GPU trước khi đo
        if main_proc and val_imgs is not None:
            res = evaluate_val(backbone, val_imgs, val_labels, device, int(cfg["eval"]["batch_size"]), amp)
            rec = {"tag": tag, "global_step": global_step, "epoch": epoch, "results": res,
                   "lr_last": lr, "train_loss_epoch": ep_stat["loss"] / max(ep_stat["n"], 1),
                   "train_loss_epoch_iters": ep_stat["n"]}   # loss của rank 0 (DDP: nửa batch); chỉ để vẽ
            if hasattr(head, "threshold_stats"):
                rec["threshold"] = head.threshold_stats()
            v = res.get(best_key, float("nan"))
            if math.isfinite(v) and v > best["value"]:
                best.update(value=float(v), epoch=epoch, global_step=global_step)
                save_checkpoint(os.path.join(ckpt_dir, "best.pt"), {
                    "backbone": backbone.state_dict(), "head": head.state_dict(), "epoch": epoch,
                    "global_step": global_step, "val": res, "best": dict(best), "config": cfg})
                rec["new_best"] = True
                event({"event": "new_best", **best})
            rec["best_so_far"] = dict(best)
            append_jsonl(os.path.join(run_dir, "val.jsonl"), rec)
            print("[val]", json.dumps({"epoch": epoch, best_key: v, "best": best}, ensure_ascii=False), flush=True)
        D.barrier(di)
        return rec

    if args.eval_only:
        do_eval("eval_only")
        D.cleanup(di)
        return

    def save(tag_file="last.pt"):
        D.average_bn_buffers(backbone, di)     # mọi rank gọi (collective)
        if main_proc:
            save_checkpoint(os.path.join(ckpt_dir, tag_file), {
                "backbone": backbone.state_dict(), "head": head.state_dict(), "optimizer": opt.state_dict(),
                "scaler": scaler.state_dict(), "epoch": epoch, "step_in_epoch": step_in_epoch,
                "global_step": global_step, "rng": rng_state(), "gen_partial": gen_partial.get_state(),
                "world_size": di.world_size, "best": dict(best), "config": cfg})
        D.barrier(di)

    logger = CSVLogger(os.path.join(run_dir, "train_log.csv"), LOG_FIELDS) if main_proc else None
    max_iters = tc.get("max_iters")
    total_epochs = int(tc["epochs"])
    speed_hist = []                       # sec/iter của từng cửa sổ log (bỏ cửa sổ đầu khi tổng hợp)
    stop = False
    model.train()
    win = {}

    def reset_window():
        win.update(t0=time.time(), wait=0.0, n=0, loss=0.0)

    def flush_log(lr, grad_norm, stats):
        """Ghi một dòng log cho cửa sổ hiện tại. Gọi mỗi log_every bước VÀ ở cuối epoch (sửa lỗi pilot:
        cửa sổ dở dang cuối epoch trước đây bị bỏ, nên điểm log đầu epoch sau chỉ gồm vài iteration)."""
        if win["n"] == 0:
            return
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        dt = time.time() - win["t0"]
        spi = dt / win["n"]
        loss_mean = D.all_reduce_mean(win["loss"] / win["n"], di, device)   # trung bình mọi GPU = loss toàn batch
        if not main_proc:
            return
        if global_step > 1:
            speed_hist.append((spi, win["n"]))
        row = {"global_step": global_step, "epoch": epoch, "step_in_epoch": step_in_epoch, "lr": lr,
               "loss": loss_mean, "grad_norm": grad_norm, "amp_scale": float(scaler.get_scale()),
               "sec_per_iter": spi, "img_per_sec": eff_batch / spi, "data_wait_frac": win["wait"] / max(dt, 1e-9),
               "n_iters_window": win["n"]}
        row.update({k: stats.get(k, "") for k in ("b", "t_eq23", "t_eq30", "t_sf2", "cos_pos_mean", "cos_neg_max_mean")})
        if device.type == "cuda":
            row["vram_alloc_max_mb"] = torch.cuda.max_memory_allocated(device) / 2 ** 20
            row["vram_reserved_max_mb"] = torch.cuda.max_memory_reserved(device) / 2 ** 20
        logger.log(row)
        print(" ".join(f"{k}={row[k]:.4g}" if isinstance(row[k], float) else f"{k}={row[k]}"
                       for k in ("global_step", "epoch", "loss", "lr", "b", "sec_per_iter", "data_wait_frac")
                       if row.get(k, "") != ""), flush=True)

    lr, grad_norm, stats = tc["lr"], float("nan"), {}
    ep_stat = {"loss": 0.0, "n": 0}     # loss train trung bình của epoch hiện tại (rank 0, để vẽ cạnh đường val)
    while epoch < total_epochs and not stop:
        sampler.set_epoch(epoch, step_in_epoch)
        loader = DataLoader(dataset, batch_size=local_batch, sampler=sampler, num_workers=nw,
                            pin_memory=device.type == "cuda", drop_last=True, worker_init_fn=worker_init_fn,
                            persistent_workers=False)
        reset_window()
        ep_stat.update(loss=0.0, n=0)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        t_wait0 = time.time()
        for images, labels in loader:
            win["wait"] += time.time() - t_wait0
            lr = lr_at(tc, global_step, steps_per_epoch)
            for g in opt.param_groups:
                g["lr"] = lr
            if isinstance(head, UnifiedCEHead) and head.uses_partial:
                # nhãn của CẢ batch toàn cục (mọi GPU) → mọi GPU chọn cùng tập lớp, giống bản 1 GPU
                all_labels = D.all_gather_cat(labels.to(device), di).cpu()
                head.sample_partial(all_labels, gen_partial)
            opt.zero_grad(set_to_none=True)
            loss_sum, stats = 0.0, {}
            chunks = list(zip(images.split(micro), labels.split(micro)))
            for ci, (x, y) in enumerate(chunks):
                x = x.to(device, non_blocking=True)
                y = y.to(device, non_blocking=True)
                sync_now = (not di.enabled) or ci == len(chunks) - 1
                ctx = model.no_sync() if (di.enabled and not sync_now) else _nullctx()
                with ctx:
                    loss, stats = model(x, y)
                    # n/local_batch trên mỗi GPU; DDP chia trung bình cho W → tổng = Σ n·loss / eff_batch
                    scaler.scale(loss * (y.size(0) / local_batch)).backward()
                loss_sum += float(loss.detach()) * y.size(0) / local_batch
            scaler.unscale_(opt)
            grad_norm = float(torch.nn.utils.clip_grad_norm_(params, tc["clip_grad"])) if tc["clip_grad"] else float("nan")
            if isinstance(head, UnifiedCEHead):
                head.momentum_before_step(opt)
            scaler.step(opt)
            scaler.update()
            if isinstance(head, UnifiedCEHead):
                head.momentum_after_step(opt)

            if not math.isfinite(loss_sum):
                event({"event": "nonfinite_loss", "global_step": global_step, "rank": di.rank})
            global_step += 1
            step_in_epoch += 1
            win["n"] += 1
            win["loss"] += loss_sum
            ep_stat["loss"] += loss_sum
            ep_stat["n"] += 1

            if global_step % int(tc["log_every"]) == 0 or global_step == 1:
                flush_log(lr, grad_norm, stats)
                reset_window()

            if tc["ckpt_every_iters"] and global_step % int(tc["ckpt_every_iters"]) == 0:
                save()
            if max_iters and global_step >= int(max_iters):
                stop = True
                break
            t_wait0 = time.time()

        flush_log(lr, grad_norm, stats)     # cửa sổ dở dang cuối epoch / lúc dừng
        reset_window()
        if not stop:   # hết epoch
            epoch += 1
            step_in_epoch = 0
            vev = int(cfg["eval"].get("val_every_epochs") or 0)
            if val_split and vev and (epoch % vev == 0 or epoch == total_epochs):
                do_val(f"epoch_{epoch}")    # trước save() → last.pt mang theo best mới (resume không mất best)
            save()
            if main_proc and tc.get("save_epoch_ckpt", True):
                torch.save({"backbone": backbone.state_dict(), "head": head.state_dict(), "epoch": epoch,
                            "config": cfg}, os.path.join(ckpt_dir, f"epoch_{epoch:02d}.pt"))
            ev = int(cfg["eval"].get("every_epochs") or 0)
            if ev and (epoch % ev == 0 or epoch == total_epochs):
                do_eval(f"epoch_{epoch}")
                # eval ở epoch cuối đã chạy → không chạy lại ở at_end
                if epoch == total_epochs:
                    cfg["eval"]["at_end"] = False

    save()
    if logger:
        logger.close()
    if cfg["eval"].get("at_end"):
        do_eval("end")

    # tổng hợp tốc độ ĐO ĐƯỢC (không ước lượng tay): bỏ cửa sổ log đầu (khởi động cudnn/DataLoader),
    # chỉ dùng cửa sổ đủ log_every bước (cửa sổ cuối epoch ngắn hơn, chứa thời gian khởi động loader mới)
    if main_proc:
        summ = {"global_step": global_step, "epoch": epoch, "steps_per_epoch": steps_per_epoch,
                "effective_batch": eff_batch, "world_size": di.world_size, "num_windows": len(speed_hist)}
        full = [s for s, n in speed_hist if n == int(tc["log_every"])]
        if len(full) >= 2:
            spi = float(np.median(full[1:]))
            summ.update({"median_sec_per_iter": spi,
                         "extrapolated_hours_per_epoch": spi * steps_per_epoch / 3600,
                         "extrapolated_hours_total_epochs": spi * steps_per_epoch * total_epochs / 3600,
                         "total_epochs_cfg": total_epochs,
                         "note": "ngoại suy = median(sec/iter) × steps_per_epoch; chưa tính thời gian eval/checkpoint"})
        if val_split:
            summ["best_val"] = dict(best)
        if device.type == "cuda":
            summ["vram_alloc_max_mb_last_epoch"] = torch.cuda.max_memory_allocated(device) / 2 ** 20
        with open(os.path.join(run_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summ, f, indent=2, ensure_ascii=False)
        print("[summary]", json.dumps(summ, ensure_ascii=False))
    D.cleanup(di)


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


if __name__ == "__main__":
    main()
