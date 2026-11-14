"""Sinh ngưỡng từ log thật và đối chiếu literal SQL, không sửa seed."""
import argparse
import csv
import json
import math
from pathlib import Path
import re
from statistics import mean
from m0_common import ROOT, MODEL_ID, BLUFR, VAL_LOG, write_report


def seed_rows(sql, table):
    pattern = rf'INSERT INTO {table}\(([^)]+)\) VALUES \((.*?)\);'
    for columns, values in re.findall(pattern, sql, flags=re.I):
        parsed = next(csv.reader([values], quotechar="'", skipinitialspace=True))
        yield dict(zip(columns.split(','), parsed, strict=True))


def derive(seed_path=ROOT / '03-app/db/seed.sql'):
    epochs = [json.loads(line) for line in VAL_LOG.read_text(encoding='utf-8').splitlines() if line.strip()]
    epoch = next(item for item in epochs if item.get('epoch') == 18)
    result = json.loads(BLUFR.read_text(encoding='utf-8'))['ket_qua'][MODEL_ID]
    trials = result['blufr']['per_trial']
    if len(trials) != 10:
        raise ValueError('Phải có đúng 10 trial BLUFR nguồn')
    values = {'DEFAULT_VAL': epoch['results']['thr@far=1e-05'],
              'STRICT_TEST': mean(trial['thr_DIR@0.01'] for trial in trials.values()),
              't_eq30': result['meta']['t_eq30']}
    sql = seed_path.read_text(encoding='utf-8')
    model = next(row for row in seed_rows(sql, 'recognition_model') if row['manifest_id'] == MODEL_ID)
    seeded = {row['level']: float(row['cos_threshold']) for row in seed_rows(sql, 'threshold_profile') if row['model_id'] == model['id']}
    seeded['t_eq30'] = float(model['t_bs'])
    refs = {'DEFAULT_VAL': f'{VAL_LOG.relative_to(ROOT).as_posix()}: epoch=18, results[thr@far=1e-05]',
            'STRICT_TEST': f'{BLUFR.relative_to(ROOT).as_posix()}: mean(10 trial thr_DIR@0.01)',
            't_eq30': f'{BLUFR.relative_to(ROOT).as_posix()}: ket_qua[{MODEL_ID}].meta.t_eq30'}
    output = {key: {'value': value, 'source_ref': refs[key], 'seed_literal': seeded[key],
                    'abs_delta': abs(value - seeded[key])} for key, value in values.items()}
    passed = all(math.isfinite(item['value']) and item['abs_delta'] <= 1e-9 for item in output.values())
    return {'thresholds': output, 'tolerance': 1e-9, 'matches_seed': passed, 'blufr_repeated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = derive()
    write_report(args.output, result)
    if not result['matches_seed']:
        raise SystemExit('DỪNG: ngưỡng lệch seed, không tự sửa nguồn.')


if __name__ == '__main__':
    main()
