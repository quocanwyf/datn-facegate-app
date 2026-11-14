"""Vét cạn trạng thái, không mô hình/ảnh/DB và không sinh sự kiện demo."""
from collections import deque
from dataclasses import replace
from itertools import product
import pytest
from app.recog.decision import Params, Observation, DeviceSession, decide, Cooldowns

PARAMS = Params(5, 3, 4, 3, 1.0, .3, 3, 60, 15, .5, True, .5)


def reference_decide(frames, params):
    # Viết độc lập bằng đếm trực tiếp, không gọi helper của implementation.
    frames = [f for f in frames if f.valid][-params.window_size:]
    lives = [f for f in frames if not params.anti_spoof_enabled or (f.p_live is not None and f.p_live >= params.liveness_threshold)]
    if len(frames) - len(lives) >= params.spoof_min:
        return 'SPOOF', None, None
    ids = list(dict.fromkeys(f.employee_id for f in lives if f.employee_id is not None and f.score >= params.tau))
    votes = {identity: [f.score for f in lives if f.employee_id == identity and f.score >= params.tau] for identity in ids}
    winner = next((identity for identity in ids if len(votes[identity]) >= params.match_min), None)
    if winner is not None:
        return 'MATCH', winner, sum(votes[winner]) / len(votes[winner])
    if len(frames) == params.window_size and sum(f.score < params.tau for f in lives) >= params.unknown_min and all(len(scores) < 2 for scores in votes.values()):
        return 'UNKNOWN', None, None
    return None


def simplified(decision):
    return (decision.result, decision.employee_id, decision.score) if decision else None


def reference_step(state, frame):
    frames, last, box, display = state
    frames = list(frames)
    if last is not None and frame.timestamp - last > 1:
        frames, last, box = [], None, None
    if frame.timestamp < display or not frame.valid:
        return (frames, last, box, display), None
    if box is not None:
        # Các bbox trong tập vét cạn hoặc trùng nhau hoặc rời hoàn toàn.
        if frame.bbox != box:
            frames = []
    frames = (frames + [frame])[-5:]
    result = reference_decide(frames, PARAMS)
    if result:
        return ([], None, None, frame.timestamp + 3), result
    return (frames, frame.timestamp, frame.bbox, display), None


@pytest.mark.parametrize('variant', ['normal', 'lost_face', 'iou_reset'])
def test_all_sequences_length_1_to_8(variant):
    checked = 0
    session = DeviceSession(PARAMS)

    def visit(depth, reference_state, raw):
        nonlocal checked
        if depth == 8:
            return
        saved = (tuple(session.window), session.last_valid, session.last_bbox, session.display_until,
                 dict(session.cooldowns.employees), dict(session.cooldowns.alerts))
        for symbol in ('INVALID', 'NL', 'LA', 'LB', 'LN'):
            session.window = deque(saved[0], maxlen=5)
            session.last_valid, session.last_bbox, session.display_until = saved[1:4]
            session.cooldowns.employees = dict(saved[4]); session.cooldowns.alerts = dict(saved[5])
            timestamp = depth * .1 + (2 if variant == 'lost_face' and depth >= 4 else 0)
            bbox = (400 if variant == 'iou_reset' and depth >= 4 else 0, 0, 100, 100)
            frame = Observation(symbol != 'INVALID', timestamp, bbox, {'LA': 'A', 'LB': 'B'}.get(symbol),
                                .5 if symbol in ('LA', 'LB') else .4, 0 if symbol == 'NL' else .5)
            # So cả hàm thuần trên cửa sổ và máy trạng thái sau từng tiền tố.
            raw_new = (raw + [frame])[-5:]
            assert simplified(decide(raw_new, PARAMS)) == reference_decide(raw_new, PARAMS)
            ref_next, expected = reference_step(reference_state, frame)
            actual = session.consume(frame)
            assert simplified(actual) == expected
            assert list(session.window) == ref_next[0]
            if actual:
                assert not session.window
            checked += 1
            visit(depth + 1, ref_next, raw_new)
    visit(0, ([], None, None, float('-inf')), [])
    assert checked == sum(5 ** n for n in range(1, 9))
    print(f'variant={variant}; sequences={checked}; max_length=8')


def test_priorities_boundaries_invalid_and_cooldown():
    box = (0, 0, 100, 100)
    live = Observation(True, 0, box, 'A', .5, .5)
    spoof = replace(live, p_live=.49)
    params = replace(PARAMS, match_min=2, spoof_min=2)
    assert decide([live, live, spoof, spoof], params).result == 'SPOOF'
    assert decide([live] * 3, PARAMS).result == 'MATCH'
    assert decide([replace(live, p_live=None)] * 3, replace(PARAMS, anti_spoof_enabled=False)).result == 'MATCH'
    session = DeviceSession(PARAMS)
    session.consume(live)
    session.consume(Observation(False, .9))
    assert len(session.window) == 1
    session.consume(Observation(False, 1))
    assert len(session.window) == 1  # chỉ xóa khi > 1,0 giây
    session.consume(Observation(False, 1.01))
    assert not session.window
    registry = Cooldowns()
    first, second = DeviceSession(PARAMS, 'gate', registry), DeviceSession(PARAMS, 'gate', registry)
    for t in (0, .1, .2):
        result = first.consume(replace(live, timestamp=t))
    assert result and not result.suppressed
    for t in (4, 4.1, 4.2):
        result = second.consume(replace(live, timestamp=t))
    assert result and result.suppressed and result.recorded_at == .2
    for t in (64, 64.1, 64.2):
        result = first.consume(replace(live, timestamp=t))
    assert result and not result.suppressed


@pytest.mark.parametrize('changes', [{'window_size':0}, {'match_min':6}, {'unknown_min':0}, {'liveness_threshold':None}, {'tau':float('nan')}])
def test_invalid_parameters_rejected(changes):
    with pytest.raises(ValueError):
        replace(PARAMS, **changes)
