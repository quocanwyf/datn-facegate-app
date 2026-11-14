"""Head phân loại + loss cho nhận dạng khuôn mặt — MỘT module dùng chung cho baseline và proposed.

Các head (cùng cách khởi tạo W, cùng cách tính cosine, cùng quy tắc θ+m>π):

    tên cfg     | công thức                                   | nguồn (report)
    ------------|---------------------------------------------|---------------------------------------------
    softmax     | normalised softmax, m = 0                    | ArcFace Eq.2 (C1 §2)  = UniFace Eq.8 (C28 §2a)
    cosface     | s·(cosθ_y − m)  + CE                         | ArcFace Eq.4 với (m1,m2,m3)=(1,0,m) (C1 §2); CosFace
    arcface     | s·cos(θ_y + m)  + CE                         | ArcFace Eq.3 (C1 §2)
    uniface     | L_uce / L_uce-m / L_uce-mb (λ hoặc r), b chung | UniFace Eq.23, 31, 32 (C28 §2d,f,g)
    bce         | như uniface nhưng b RIÊNG từng lớp           | UniFace Bảng 1, L_bce-m (C28 §5; repo: Normalized_BCE_Loss)
    sphereface2 | SphereFace2-C: BCE one-vs-all, b chung, g(z) | SphereFace2 Eq.5 (C24 §2g); code OpenSphere (xem class)

Lựa chọn thống nhất (ghi rõ để bảo vệ trước hội đồng):
  1. Cosine luôn tính ở fp32 (tắt autocast) vì s = 64 nhân vào → fp16 dễ tràn/mất chính xác.
  2. W khởi tạo N(0, 0.01²) cho MỌI head (theo PartialFC_V2 của insightface arcface_torch).
     Repo UniFace dùng kaiming_normal; chọn một cách chung để so sánh công bằng.
  3. θ + m > π (chỉ xảy ra với margin GÓC: arcface, uniface margin_type='arc'):
     dùng quy tắc của code ArcFace gốc (insightface bản MXNet / arcface-pytorch, ``easy_margin=False``):
         g(θ) = cos(θ + m)                 nếu θ < π − m   (tức cosθ > cos(π − m))
         g(θ) = cosθ − m·sin(π − m)        nếu θ ≥ π − m
     → logit đích luôn ĐƠN ĐIỆU GIẢM theo θ trên [0, π] (có bước nhảy xuống tại θ = π − m),
     gradient không triệt tiêu. Đây chính là các hằng ``theta``, ``sinmm`` mà bản PyTorch hiện hành
     của insightface khai báo nhưng không dùng (C1 §3). Margin COSINE (cosface, uniface 'cos')
     không có vấn đề này, nên không cần xử lý.
     Khác bản insightface PyTorch: ở đây gradient đi qua đúng công thức cos(θ+m) (như paper),
     không dùng thủ thuật no_grad/in-place (gradient "thẳng" qua cos) của insightface PyTorch.
  4. Mọi loss trả về dạng trung bình theo mẫu trong micro-batch.
  5. Ngoại lệ có chủ đích — SphereFace2: bám SÁT code chính thức OpenSphere (chuẩn hoá W tại chỗ,
     gradient "thẳng" qua g(·) và margin, hệ số lw), vì đây là baseline so sánh lấy nguyên phương pháp
     của tác giả; chi tiết trong docstring ``SphereFace2Head``.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

_EPS = 1e-7


# ----------------------------------------------------------------------------- helpers
def angular_margin_target(cos_y: torch.Tensor, m: float) -> torch.Tensor:
    """Logit đích có margin góc, xử lý θ + m > π theo quy tắc thống nhất (xem docstring module).

    ArcFace Eq.3 (C1 §2): thay cosθ_y bằng cos(θ_y + m).
    cos(θ+m) = cosθ·cos m − sinθ·sin m, với sinθ = sqrt(1 − cos²θ) (θ ∈ [0, π] nên sinθ ≥ 0).
    """
    if m == 0.0:
        return cos_y
    cos_y = cos_y.clamp(-1.0 + _EPS, 1.0 - _EPS)
    sin_y = torch.sqrt((1.0 - cos_y * cos_y).clamp(min=_EPS))
    phi = cos_y * math.cos(m) - sin_y * math.sin(m)
    th = math.cos(math.pi - m)          # θ = π − m  <=>  cosθ = cos(π − m)
    mm = math.sin(math.pi - m) * m      # bù tuyến tính kiểu CosFace khi θ ≥ π − m
    return torch.where(cos_y > th, phi, cos_y - mm)


def cosine_margin_target(cos_y: torch.Tensor, m: float) -> torch.Tensor:
    """Margin cosine (CosFace; UniFace Eq.31 dùng dạng này cho cặp dương): cosθ_y − m."""
    return cos_y - m


_MARGIN_FN = {"cos": cosine_margin_target, "arc": angular_margin_target}


# ----------------------------------------------------------------------------- base
class _BaseHead(nn.Module):
    """W ∈ R^{N×d}: mỗi hàng là proxy (tâm lớp) trên hypersphere. cosθ_j = <x/|x|, W_j/|W_j|>."""

    uses_partial = False

    def __init__(self, num_classes: int, emb_dim: int = 512, s: float = 64.0, w_init_std: float = 0.01):
        super().__init__()
        self.num_classes = int(num_classes)
        self.emb_dim = int(emb_dim)
        self.s = float(s)
        self.weight = nn.Parameter(torch.empty(self.num_classes, self.emb_dim))
        nn.init.normal_(self.weight, 0.0, w_init_std)

    def cosine(self, emb: torch.Tensor, index: Optional[torch.Tensor] = None) -> torch.Tensor:
        w = self.weight if index is None else self.weight[index]
        return F.linear(F.normalize(emb.float(), eps=1e-5), F.normalize(w.float(), eps=1e-5))

    def extra_repr(self) -> str:
        return f"num_classes={self.num_classes}, emb_dim={self.emb_dim}, s={self.s}"


# ----------------------------------------------------------------------------- softmax family
class MarginSoftmaxHead(_BaseHead):
    """Họ normalised-softmax + margin (CE trên logit s·cos).

    margin_type='cos', m=0      → normalised softmax  (ArcFace Eq.2; UniFace Eq.8)
    margin_type='cos', m>0      → CosFace             (ArcFace Eq.4 với m3 = m)
    margin_type='arc', m>0      → ArcFace             (ArcFace Eq.3)

        L = −1/N Σ_i log( e^{s·g(θ_yi)} / (e^{s·g(θ_yi)} + Σ_{j≠yi} e^{s·cosθ_j}) )
    """

    def __init__(self, num_classes, emb_dim=512, s=64.0, m=0.5, margin_type="arc", w_init_std=0.01):
        super().__init__(num_classes, emb_dim, s, w_init_std)
        if margin_type not in _MARGIN_FN:
            raise ValueError(margin_type)
        self.m = float(m)
        self.margin_type = margin_type

    def forward(self, emb: torch.Tensor, labels: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        with torch.autocast(device_type=emb.device.type, enabled=False):
            cos = self.cosine(emb)                                   # (B, N), fp32
            idx = torch.arange(cos.size(0), device=cos.device)
            cos_y = cos[idx, labels]
            target = _MARGIN_FN[self.margin_type](cos_y, self.m)
            logits = cos.clone()
            logits[idx, labels] = target
            loss = F.cross_entropy(self.s * logits, labels)
        stats = _cos_stats(cos.detach(), labels)
        return loss, stats

    def extra_repr(self):
        return super().extra_repr() + f", m={self.m}, margin_type={self.margin_type}"


# ----------------------------------------------------------------------------- UniFace family
class UnifiedCEHead(_BaseHead):
    """UniFace — Unified Cross-Entropy (Zhou et al., ICCV 2023), report C28.

    Eq.23  L_uce   = log(1 + e^{−s·cosθ_y + b̃}) + Σ_{j≠y} log(1 + e^{s·cosθ_j − b̃})
    Eq.31  L_uce-m = log(1 + e^{−s·(cosθ_y − m) + b̃}) + Σ_{j≠y} log(1 + e^{s·cosθ_j − b̃})
    Eq.32  L_uce-mb= log(1 + e^{−s·(cosθ_y − m) + b̃}) + λ·Σ_{j≠y, p_j<r} log(1 + e^{s·cosθ_j − b̃})
              biến thể "λ": r = 1, λ < 1 (re-weighting) ; biến thể "r": λ = 1, r < 1 (sampling lớp âm).

    Theo code chính thức (CVI-SZU/UniFace, head.py ``Unified_Cross_Entropy_Loss``):
      * b̃ là MỘT tham số học được dùng chung mọi lớp, khởi tạo b̃₀ = log(N·r·10).
      * z được kẹp vào [−s, s] trước softplus: log(1+exp(±clamp(z, −s, s))).  (clamp=True mặc định)
      * Loss = tổng theo lớp (dương + các âm) cho mỗi mẫu, rồi trung bình theo batch.
      * Biến thể r: mỗi bước tối ưu chọn tập lớp = mọi lớp dương trong batch + lớp ngẫu nhiên khác,
        tổng ⌊N·r⌋ lớp (``partial_index``); trình train gọi ``sample_partial`` mỗi bước.
    bias_mode='per_class' → b riêng từng lớp = L_bce-m (repo: ``Normalized_BCE_Loss``) — dùng cho
    ablation tách "BCE" khỏi "ngưỡng thống nhất" (C28 §6, dòng U1).
    margin_type='arc' → Arc-UniFace (C28 Bảng 2; paper không viết công thức — ở đây thay
    cosθ_y − m bằng g(θ_y) margin góc, cùng quy tắc θ+m>π như ArcFace).

    Ngưỡng: paper không nhất quán (C28 §4): Eq.23 b̃ = s·cosθ_t + log(N−1)  →  t₂₃ = (b̃ − log(N−1))/s ;
    Eq.30 b̃* = s·t*  →  t₃₀ = b̃/s. Log cả hai để An đối chiếu (Fig.4 paper: t ≈ 0.2928).
    """

    def __init__(self, num_classes, emb_dim=512, s=64.0, m=0.45, lam=1.0, r=1.0, margin_type="cos",
                 bias_mode="shared", clamp=True, w_init_std=0.01):
        super().__init__(num_classes, emb_dim, s, w_init_std)
        if margin_type not in _MARGIN_FN:
            raise ValueError(margin_type)
        if bias_mode not in ("shared", "per_class"):
            raise ValueError(bias_mode)
        if not (0.0 < r <= 1.0):
            raise ValueError("r phải thuộc (0, 1]")
        self.m, self.lam, self.r = float(m), float(lam), float(r)
        self.margin_type, self.bias_mode, self.clamp = margin_type, bias_mode, bool(clamp)
        nb = 1 if bias_mode == "shared" else self.num_classes
        b0 = math.log(self.num_classes * self.r * 10.0)            # khởi tạo theo repo gốc
        self.bias = nn.Parameter(torch.full((nb,), b0))
        self.uses_partial = self.r < 1.0
        self.register_buffer("partial_index", torch.empty(0, dtype=torch.long), persistent=False)
        # momentum riêng của từng hàng W khi lấy mẫu lớp (repo: weight_mom) — lưu trong checkpoint
        self.register_buffer("weight_mom", torch.zeros(self.num_classes, self.emb_dim) if self.uses_partial
                             else torch.zeros(0))

    # ---- biến thể r ------------------------------------------------------------------------
    @torch.no_grad()
    def sample_partial(self, labels_full_step: torch.Tensor, generator: Optional[torch.Generator] = None):
        """Chọn ⌊N·r⌋ lớp: mọi lớp dương của CẢ bước tối ưu (mọi micro-batch) + lớp ngẫu nhiên khác.
        Giống repo: perm = randperm(N); perm[positive] = 0; topk nhỏ nhất → luôn giữ lớp dương."""
        if not self.uses_partial:
            self.partial_index = torch.empty(0, dtype=torch.long, device=self.weight.device)
            return
        n = self.num_classes
        k = int(n * self.r)
        positive = torch.unique(labels_full_step.to("cpu"))
        if positive.numel() > k:
            raise ValueError(f"số lớp dương trong một bước ({positive.numel()}) > N·r = {k}")
        perm = torch.randperm(n, generator=generator).float() + 1.0   # +1 để lớp dương (=0) luôn nhỏ nhất
        perm[positive] = 0.0
        idx = torch.topk(perm, k=k, largest=False)[1]
        self.partial_index = idx.sort()[0].to(self.weight.device)

    def _columns(self, labels):
        if self.uses_partial:
            if self.partial_index.numel() == 0:
                raise RuntimeError("Gọi sample_partial(labels) trước forward khi r < 1")
            cols = torch.searchsorted(self.partial_index, labels)
            return self.partial_index, cols
        return None, labels

    # ---- forward -----------------------------------------------------------------------------
    def forward(self, emb: torch.Tensor, labels: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        with torch.autocast(device_type=emb.device.type, enabled=False):
            index, cols = self._columns(labels)
            cos = self.cosine(emb, index)                                    # (B, K) fp32
            B, K = cos.shape
            if self.bias_mode == "shared":
                b = self.bias.view(1, 1)                                     # broadcast
            else:
                b = (self.bias if index is None else self.bias[index]).view(1, K)
            onehot = torch.zeros(B, K, dtype=torch.bool, device=cos.device)
            onehot[torch.arange(B, device=cos.device), cols] = True
            pos_cos = _MARGIN_FN[self.margin_type](cos, self.m)              # chỉ dùng tại vị trí dương
            z_p = self.s * pos_cos - b                                       # s(cosθ_y − m) − b̃
            z_n = self.s * cos - b                                           # s·cosθ_j − b̃
            if self.clamp:
                z_p = z_p.clamp(-self.s, self.s)
                z_n = z_n.clamp(-self.s, self.s)
            p_loss = F.softplus(-z_p)                                        # log(1 + e^{−z_p})
            n_loss = F.softplus(z_n) * self.lam                              # λ·log(1 + e^{z_n})
            loss = torch.where(onehot, p_loss, n_loss).sum(dim=1).mean()
        stats = _cos_stats(cos.detach(), cols)
        stats.update(self.threshold_stats())
        return loss, stats

    @torch.no_grad()
    def threshold_stats(self) -> Dict[str, float]:
        b = float(self.bias.detach().float().mean())
        n_eff = self.num_classes * (self.r if self.uses_partial else 1.0)
        return {"b": b,
                "t_eq30": b / self.s,                                   # b̃* = s·t*
                "t_eq23": (b - math.log(max(n_eff - 1.0, 1.0))) / self.s}  # b̃ = s·cosθ_t + log(N−1)

    # ---- momentum theo hàng khi r < 1 (theo train.py repo UniFace) ---------------------------
    @torch.no_grad()
    def momentum_before_step(self, optimizer: torch.optim.Optimizer):
        """Đặt momentum của W: 0 cho lớp không được chọn, khôi phục momentum đã lưu cho lớp được chọn."""
        if not self.uses_partial:
            return
        st = optimizer.state.get(self.weight)
        if st and "momentum_buffer" in st and st["momentum_buffer"] is not None:
            buf = st["momentum_buffer"]
            buf.zero_()
            buf[self.partial_index] = self.weight_mom[self.partial_index].to(buf.dtype)

    @torch.no_grad()
    def momentum_after_step(self, optimizer: torch.optim.Optimizer):
        if not self.uses_partial:
            return
        st = optimizer.state.get(self.weight)
        if st and st.get("momentum_buffer") is not None:
            self.weight_mom[self.partial_index] = st["momentum_buffer"][self.partial_index].to(self.weight_mom.dtype)

    def extra_repr(self):
        return (super().extra_repr() + f", m={self.m}, lam={self.lam}, r={self.r}, margin_type={self.margin_type}, "
                f"bias_mode={self.bias_mode}, clamp={self.clamp}")


# ----------------------------------------------------------------------------- SphereFace2
OPENSPHERE_REF = ("https://github.com/ydwen/opensphere/blob/a679e82032455941932e23e3d3cbab6b8c07e3d4/"
                  "opensphere/module/head/sphereface2.py")   # commit a679e82 (HEAD 12/10/2023, file đổi lần cuối ở ec8a8ca)


def sphereface2_bias_init(num_classes: int, lam: float, r: float, m: float, t: float) -> float:
    """b khởi tạo sao cho ∂L/∂b = 0 khi mọi cosθ = 0 (SphereFace2 Phụ lục G; = code OpenSphere __init__).
    z = λ / ((1−λ)(K−1)), a_y = r(g(0) − m), a_i = r(g(0) + m), g(0) = 2·0.5^t − 1."""
    z = lam / ((1.0 - lam) * (num_classes - 1.0))
    ay = r * (2.0 * 0.5 ** t - 1.0 - m)
    ai = r * (2.0 * 0.5 ** t - 1.0 + m)
    temp = (1.0 - z) ** 2 + 4.0 * z * math.exp(ay - ai)
    return math.log(2.0 * z) - ai - math.log(1.0 - z + math.sqrt(temp))


class SphereFace2Head(_BaseHead):
    """SphereFace2-C (Wen et al., ICLR 2022), report C24. Port của ``SphereFace2`` trong OpenSphere
    (MIT, © 2022 Yandong Wen, Weiyang Liu) — ``OPENSPHERE_REF``.

    Eq.5:  L = λ/r·log(1 + e^{−r(g(cosθ_y) − m) − b}) + (1−λ)/r·Σ_{i≠y} log(1 + e^{r(g(cosθ_i) + m) + b})
           g(z) = 2((z+1)/2)^t − 1 ;  b: MỘT bias học được dùng chung mọi lớp (= ngưỡng thống nhất).

    Giữ đúng code chính thức (khác với cách viết thống nhất của các head còn lại — ghi rõ để bảo vệ):
      (1) W được chuẩn hoá TẠI CHỖ (``w.data = normalize(w.data)``) đầu mỗi forward, không truyền gradient
          qua phép chuẩn hoá; feature x được chuẩn hoá có gradient.
      (2) g(·) và margin tính trong no_grad rồi cộng Δ = g − cos → giá trị forward đúng Eq.5, nhưng
          ∂logit/∂cos = r (gradient KHÔNG đi qua đạo hàm của g) — C24 §2 "Lưu ý".
      (3) loss = BCEWithLogits(logits, onehot, weight) lấy TRUNG BÌNH trên B×K phần tử, weight =
          lw·K/r·(λ·onehot + (1−λ)(1−onehot)) → loss = lw × [Eq.5 trung bình theo mẫu]. lw = 50 (mặc định code).
      (4) Không kẹp logit. Tính ở fp32 (tắt autocast) như mọi head.
    Khác code chính thức (ghi rõ): khởi tạo W = N(0, 0.01²) như mọi head (code gốc: xavier_normal); vì W
    được chuẩn hoá ngay ở forward đầu, cả hai đều cho hướng phân bố đều trên mặt cầu → tương đương.
    Siêu tham số mặc định = mặc định class OpenSphere = cấu hình so sánh lớn của paper (§3.2):
    λ(alpha)=0.7, r=40, m=0.4, t=3. (Config MS1M của OpenSphere dùng 0.8/64/0.5/3 — không dùng ở đây.)
    """

    def __init__(self, num_classes, emb_dim=512, lam=0.7, r=40.0, m=0.4, t=3.0, lw=50.0, w_init_std=0.01):
        super().__init__(num_classes, emb_dim, s=r, w_init_std=w_init_std)
        if not (0.0 < lam < 1.0):
            raise ValueError("lam (alpha) phải thuộc (0, 1)")
        self.lam, self.r, self.m, self.t, self.lw = float(lam), float(r), float(m), float(t), float(lw)
        self.bias = nn.Parameter(torch.full((1,), sphereface2_bias_init(self.num_classes, self.lam, self.r,
                                                                         self.m, self.t)))

    def g(self, z: torch.Tensor) -> torch.Tensor:
        return 2.0 * ((z + 1.0) / 2.0).pow(self.t) - 1.0

    def forward(self, emb: torch.Tensor, labels: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        with torch.autocast(device_type=emb.device.type, enabled=False):
            with torch.no_grad():
                self.weight.data.copy_(F.normalize(self.weight.data.float(), dim=-1))   # (1)
            x = F.normalize(emb.float(), dim=-1)
            cos = F.linear(x, self.weight.float())                                     # (B, K)
            one_hot = torch.zeros_like(cos)
            one_hot.scatter_(1, labels.view(-1, 1), 1.0)
            with torch.no_grad():                                                      # (2)
                g_cos = self.g(cos) - self.m * (2.0 * one_hot - 1.0)
                d_theta = g_cos - cos
            logits = self.r * (cos + d_theta) + self.bias
            weight = self.lam * one_hot + (1.0 - self.lam) * (1.0 - one_hot)
            weight = self.lw * self.num_classes / self.r * weight                      # (3)
            loss = F.binary_cross_entropy_with_logits(logits, one_hot, weight=weight)
        stats = _cos_stats(cos.detach(), labels)
        stats.update(self.threshold_stats())
        return loss, stats

    @torch.no_grad()
    def threshold_stats(self) -> Dict[str, float]:
        """Ranh giới không margin: r·g(cosθ) + b = 0  →  cosθ_t = g⁻¹(−b/r) = 2((1 − b/r)/2)^{1/t} − 1."""
        b = float(self.bias.detach().float())
        u = (1.0 - b / self.r) / 2.0
        t_sf2 = 2.0 * u ** (1.0 / self.t) - 1.0 if 0.0 <= u <= 1.0 else float("nan")
        return {"b": b, "t_sf2": t_sf2}

    def extra_repr(self):
        return (f"num_classes={self.num_classes}, emb_dim={self.emb_dim}, lam={self.lam}, r={self.r}, "
                f"m={self.m}, t={self.t}, lw={self.lw}")


# ----------------------------------------------------------------------------- stats & factory
@torch.no_grad()
def _cos_stats(cos: torch.Tensor, cols: torch.Tensor) -> Dict[str, float]:
    B = cos.size(0)
    idx = torch.arange(B, device=cos.device)
    pos = cos[idx, cols]
    neg = cos.clone()
    neg[idx, cols] = -2.0
    return {"cos_pos_mean": float(pos.mean()), "cos_neg_max_mean": float(neg.max(dim=1).values.mean())}


def build_head(cfg: dict, num_classes: int, emb_dim: int = 512) -> _BaseHead:
    """cfg = {name, s, m, lam, r, margin_type, clamp, w_init_std} (+ t, lw cho sphereface2). Xem configs/*.yaml.
    LƯU Ý sphereface2: lam = λ(alpha) Eq.5, r = độ cong softplus (≈ s) — KHÁC nghĩa với lam/r của uniface;
    mặc định của DEFAULTS trong config.py (lam=1, r=1) không hợp lệ cho sphereface2 → config phải ghi rõ."""
    name = cfg["name"].lower()
    s = float(cfg.get("s", 64.0))
    std = float(cfg.get("w_init_std", 0.01))
    if name == "softmax":
        return MarginSoftmaxHead(num_classes, emb_dim, s, m=0.0, margin_type="cos", w_init_std=std)
    if name == "cosface":
        return MarginSoftmaxHead(num_classes, emb_dim, s, m=float(cfg.get("m", 0.35)), margin_type="cos", w_init_std=std)
    if name == "arcface":
        return MarginSoftmaxHead(num_classes, emb_dim, s, m=float(cfg.get("m", 0.5)), margin_type="arc", w_init_std=std)
    if name in ("uniface", "bce"):
        return UnifiedCEHead(num_classes, emb_dim, s, m=float(cfg.get("m", 0.45)), lam=float(cfg.get("lam", 1.0)),
                             r=float(cfg.get("r", 1.0)), margin_type=cfg.get("margin_type", "cos"),
                             bias_mode="shared" if name == "uniface" else "per_class",
                             clamp=bool(cfg.get("clamp", True)), w_init_std=std)
    if name == "sphereface2":
        return SphereFace2Head(num_classes, emb_dim, lam=float(cfg.get("lam", 0.7)), r=float(cfg.get("r", 40.0)),
                               m=float(cfg.get("m", 0.4)), t=float(cfg.get("t", 3.0)), lw=float(cfg.get("lw", 50.0)),
                               w_init_std=std)
    raise ValueError(f"head không hỗ trợ: {name}")
