import math

def calculate_angle(p1, p2):
    """Calculates the angle between two points in degrees."""
    x1, y1 = p1
    x2, y2 = p2
    theta = math.atan2(y2 - y1, x2 - x1)
    return math.degrees(theta)

def is_fist(hand_landmarks):
    """Detects if a hand is making a fist."""
    wrist = hand_landmarks.landmark[0]
    tips = [8, 12, 16, 20]
    folded_count = 0
    for tip_idx in tips:
        tip = hand_landmarks.landmark[tip_idx]
        pip = hand_landmarks.landmark[tip_idx - 2]
        d_tip_wrist = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
        d_pip_wrist = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
        if d_tip_wrist < d_pip_wrist:
            folded_count += 1
    return folded_count >= 3
