import math
from typing import Tuple


def calculate_angle_3p(
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
    p3: Tuple[float, float, float]
) -> float:
    """Calculates interior angle in degrees between three points p1-p2-p3 at vertex p2 (returns 0..180 deg)."""
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]

    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
    angle = abs(angle)
    if angle > 180.0:
        angle = 360.0 - angle
    return round(angle, 2)


def calculate_distance(
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float]
) -> float:
    """Calculates Euclidean distance between two points."""
    return round(math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2), 2)
