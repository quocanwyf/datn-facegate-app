"""So biên RGB/feature Hub với extract_features đóng băng trên cùng ảnh/cùng device."""
import argparse
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m0_common import reference_rows, select_device, verified_model, aligned_sample, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lfw', required=True, type=Path)
    parser.add_argument('--n', '--limit', dest='n', type=int, default=100)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--device', choices=['cpu', 'cuda', 'auto'], default='cuda')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.n < 1:
        parser.error('--n phải dương')
    import cv2
    import numpy as np
    import torch
    from app.recog.model_loader import extract_aligned_bgr, frozen_features
    from fr.align.detector import YuNetDetector
    device = select_device(args.device)
    backbone, meta, gate = verified_model(device)
    # Loại ảnh fallback theo log gốc; landmark parity riêng kiểm toàn bộ tập, gồm fallback.
    candidates = sorted(row['image'] for row in reference_rows() if row['method'] in ('detect', 'detect_retry'))
    if args.n > len(candidates):
        raise ValueError('Số ảnh yêu cầu vượt số ảnh detect trong log nguồn')
    chosen = random.Random(args.seed).sample(candidates, args.n)
    detector = YuNetDetector(score_threshold=0.6)
    deltas = []
    for name in chosen:
        image = aligned_sample(args.lfw, name, detector)
        hub = extract_aligned_bgr(backbone, image, device)
        reference_u8 = np.ascontiguousarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB).transpose(2, 0, 1))
        direct = frozen_features().extract_features(backbone, torch.from_numpy(reference_u8)[None], device)
        deltas.append(float(np.max(np.abs(hub - direct))))
    maximum = max(deltas)
    write_report(args.output, {'n': len(chosen), 'seed': args.seed, 'device': str(device), 'amp': meta['amp'],
                               'sampling': 'detect/detect_retry trong align_log.csv, sorted + random.Random.sample',
                               'max_abs_delta': maximum, 'tolerance': 1e-5, 'passed_for_selected_images': maximum <= 1e-5,
                               'full_gpu_run': device.type == 'cuda' and args.n >= 100,
                               'gate': gate, 'blufr_repeated': False})
    if maximum > 1e-5:
        raise SystemExit('DỪNG: parity feature không đạt, không nới 1e-5.')


if __name__ == '__main__':
    main()
