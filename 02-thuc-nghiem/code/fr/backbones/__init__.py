from .iresnet import iresnet18, iresnet34, iresnet50, iresnet100

_ZOO = {"r18": iresnet18, "r34": iresnet34, "r50": iresnet50, "r100": iresnet100}


def get_backbone(name: str, num_features: int = 512, dropout: float = 0.0, fp16: bool = False):
    """fp16=True: iresnet tự bật autocast bên trong (khối conv), lớp fc cuối chạy fp32 — đúng cách insightface dùng.
    LƯU Ý: iresnet gọi torch.cuda.amp.autocast(self.fp16); nếu fp16=False nó sẽ TẮT autocast bên ngoài."""
    return _ZOO[name.lower()](num_features=num_features, dropout=dropout, fp16=fp16)
