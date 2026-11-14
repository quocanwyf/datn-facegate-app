"""Bước 7 — trích checkpoint chỉ còn BACKBONE để giảm dung lượng upload Kaggle (không tự upload).

    python -m evaltest.strip_backbone --manifest manifest/manifest_24.json --base <02-thuc-nghiem> --out <thư mục đích>

Mỗi file đích giữ: backbone (nguyên tensor, không đổi dtype), config, epoch, global_step, val (best), danh sách khoá
head đã bỏ, b̃ (1 số, nếu có — để ghi ngưỡng học được t = b̃/s), sha256 nguồn. Ghi ``strip_map.json``:
sha256 đích → {sha256 nguồn, id, đường dẫn}. Kiểm ngay sau khi ghi: mọi tensor backbone bằng hệt bản gốc
(``torch.equal``) và sha256 nguồn khớp manifest.
"""
from __future__ import annotations

import argparse
import os

import torch

from .common import dump_json, load_json, sha256_file


def strip_one(src: str, dst: str, src_sha: str) -> dict:
    ck = torch.load(src, map_location="cpu", weights_only=False)
    head = ck.get("head") or {}
    out = {"backbone": ck["backbone"], "config": ck["config"], "epoch": ck["epoch"],
           "global_step": ck.get("global_step"), "val": ck.get("val"), "best": ck.get("best"),
           "head_keys": sorted(head.keys()), "stripped": True, "source_sha256": src_sha}
    if "bias" in head and head["bias"].numel() == 1:
        out["head_bias"] = head["bias"].detach().clone()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    torch.save(out, dst)
    back = torch.load(dst, map_location="cpu", weights_only=False)
    assert back["backbone"].keys() == ck["backbone"].keys()
    assert all(torch.equal(back["backbone"][k], ck["backbone"][k]) for k in ck["backbone"])
    return {"source_sha256": src_sha, "dest_sha256": sha256_file(dst), "bytes_src": os.path.getsize(src),
            "bytes_dst": os.path.getsize(dst)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    m = load_json(a.manifest)
    smap = {}
    for row in m["checkpoints"]:
        src = os.path.join(a.base, row["path"])
        sha = sha256_file(src)
        if sha != row["sha256"]:
            raise SystemExit(f"DỪNG — {row['id']}: sha256 nguồn lệch manifest")
        dst = os.path.join(a.out, row["run"], f"{row['kind']}.pt")
        r = strip_one(src, dst, sha)
        smap[r["dest_sha256"]] = {**r, "id": row["id"], "dest": os.path.relpath(dst, a.out).replace(os.sep, "/")}
        print(row["id"], r["bytes_src"] // 2**20, "MB →", r["bytes_dst"] // 2**20, "MB")
    dump_json(smap, os.path.join(a.out, "strip_map.json"))


if __name__ == "__main__":
    main()
