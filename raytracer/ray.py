"""
Ray representation for 3D geometric ray tracing.
"""

from typing import Union
import numpy as np
from .math_utils import normalize


class Ray:
    """
    Parametric 3D Ray: P(t) = origin + t * direction, for t >= 0.
    Supports either single vectors of shape (3,) or batch arrays of shape (..., 3).
    """

    def __init__(self, origin: Union[np.ndarray, list, tuple], direction: Union[np.ndarray, list, tuple], is_normalized: bool = False):
        self.origin = np.asarray(origin, dtype=np.float32)
        direction_arr = np.asarray(direction, dtype=np.float32)
        if is_normalized:
            self.direction = direction_arr
        else:
            self.direction = normalize(direction_arr, axis=-1)

    def point_at(self, t: Union[float, np.ndarray]) -> np.ndarray:
        """
        Evaluates position along ray at distance t: P(t) = origin + t * direction.
        """
        if isinstance(t, np.ndarray):
            if t.ndim < self.direction.ndim:
                t = t[..., np.newaxis]
        return self.origin + t * self.direction

    def __repr__(self) -> str:
        return f"Ray(origin={self.origin}, direction={self.direction})"
