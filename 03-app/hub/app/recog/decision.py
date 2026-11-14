from collections import Counter, deque
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Params:
    window_size: int
    match_min: int
    unknown_min: int
    spoof_min: int
    lost_face_sec: float
    iou_reset: float
    result_display_sec: float
    cooldown_employee_sec: float
    cooldown_alert_sec: float
    tau: float
    anti_spoof_enabled: bool = False
    liveness_threshold: float | None = None

    def __post_init__(self):
        if type(self.window_size) is not int or self.window_size < 1:
            raise ValueError('W phải là số nguyên dương')
        if any(type(value) is not int or not 1 <= value <= self.window_size for value in (self.match_min, self.unknown_min, self.spoof_min)):
            raise ValueError('Ngưỡng đếm phải trong [1,W]')
        if not math.isfinite(self.tau) or not -1 <= self.tau <= 1:
            raise ValueError('Ngưỡng cosine không hợp lệ')
        if not 0 <= self.iou_reset <= 1 or any(not math.isfinite(value) or value < 0 for value in
                (self.lost_face_sec, self.result_display_sec, self.cooldown_employee_sec, self.cooldown_alert_sec)):
            raise ValueError('Tham số theo dõi/cooldown không hợp lệ')
        if self.anti_spoof_enabled and (self.liveness_threshold is None or not 0 <= self.liveness_threshold <= 1):
            raise ValueError('Bật chống giả mạo cần L trong [0,1]')

    @classmethod
    def from_settings(cls, settings, tau):
        fields = cls.__dataclass_fields__
        return cls(**{key: settings[key] for key in fields if key != 'tau'}, tau=tau)


@dataclass(frozen=True)
class Observation:
    valid: bool
    timestamp: float
    bbox: tuple[float, float, float, float] | None = None
    employee_id: object | None = None
    score: float = -1
    p_live: float | None = None


@dataclass(frozen=True)
class Decision:
    result: str
    employee_id: object | None = None
    score: float | None = None
    n_frames: int = 0
    p_live_min: float | None = None
    suppressed: bool = False
    recorded_at: float | None = None


def is_live(frame, params):
    return not params.anti_spoof_enabled or (frame.p_live is not None and frame.p_live >= params.liveness_threshold)


def decide(window, params: Params) -> Decision | None:
    frames = [frame for frame in window if frame.valid][-params.window_size:]
    live = [frame for frame in frames if is_live(frame, params)]
    minimum = min((frame.p_live for frame in frames if frame.p_live is not None), default=None)
    if len(frames) - len(live) >= params.spoof_min:
        return Decision('SPOOF', n_frames=len(frames), p_live_min=minimum)
    matches = [frame for frame in live if frame.employee_id is not None and frame.score >= params.tau]
    counts = Counter(frame.employee_id for frame in matches)
    for employee_id, count in counts.items():
        if count >= params.match_min:
            votes = [frame.score for frame in matches if frame.employee_id == employee_id]
            return Decision('MATCH', employee_id, sum(votes) / len(votes), len(frames), minimum)
    unknown = sum(frame.score < params.tau for frame in live)
    if len(frames) == params.window_size and unknown >= params.unknown_min and max(counts.values(), default=0) < 2:
        return Decision('UNKNOWN', n_frames=len(frames), p_live_min=minimum)
    return None


def bbox_iou(first, second):
    x, y, w, h = first
    a, b, c, d = second
    overlap = max(0, min(x + w, a + c) - max(x, a)) * max(0, min(y + h, b + d) - max(y, b))
    union = w * h + c * d - overlap
    return overlap / union if union > 0 else 0


@dataclass
class Cooldowns:
    employees: dict = field(default_factory=dict)
    alerts: dict = field(default_factory=dict)


class DeviceSession:
    def __init__(self, params: Params, gate_id=None, cooldowns: Cooldowns | None = None):
        self.params, self.gate_id = params, gate_id
        self.cooldowns = cooldowns if cooldowns is not None else Cooldowns()
        self.window = deque(maxlen=params.window_size)
        self.last_valid = None
        self.last_bbox = None
        self.display_until = float('-inf')

    def clear(self):
        self.window.clear()
        self.last_valid = self.last_bbox = None

    def consume(self, observation: Observation) -> Decision | None:
        now, params = observation.timestamp, self.params
        if self.last_valid is not None and now - self.last_valid > params.lost_face_sec:
            self.clear()
        if now < self.display_until or not observation.valid:
            return None
        if observation.bbox is None:
            raise ValueError('Khung hợp lệ cần bbox')
        if self.last_bbox is not None and bbox_iou(self.last_bbox, observation.bbox) < params.iou_reset:
            self.clear()
        self.last_valid, self.last_bbox = now, observation.bbox
        self.window.append(observation)
        decision = decide(self.window, params)
        if decision is None:
            return None
        self.clear()
        self.display_until = now + params.result_display_sec
        is_match = decision.result == 'MATCH'
        registry = self.cooldowns.employees if is_match else self.cooldowns.alerts
        key = (self.gate_id, decision.employee_id) if is_match else self.gate_id
        previous = registry.get(key)
        duration = params.cooldown_employee_sec if is_match else params.cooldown_alert_sec
        if previous is not None and now - previous < duration:
            return Decision(decision.result, decision.employee_id, decision.score, decision.n_frames, decision.p_live_min, True, previous)
        registry[key] = now
        return decision
