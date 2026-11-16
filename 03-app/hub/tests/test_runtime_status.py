from types import SimpleNamespace
from uuid import uuid4

from app.recog.decision import Cooldowns
from app.recog.mutations import MutationBarrier
from app.recog.runtime import RecognitionRuntime


def test_status_reload_invalidates_only_changed_employee_cooldown():
    runtime = RecognitionRuntime.__new__(RecognitionRuntime)
    runtime.model_verified = True
    runtime.gallery = SimpleNamespace(reload=lambda rows: 2)
    runtime.sessions = {'old-connection': object()}
    runtime.mutations = MutationBarrier()
    runtime.paused = runtime.mutations.paused
    employee, other, gate = uuid4(), uuid4(), uuid4()
    runtime.cooldowns = Cooldowns({(gate, employee): 10, (gate, other): 11}, {gate: 12})
    # Reload thông thường vẫn giữ chống lặp, kể cả khi đổi kết nối.
    runtime.reload(None)
    assert (gate, employee) in runtime.cooldowns.employees
    completed = runtime.mutations.begin(f'employee/{employee}/status')
    runtime.reload({'complete': completed})
    assert (gate, employee) not in runtime.cooldowns.employees
    assert runtime.cooldowns.employees[(gate, other)] == 11
    assert runtime.cooldowns.alerts[gate] == 12
    assert not runtime.paused.is_set() and not runtime.sessions
