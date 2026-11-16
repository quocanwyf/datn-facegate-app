"""Người dùng chốt L sau khi đọc báo cáo thật; không tự bật cờ DB/API."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recog.liveness import GROUPS, POLICY_FIELDS, bundle_id, verify_bundle, require_approval
from scripts.collect_liveness import private_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--data-dir', required=True, type=Path, help='HUB_DATA_DIR của đúng Hub sẽ bật')
    parser.add_argument('--threshold', required=True, type=float)
    parser.add_argument('--approved-by', required=True)
    args = parser.parse_args()
    if not math.isfinite(args.threshold) or not 0 <= args.threshold <= 1 or not args.approved_by.strip():
        parser.error('Cần L hữu hạn trong [0,1] và người chốt.')
    content = args.report.read_bytes(); report = json.loads(content)
    verify_bundle()
    if report['schema_version'] != 1 or report['bundle_id'] != bundle_id() or report['participants'] < 1:
        raise SystemExit('Báo cáo khác mô hình hoặc chưa có người tham gia.')
    row = next((row for row in report['thresholds'] if row['threshold'] == args.threshold), None)
    if row is None or any(report['trial_counts'][split].get(group, 0) < 2 for split in ('calibration', 'validation') for group in GROUPS):
        raise SystemExit('L không có trong bảng hoặc chưa đủ lượt/split; không tạo phê duyệt.')
    if any(row[split][group]['frames'] <= 0 for split in ('calibration', 'validation') for group in GROUPS):
        raise SystemExit('Bảng tỷ lệ thiếu nhóm; không tạo phê duyệt.')
    directory = private_root(args.data_dir)
    approval = dict(threshold=args.threshold, approved_by=args.approved_by.strip(), approved_at=datetime.now(timezone.utc).isoformat(),
        bundle_id=bundle_id(), policy={key: report['policy'][key] for key in POLICY_FIELDS},
        trial_counts=report['trial_counts']['validation'], calibration_sha256=hashlib.sha256(content).hexdigest())
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'liveness-approved.json'; temporary = directory / f'.liveness-{uuid4().hex}.tmp'
    try:
        with temporary.open('x', encoding='utf8') as stream: json.dump(approval, stream, indent=2, allow_nan=False)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    require_approval(directory, args.threshold, approval['policy'])
    print('Đã ghi phê duyệt L=', args.threshold, '; chưa thay DB. Chủ DN bật bằng PUT settings hoặc giao diện cấu hình trên đúng Hub.')


if __name__ == '__main__':
    main()
