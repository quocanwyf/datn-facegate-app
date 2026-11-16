"""Fixture tổng hợp chỉ kiểm parity/đường điều khiển; không hiệu chỉnh L hay ghi DB."""
from datetime import datetime, timezone
import importlib.util
import json
from threading import Event
from types import SimpleNamespace
from uuid import uuid4
import cv2
import numpy as np
import pytest
import torch
from app.recog.liveness import BUNDLE, MODELS, Liveness, bundle_id, input_tensor, require_approval, verify_bundle
from app.recog.decision import Cooldowns
from app.recog.runtime import FrameError, RecognitionRuntime
from app.recog.detector import FrameObs
from scripts.collect_liveness import DEFAULT_POLICY


def test_preprocessing_and_ensemble_match_pinned_upstream():
    torch.set_num_threads(2)
    verify_bundle()
    spec = importlib.util.spec_from_file_location('t13_upstream_functional', BUNDLE/'src/data_io/functional.py')
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    image = np.random.default_rng(13).integers(0, 256, (240, 320, 3), dtype=np.uint8)
    assert torch.equal(input_tensor(image), reference.to_tensor(image).unsqueeze(0))
    model = Liveness(); actual = model.probabilities(image, (0, 8, 95, 111))
    from vendor.silentface.src.generate_patches import CropImage
    from vendor.silentface.src.model_lib import MiniFASNet
    prediction = np.zeros((1, 3))
    for filename, architecture, scale in MODELS:
        network = getattr(MiniFASNet, architecture)(conv6_kernel=(5, 5))
        original = torch.load(BUNDLE/filename, map_location='cpu', weights_only=True)
        network.load_state_dict({key.removeprefix('module.'): value for key, value in original.items()}); network.eval()
        crop = CropImage().crop(image, (0, 8, 95, 111), scale, 80, 80)
        with torch.no_grad(): prediction += torch.softmax(network(reference.to_tensor(crop).unsqueeze(0)), dim=1).numpy()
    np.testing.assert_allclose(actual, prediction[0]/2, atol=1e-7)
    assert model.score(image, (0, 8, 95, 111)) == pytest.approx(prediction[0, 1]/2, abs=1e-7)
    assert actual.sum() == pytest.approx(1, abs=1e-6)


def test_approval_requires_real_workflow_marker_and_matching_policy(tmp_path):
    with pytest.raises(OSError): require_approval(tmp_path, .7, DEFAULT_POLICY)
    approval = dict(threshold=.7, bundle_id=bundle_id(), policy=DEFAULT_POLICY, approved_by='fixture only',
        approved_at=datetime.now(timezone.utc).isoformat(), trial_counts={key: 2 for key in ('live','print','phone','replay')}, calibration_sha256='0'*64)
    path = tmp_path/'liveness-approved.json'; path.write_text(json.dumps(approval))
    assert require_approval(tmp_path, .7, DEFAULT_POLICY)['threshold'] == .7
    for threshold, policy in [(.8, DEFAULT_POLICY), (.7, dict(DEFAULT_POLICY, jpeg_quality=70)), (.7, dict(DEFAULT_POLICY, spoof_min=1))]:
        with pytest.raises(ValueError): require_approval(tmp_path, threshold, policy)
    approval['trial_counts']['replay'] = 0; path.write_text(json.dumps(approval))
    with pytest.raises(ValueError): require_approval(tmp_path, .7, DEFAULT_POLICY)


