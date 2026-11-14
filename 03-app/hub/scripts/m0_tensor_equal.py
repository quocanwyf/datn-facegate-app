"""So tensor checkpoint gốc với bản trích sẵn, không torch.save/trích lại backbone."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m0_common import VENDOR, model_row, verified_model, select_device, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stripped', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    import torch
    original, _, gate = verified_model(select_device('cpu'))
    row, reference, _ = model_row()
    mapping = json.loads((VENDOR / 'manifest/strip_map_ban_sao.json').read_text(encoding='utf-8'))
    entry = mapping[reference['sha256']]
    root = args.stripped.resolve()
    path = (root / entry['dest']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Đường dẫn bản trích ngoài thư mục được chỉ định')
    with path.open('rb') as stream:
        actual_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual_sha != entry['dest_sha256']:
        raise SystemExit('DỪNG: hash bản trích không khớp strip_map')
    # Chỉ giải mã sau khi hash khớp nguồn tin cậy.
    stripped = torch.load(path, map_location='cpu', weights_only=False)['backbone']
    source = original.state_dict()
    keys_equal = set(source) == set(stripped)
    mismatches = [key for key in source if key not in stripped or source[key].shape != stripped[key].shape
                  or source[key].dtype != stripped[key].dtype or not torch.equal(source[key].cpu(), stripped[key].cpu())]
    passed = keys_equal and not mismatches
    write_report(args.output, {'model_id': row['id'], 'keys_equal': keys_equal, 'n_keys': len(source),
                               'mismatched_keys': mismatches, 'all_tensors_equal': passed,
                               'stripped_sha256': actual_sha, 'gate': gate, 'blufr_repeated': False})
    if not passed:
        raise SystemExit('DỪNG: torch.equal False hoặc tập khóa khác nhau; không sửa vendor/ngưỡng.')


if __name__ == '__main__':
    main()
