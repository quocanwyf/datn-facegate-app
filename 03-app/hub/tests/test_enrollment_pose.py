import numpy as np
import pytest

from app.recog.enrollment_pose import matches_enrollment_step, pose_ratios


@pytest.mark.parametrize(
    ('index', 'nose'),
    [(0, (50, 65)), (1, (42, 65)), (2, (58, 65)), (3, (50, 60)), (4, (50, 70))],
)
def test_only_requested_pose_matches(index, nose):
    def points(nose_position):
        return np.array([(25, 50), (75, 50), nose_position, (35, 80), (65, 80)])

    frontal = pose_ratios(points((50, 65)))
    pose = pose_ratios(points(nose))
    assert frontal is not None and pose is not None
    assert matches_enrollment_step(index, pose, frontal)
    # The initial frontal frame establishes a baseline and has no prior pitch to compare.
    for other in range(1, 5):
        if other != index:
            assert not matches_enrollment_step(other, pose, frontal)


def test_degenerate_landmarks_cannot_be_used():
    assert pose_ratios(np.zeros((5, 2))) is None
