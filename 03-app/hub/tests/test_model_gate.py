import json
import pytest
import torch
from app.recog.model_loader import BLUFR, MANIFEST, STRIP_MAP, ModelNotVerified, load_verified


def test_real_checkpoint_passes_four_steps_on_cpu(model_row):
    backbone, meta, report = load_verified(model_row, torch.device('cpu'))
    assert [step['step'] for step in report['steps']] == [1, 2, 3, 4]
    assert all(step['ok'] for step in report['steps'])
    assert meta['epoch'] == 18
    assert abs(meta['t_eq30'] - model_row['t_bs']) <= 1e-6
    assert meta['amp'] is False
    assert not backbone.training
    assert not any(parameter.requires_grad for parameter in backbone.parameters())
    print(json.dumps({'verify_report': report, 'meta': meta}, ensure_ascii=False, indent=2))


def test_wrong_sha_blocked_at_step_1(model_row, tmp_path):
    fake = tmp_path / 'not-a-checkpoint.pt'
    fake.write_bytes(b'Khong phai checkpoint - chi dung kiem thu hash')
    with pytest.raises(ModelNotVerified) as failure:
        load_verified({**model_row, 'source_path': str(fake)}, torch.device('cpu'))
    assert failure.value.code == 'MODEL_NOT_VERIFIED'
    assert failure.value.step == 1


def test_missing_strip_link_blocked_at_step_2(model_row, tmp_path):
    mapping = json.loads(STRIP_MAP.read_text(encoding='utf-8'))
    del mapping[model_row['stripped_sha256']]
    path = tmp_path / 'strip-map.json'
    path.write_text(json.dumps(mapping), encoding='utf-8')
    with pytest.raises(ModelNotVerified) as failure:
        load_verified(model_row, torch.device('cpu'), strip_map_path=path)
    assert failure.value.step == 2


def test_manifest_config_mismatch_converted_to_step_3_error(model_row, tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    next(row for row in manifest['checkpoints'] if row['id'] == model_row['manifest_id'])['config_fingerprint'] = '0' * 64
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ModelNotVerified) as failure:
        load_verified(model_row, torch.device('cpu'), manifest_path=path)
    assert failure.value.step == 3


def test_learned_threshold_mismatch_blocked_at_step_4(model_row, tmp_path):
    reference = json.loads(BLUFR.read_text(encoding='utf-8'))
    reference['ket_qua'][model_row['manifest_id']]['meta']['t_eq30'] += 0.01
    path = tmp_path / 'blufr.json'
    path.write_text(json.dumps(reference), encoding='utf-8')
    with pytest.raises(ModelNotVerified) as failure:
        load_verified(model_row, torch.device('cpu'), blufr_path=path)
    assert failure.value.step == 4
