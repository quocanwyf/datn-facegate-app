"""Hiệu chỉnh T13 từ video camera đã đồng ý ngoài repo; chỉ xuất tổng hợp, không ảnh/vector."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import cv2
import numpy as np
import torch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recog.detector import Detector
from app.recog.liveness import GROUPS, POLICY_FIELDS, Liveness, bundle_id
from scripts.collect_liveness import private_root


def rates(scores, threshold):
    result = {}
    for group in GROUPS:
        values = np.asarray(scores[group], dtype=float)
        if not len(values) or not np.isfinite(values).all():
            raise ValueError('Mỗi nhóm cần khung mặt hợp lệ; không được thay nhóm rỗng bằng 0%.')
        passed = int(np.count_nonzero(values >= threshold))
        result[group] = dict(frames=len(values), accepted=passed, blocked=len(values)-passed, accept_rate=passed/len(values))
    return result


def summaries(scores):
    return {group: dict(valid_frames=len(values), p05=float(np.quantile(values, .05)),
        p50=float(np.quantile(values, .5)), p95=float(np.quantile(values, .95))) for group, values in scores.items() if values}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--max-frames-per-trial', type=int, default=12)
    parser.add_argument('--min-trials-per-group', type=int, default=2)
    args = parser.parse_args()
    if not 5 <= args.max_frames_per_trial <= 120 or args.min_trials_per_group < 2:
        parser.error('Cần 5..120 khung/lượt và ít nhất 2 lượt độc lập mỗi nhóm/mỗi split.')
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise SystemExit('Không có CUDA; không tự đổi sang CPU để báo đạt phép đo GPU.')
    torch.set_num_threads(2)
    root = private_root(args.data)
    metadata = json.loads((root / 'metadata.json').read_text(encoding='utf8'))
    if not all(str(metadata['conditions'].get(key, '')).strip() for key in ('camera', 'lighting', 'distance')):
        raise SystemExit('Cần ghi camera/ánh sáng/khoảng cách thực tế trong metadata.json.')
    policy = {key: metadata['policy'][key] for key in POLICY_FIELDS}
    scores = {split: {group: [] for group in GROUPS} for split in ('calibration', 'validation')}
    trials = {split: Counter() for split in scores}
    invalid = Counter(); seen = set(); trial_ids = set(); participants = set(); hashes = []
    rows = list(csv.DictReader((root / 'trials.csv').open(encoding='utf-8-sig', newline='')))
    if not rows:
        raise SystemExit('Bộ quay đang trống; chưa có kết quả hiệu chỉnh.')
    detector = Detector(policy['min_face_px'], policy['max_abs_yaw_ratio']); model = Liveness(args.device)
    for row in rows:
        participant, group, split = row['participant'], row['group'], row['split']
        if group not in GROUPS or split not in scores or not metadata['participants'].get(participant, {}).get('consent'):
            raise ValueError('Nhãn/split/consent không hợp lệ.')
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() not in ('.mp4', '.avi', '.mov', '.mkv'):
            raise ValueError('Mỗi lượt phải là video camera trong bộ quay riêng.')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen or row['trial'] in trial_ids:
            raise ValueError('Video/lượt trùng lặp; không tính copy thành lượt độc lập hoặc rò split.')
        seen.add(digest); trial_ids.add(row['trial']); hashes.append(digest); participants.add(participant)
        video = cv2.VideoCapture(str(path)); count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        stride = max(1, round(video.get(cv2.CAP_PROP_FPS) / policy['max_fps']))
        used = valid = index = 0
        try:
            while used < args.max_frames_per_trial:
                ok, image = video.read()
                if not ok: break
                index += 1
                if (index-1) % stride: continue
                used += 1
                scale = min(1., policy['frame_long_side'] / max(image.shape[:2]))
                if scale < 1: image = cv2.resize(image, (round(image.shape[1]*scale), round(image.shape[0]*scale)), interpolation=cv2.INTER_AREA)
                ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, policy['jpeg_quality']])
                if not ok: raise ValueError('Không mã hóa được khung hiệu chỉnh.')
                image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                faces = detector.detector.detect(image); observation = detector.observe(image, faces)
                if len(faces) != 1 or not observation.valid:
                    invalid[f'{split}/{group}'] += 1; continue
                scores[split][group].append(model.score(image, observation.bbox)); valid += 1
        finally:
            video.release()
        if not count or valid < 3:
            raise ValueError('Một lượt có dưới 3 khung mặt hợp lệ; quay lại thay vì loại âm thầm làm đẹp tỷ lệ.')
        trials[split][group] += 1
        print(f'Đã chấm {group}/{split}: {valid} khung hợp lệ, {used-valid} khung loại.', flush=True)
    if any(trials[split][group] < args.min_trials_per_group for split in scores for group in GROUPS):
        raise ValueError('Chưa đủ lượt độc lập cho cả bốn nhóm ở calibration và validation.')
    thresholds = []
    for threshold in np.linspace(0, 1, 21):
        thresholds.append(dict(threshold=round(float(threshold), 2), **{split: rates(values, threshold) for split, values in scores.items()}))
    candidates = [row['threshold'] for row in thresholds if row['calibration']['live']['accept_rate'] >= .9
                  and max(row['calibration'][g]['accept_rate'] for g in GROUPS if g != 'live') <= .05]
    report = dict(schema_version=1, purpose='Kiểm thử chức năng nội bộ, không phải kết quả nghiên cứu hay chứng nhận PAD',
        unit='Tỷ lệ theo khung mặt hợp lệ; khung cùng video tương quan, không coi là các lượt độc lập',
        participants=len(participants), conditions=metadata['conditions'], policy=policy, bundle_id=bundle_id(),
        dataset_digest=hashlib.sha256((''.join(sorted(hashes))+(root/'trials.csv').read_text(encoding='utf8')).encode()).hexdigest(),
        runtime=dict(python=platform.python_version(), torch=str(torch.__version__), opencv=cv2.__version__, device=args.device),
        trial_counts={split: dict(values) for split, values in trials.items()}, invalid_frames=dict(invalid),
        distributions={split: summaries(values) for split, values in scores.items()}, thresholds=thresholds,
        suggested_threshold=min(candidates) if candidates else None,
        suggestion_rule='Chỉ dùng calibration: live accept >=90%, mỗi nhóm attack accept <=5%. Không có mức đạt thì không đề xuất L; validation chỉ đối chiếu, người dùng chốt.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
    print('Đã xuất tổng hợp. Chưa phê duyệt/bật chống giả mạo. Suggested L:', report['suggested_threshold'])


if __name__ == '__main__':
    main()
