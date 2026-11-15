from app.recog.mutations import MutationBarrier


def test_unrelated_reload_cannot_resume_unfinished_operation():
    barrier=MutationBarrier()
    old_snapshot=barrier.snapshot()
    first=barrier.begin('employee-A')
    assert not barrier.finish_reload(old_snapshot,{})
    second=barrier.begin('employee-B')
    assert not barrier.finish_reload(barrier.snapshot(),second)
    assert barrier.pending('employee-A') and barrier.paused.is_set()
    assert barrier.finish_reload(barrier.snapshot(),first)
    assert not barrier.paused.is_set()


def test_old_completion_cannot_clear_newer_operation_on_same_employee():
    barrier=MutationBarrier()
    first=barrier.begin('employee-A');snapshot=barrier.snapshot()
    retry=barrier.begin('employee-A')
    assert not barrier.finish_reload(snapshot,first)
    assert barrier.pending('employee-A')
    assert barrier.finish_reload(barrier.snapshot(),retry)


def test_failed_cleanup_stays_paused_across_independent_reloads():
    barrier=MutationBarrier()
    barrier.begin('incomplete-delete')
    for _ in range(10):
        assert not barrier.finish_reload(barrier.snapshot(),{})
        assert barrier.paused.is_set()
    completed_retry=barrier.begin('incomplete-delete')
    assert barrier.finish_reload(barrier.snapshot(),completed_retry)


def test_suspend_same_employee_cannot_complete_approval_cleanup():
    barrier=MutationBarrier()
    approval=barrier.begin('employee/A/review/P1/approve')
    suspended=barrier.begin('employee/A/status')
    assert not barrier.finish_reload(barrier.snapshot(),suspended)
    assert barrier.pending('employee/A/review/P1/approve')
    assert barrier.paused.is_set()
    assert barrier.finish_reload(barrier.snapshot(),approval)


def test_full_delete_only_completes_captured_operations_after_success():
    barrier=MutationBarrier()
    barrier.begin('employee/A/review/P1/approve')
    barrier.begin('employee/B/review/P2/approve')
    deletion=barrier.begin('employee/A/delete',supersede_prefix='employee/A/')
    assert barrier.pending('employee/A/review/P1/approve')  # chưa xóa file xong thì vẫn chặn
    assert not barrier.finish_reload(barrier.snapshot(),deletion)
    assert not barrier.pending('employee/A/review/P1/approve')
    assert barrier.pending('employee/B/review/P2/approve')
