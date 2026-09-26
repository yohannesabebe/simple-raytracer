"""
Light sources for illumination models (Point, Directional, and Ambient lights).
"""

from typing import Union, Tuple
import numpy as np
from .math_utils import normalize


class AmbientLight:
    """
    Constant ambient light illuminating all surfaces equally.
    """
    def __init__(self, color: Union[np.ndarray, list, tuple] = (1.0, 1.0, 1.0), intensity: float = 0.2):
        self.color = np.asarray(color, dtype=np.float32)
        self.intensity = float(intensity)

    def get_contribution(self) -> np.ndarray:
        return self.color * self.intensity


class PointLight:
    """
    Omnidirectional point light source positioned at a specific 3D location.
    """
    def __init__(
        self,
        position: Union[np.ndarray, list, tuple],
        color: Union[np.ndarray, list, tuple] = (1.0, 1.0, 1.0),
        intensity: float = 1.0
    ):
        self.position = np.asarray(position, dtype=np.float32)
        self.color = np.asarray(color, dtype=np.float32)
        self.intensity = float(intensity)

    def get_light_direction_and_distance(self, hit_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates normalized vector pointing from surface hit points to light,
        and the distance from hit points to light source.
        
        Returns:
            Tuple: (light_dir: shape (..., 3), distance: shape (...))
        """
        to_light = self.position - hit_points
        dist = np.linalg.norm(to_light, axis=-1)
        # Avoid division by zero
        safe_dist = np.maximum(dist, 1e-6)[..., np.newaxis]
        light_dir = to_light / safe_dist
        return light_dir, dist


class DirectionalLight:
    """
    Distant directional light (such as the Sun) with parallel rays.
    """
    def __init__(
        self,
        direction: Union[np.ndarray, list, tuple],
        color: Union[np.ndarray, list, tuple] = (1.0, 1.0, 1.0),
        intensity: float = 1.0
    ):
        # Stored as normalized direction from surface TOWARDS the light source
        raw_dir = np.asarray(direction, dtype=np.float32)
        self.light_dir = normalize(raw_dir)
        self.color = np.asarray(color, dtype=np.float32)
        self.intensity = float(intensity)

    def get_light_direction_and_distance(self, hit_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        For directional light, direction is uniform across all points,
        and distance is effectively infinite.
        """
        shape = hit_points.shape[:-1]
        dist = np.full(shape, 1e8, dtype=np.float32)
        light_dir = np.broadcast_to(self.light_dir, hit_points.shape)
        return light_dir, dist
