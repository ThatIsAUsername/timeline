
from typing import Tuple


def interpolate(v: float, source_range: Tuple[float, float], dest_range: Tuple[float, float]) -> float:
    """
    Interpolate the value v from the source range into the destination range.
    """
    s0, s1 = source_range
    d0, d1 = dest_range
    ratio = (v-s0)/(s1-s0)  # How far this value is in the source range on a scale of 0 to 1.
    answer = d0 + ratio*(d1-d0)  # Interpolated value in the destination range.
    return answer