def runtime_fixture(live):
    runtime = RecognitionRuntime.__new__(RecognitionRuntime)
    runtime.model_verified = True; runtime.model = {'id': uuid4()}; runtime.paused = Event()
    runtime.gallery = SimpleNamespace(ready=True, size=1, top1=lambda vector: ('fixture-employee', .99))
    observation = FrameObs(True, bbox=(100, 80, 100, 110), landmarks=np.zeros((5, 2)), det_score=.99, yaw_ratio=0.)
    runtime.detector = SimpleNamespace(detector=SimpleNamespace(detect=lambda image: [{}]), observe=lambda image, faces: observation)
    runtime.embedder = SimpleNamespace(embed=lambda image, landmarks: np.ones(512))
    runtime.liveness = SimpleNamespace(score=lambda image, bbox: live)
    runtime.samples = {}; runtime.sessions = {}; runtime.cooldowns = Cooldowns()
    settings = dict(DEFAULT_POLICY, result_display_sec=3, cooldown_employee_sec=60, cooldown_alert_sec=15, anti_spoof_enabled=True, liveness_threshold=.7)
    _, encoded = cv2.imencode('.jpg', np.zeros((240, 320, 3), dtype=np.uint8))
    payload = dict(settings=settings, jpeg=encoded.tobytes(), mode='recognize', connection_id='fixture', gate_id=uuid4(), tau=.5)
    return runtime, payload


def test_spoof_has_priority_and_enrollment_does_not_accept_fake(monkeypatch):
    monkeypatch.setattr('app.recog.runtime.require_approval', lambda *args: None)
    runtime, payload = runtime_fixture(.1)
    runtime.embedder.embed = lambda *args: pytest.fail('Không embed khung không live')
    for _ in range(2): assert runtime.frame(payload)['state'] == 'CHECKING'
    output = runtime.frame(payload)
    assert output['decision'].result == 'SPOOF' and output['decision'].p_live_min == .1 and 'crop' in output
    payload.update(mode='enroll', enroll_session_id=uuid4(), employee_id=uuid4())
    key = (payload['connection_id'], payload['enroll_session_id'], payload['employee_id'])
    runtime.samples[key] = [{'p_live': None}] * 4
    runtime.sample_policies = {key: dict(payload['settings'], anti_spoof_enabled=False)}
    rejected = runtime.frame(payload)
    assert rejected == {'type':'enroll_progress','accepted':0,'total':5,'reason':'SPOOF'}
    assert all(not samples for samples in runtime.samples.values())


def test_disabled_flag_preserves_match_without_loading_liveness():
    runtime, payload = runtime_fixture(None); payload['settings']['anti_spoof_enabled'] = False
    runtime.liveness.score = lambda *args: pytest.fail('Không gọi liveness khi tắt')
    for _ in range(2): assert runtime.frame(payload)['state'] == 'CHECKING'
    output = runtime.frame(payload)
    assert output['decision'].result == 'MATCH' and output['decision'].p_live_min is None
    runtime.gallery.size = 0
    assert runtime.frame(payload) == {'type':'state','state':'NO_GALLERY'}


def test_unapproved_enabled_settings_fail_closed(monkeypatch):
    runtime, payload = runtime_fixture(.99)
    def missing(*args): raise FileNotFoundError()
    monkeypatch.setattr('app.recog.runtime.require_approval', missing)
    with pytest.raises(FrameError, match='chốt L'): runtime.frame(payload)


def test_opt_in_timings_preserve_result_and_report_executed_stages_only():
    runtime, payload = runtime_fixture(None); runtime.device = torch.device('cpu')
    payload['settings']['anti_spoof_enabled'] = False
    timings = []; runtime.timing_sink = timings.append
    for _ in range(3): result = runtime.frame(payload)
    assert result['decision'].result == 'MATCH' and len(timings) == 3
    assert set(timings[0]['stages_ms']) == {'decode', 'yunet', 'embed', 'top1', 'decision'}
    assert all(value >= 0 for row in timings for value in row['stages_ms'].values())
    assert all(row['total_ms'] >= max(row['stages_ms'].values()) for row in timings)


def test_oversized_jpeg_is_rejected_before_full_pixel_decode(monkeypatch):
    runtime, payload = runtime_fixture(None); payload['settings']['anti_spoof_enabled'] = False
    _, encoded = cv2.imencode('.jpg', np.zeros((800, 800, 3), dtype=np.uint8))
    payload['jpeg'] = encoded.tobytes()
    monkeypatch.setattr(cv2, 'imdecode', lambda *args: pytest.fail('Không cấp phát pixel trước khi kiểm header'))
    with pytest.raises(FrameError, match='vượt kích thước'): runtime.frame(payload)
