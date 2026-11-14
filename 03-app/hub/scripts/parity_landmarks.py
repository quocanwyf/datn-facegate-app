"""Tái lập detector/median fallback của align_lfw trên mọi ảnh trong log, chỉ xuất tổng hợp."""
import argparse
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m0_common import ALIGN_LOG, detect_like_lfw, reference_rows, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lfw', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    import cv2
    import numpy as np
    from fr.align.detector import YuNetDetector
    rows = reference_rows()
    detector = YuNetDetector(score_threshold=0.6)
    landmarks, methods = [], []
    largest_changes = 0
    root = args.lfw.resolve()
    for index, row in enumerate(rows):
        path = (root / row['image']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Ảnh nằm ngoài LFW root')
        image = cv2.imread(str(path))
        if image is None:
            landmarks.append(None); methods.append('read_error'); continue
        face, faces, method = detect_like_lfw(detector, image)
        if face is None:
            landmarks.append(None); methods.append('fallback')
        else:
            landmarks.append(face['landmarks']); methods.append(method)
            if max(faces, key=lambda item: item['box'][2] * item['box'][3]) is not face:
                largest_changes += 1
        if (index + 1) % 2000 == 0:
            print(f'Đã detect {index + 1}/{len(rows)} ảnh', flush=True)
    detected = [value for value in landmarks if value is not None]
    if not detected:
        raise RuntimeError('Không có ảnh detect được, không thể tính median fallback')
    fallback = np.median(np.stack(detected).astype(np.float32), axis=0)
    deltas, within, unreadable = [], 0, 0
    columns = [axis + str(index) for index in range(5) for axis in ('x', 'y')]
    for row, points, method in zip(rows, landmarks, methods, strict=True):
        expected = np.array([float(row[column]) for column in columns], dtype=np.float32)
        if method == 'read_error' or not np.isfinite(expected).all():
            unreadable += 1; continue
        actual = fallback if points is None else points
        delta = float(np.max(np.abs(actual.reshape(10) - expected)))
        deltas.append(delta)
        within += delta <= 0.5
    ratio = within / len(rows) if rows else 0.0
    write_report(args.output, {'source_ref': ALIGN_LOG.relative_to(ALIGN_LOG.parents[3]).as_posix(),
                               'n_reference_images': len(rows), 'n_compared': len(deltas), 'unreadable_or_missing_reference': unreadable,
                               'methods': dict(Counter(methods)), 'changed_method': sum(row['method'] != method for row, method in zip(rows, methods)),
                               'largest_face_selection_changes': largest_changes, 'within_0_5px': within, 'ratio_all_images': ratio,
                               'delta_max': max(deltas) if deltas else None,
                               'delta_percentiles': dict(zip(['p50', 'p90', 'p95', 'p99'], np.percentile(deltas, [50, 90, 95, 99]).tolist())) if deltas else {},
                               'passed': ratio >= .99, 'opencv': cv2.__version__, 'blufr_repeated': False})
    if ratio < .99:
        raise SystemExit('DỪNG: landmark <99% ảnh trong 0.5px; không loại ảnh/nới tiêu chí.')


if __name__ == '__main__':
    main()
