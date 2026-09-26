"""
Surface materials for shading, reflection, and texturing.
"""

from typing import Union, Tuple
import numpy as np


class Material:
    """
    Material defining optical surface properties for Blinn-Phong illumination
    and specular recursive reflections.
    """

    def __init__(
        self,
        diffuse: Union[np.ndarray, list, tuple] = (0.8, 0.8, 0.8),
        ambient: Union[np.ndarray, list, tuple] = None,
        specular: Union[np.ndarray, list, tuple] = (1.0, 1.0, 1.0),
        shininess: float = 32.0,
        reflectivity: float = 0.0,
        is_checkerboard: bool = False,
        checker_color1: Union[np.ndarray, list, tuple] = (0.9, 0.9, 0.9),
        checker_color2: Union[np.ndarray, list, tuple] = (0.15, 0.15, 0.15),
        checker_scale: float = 1.0
    ):
        self.diffuse = np.asarray(diffuse, dtype=np.float32)
        if ambient is None:
            # Default ambient is 15% of diffuse
            self.ambient = self.diffuse * 0.15
        else:
            self.ambient = np.asarray(ambient, dtype=np.float32)
            
        self.specular = np.asarray(specular, dtype=np.float32)
        self.shininess = float(shininess)
        self.reflectivity = float(np.clip(reflectivity, 0.0, 1.0))
        
        # Procedural checkerboard properties
        self.is_checkerboard = is_checkerboard
        self.checker_color1 = np.asarray(checker_color1, dtype=np.float32)
        self.checker_color2 = np.asarray(checker_color2, dtype=np.float32)
        self.checker_scale = float(checker_scale)

    def get_diffuse(self, hit_points: np.ndarray) -> np.ndarray:
        """
        Returns the diffuse color at given 3D hit point(s).
        For procedural checkerboards, alters color based on spatial coordinates.
        Always returns array matching hit_points shape (..., 3).
        """
        if not self.is_checkerboard:
            return np.broadcast_to(self.diffuse, hit_points.shape).copy()
            
        # 2D checkerboard pattern based on horizontal X and Z plane coordinates
        # Offset slightly to prevent negative zero fluctuations
        coord_x = np.floor((hit_points[..., 0] + 1000.0) * self.checker_scale).astype(np.int32)
        coord_z = np.floor((hit_points[..., 2] + 1000.0) * self.checker_scale).astype(np.int32)
        pattern = (coord_x + coord_z) % 2
        
        # Expand dimensions for color blending
        mask = (pattern == 0)[..., np.newaxis]
        return np.where(mask, self.checker_color1, self.checker_color2)

    def get_ambient(self, hit_points: np.ndarray) -> np.ndarray:
        """
        Returns ambient color at given 3D hit point(s), matching hit_points shape (..., 3).
        """
        if not self.is_checkerboard:
            return np.broadcast_to(self.ambient, hit_points.shape).copy()
        diffuse = self.get_diffuse(hit_points)
        return diffuse * 0.15
