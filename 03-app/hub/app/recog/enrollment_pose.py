import numpy as np


def pose_ratios(landmarks: np.ndarray) -> tuple[float, float] | None:
    """Measure nose position relative to the eye line and mouth center."""
    if landmarks.shape != (5, 2) or not np.isfinite(landmarks).all():
        return None
    left, right = sorted(landmarks[:2], key=lambda point: point[0])
    eye_line = right - left
    eye_width = float(np.linalg.norm(eye_line))
    if eye_width <= 0:
        return None
    across = eye_line / eye_width
    down = np.array([-across[1], across[0]])
    eyes = (left + right) / 2
    nose = landmarks[2] - eyes
    mouth_height = float((landmarks[3:].mean(axis=0) - eyes) @ down)
    if mouth_height <= 0:
        return None
    return float(nose @ across / eye_width), float(nose @ down / mouth_height)


def matches_enrollment_step(
    index: int, pose: tuple[float, float], frontal: tuple[float, float]
) -> bool:
    yaw, pitch = pose
    front_yaw, front_pitch = frontal
    if index == 0:
        return abs(yaw) <= 0.10 and 0.35 <= pitch <= 0.85
    if index == 1:
        return yaw <= -0.10 and yaw - front_yaw <= -0.12
    if index == 2:
        return yaw >= 0.10 and yaw - front_yaw >= 0.12
    if index == 3:
        return abs(yaw) <= 0.12 and pitch - front_pitch <= -0.07
    if index == 4:
        return abs(yaw) <= 0.12 and pitch - front_pitch >= 0.07
    return False
