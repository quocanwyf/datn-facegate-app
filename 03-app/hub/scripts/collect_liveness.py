"""Khởi tạo/thu video T13 ngoài repo. Chỉ quay khi có --consent và người dùng bấm Space."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from uuid import uuid4
import cv2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.recog.liveness import GROUPS

DEFAULT_POLICY = dict(frame_long_side=640, jpeg_quality=80, min_face_px=80, max_abs_yaw_ratio=.35,
    max_fps=4, window_size=5, match_min=3, unknown_min=4, spoof_min=3, lost_face_sec=1., iou_reset=.3)
FIELDS = ('participant', 'group', 'split', 'trial', 'path')


def private_root(path):
    path = Path(path).resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError('Video/ảnh mặt phải nằm ngoài repo.')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'capture'])
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--participant', default='U01')
    parser.add_argument('--group', choices=GROUPS)
    parser.add_argument('--split', choices=['calibration', 'validation'], default='calibration')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--seconds', type=float, default=3)
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--consent', action='store_true')
    args = parser.parse_args()
    root = private_root(args.data)
    if not re.fullmatch(r'U\d{2,4}', args.participant):
        parser.error('Dùng mã ẩn danh U01..U9999, không dùng tên người.')
    root.mkdir(parents=True, exist_ok=True)
    if args.action == 'init':
        metadata = root / 'metadata.json'
        if metadata.exists():
            raise SystemExit('Đã có metadata; không ghi đè bộ quay đang dùng.')
        for group in GROUPS:
            (root / group).mkdir(exist_ok=True)
        metadata.write_text(json.dumps({'conditions': {'camera': '', 'lighting': '', 'distance': '', 'notes': ''},
            'participants': {args.participant: {'consent': False}}, 'policy': DEFAULT_POLICY}, indent=2), encoding='utf8')
        with (root / 'trials.csv').open('x', newline='', encoding='utf8') as stream:
            csv.DictWriter(stream, fieldnames=FIELDS).writeheader()
        print('Đã tạo bộ quay trống ngoài repo. Điền điều kiện và consent trong metadata.json trước khi quay.')
        return
    metadata = json.loads((root / 'metadata.json').read_text(encoding='utf8'))
    if not args.consent or not metadata.get('participants', {}).get(args.participant, {}).get('consent'):
        parser.error('Cần người tình nguyện đồng ý, consent=true trong metadata và --consent.')
    if not args.group or not .5 <= args.seconds <= 15 or not 1 <= args.trials <= 100:
        parser.error('Cần --group, seconds 0.5..15, trials 1..100.')
    camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        raise SystemExit('Chưa mở được webcam; không có video nào được ghi.')
    writer = None
    try:
        print(f'Nhóm {args.group}; split {args.split}. Space bắt đầu mỗi lượt; Esc dừng. Video riêng ngoài Git.')
        for _ in range(args.trials):
            while True:
                ok, frame = camera.read()
                if not ok: raise RuntimeError('Camera không trả khung hình.')
                cv2.putText(frame, f'{args.group} / {args.split} - SPACE record, ESC stop', (16, 32), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 255, 255), 2)
                cv2.imshow('FaceGate T13 capture', frame)
                key = cv2.waitKey(20) & 255
                if key == 27: return
                if key == 32: break
            trial = uuid4().hex
            relative = f'{args.group}/{args.participant}-{trial}.mp4'
            writer = cv2.VideoWriter(str(root / relative), cv2.VideoWriter_fourcc(*'mp4v'), 15., (frame.shape[1], frame.shape[0]))
            if not writer.isOpened(): raise RuntimeError('Không mở được bộ ghi video.')
            begin = time.perf_counter(); frames = 0
            while time.perf_counter() - begin < args.seconds:
                ok, frame = camera.read()
                if not ok: raise RuntimeError('Mất camera giữa lượt; video này không được thêm manifest.')
                writer.write(frame); frames += 1
                cv2.imshow('FaceGate T13 capture', frame)
                if cv2.waitKey(1) & 255 == 27: return
                time.sleep(max(0, begin + frames / 15. - time.perf_counter()))
            writer.release(); writer = None
            with (root / 'trials.csv').open('a', newline='', encoding='utf8') as stream:
                csv.DictWriter(stream, fieldnames=FIELDS).writerow(dict(participant=args.participant, group=args.group, split=args.split, trial=trial, path=relative))
            print(f'Đã ghi 1 lượt {args.group}/{args.split}; {frames} khung, {datetime.now(timezone.utc).isoformat()}')
    finally:
        if writer is not None: writer.release()
        camera.release(); cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
