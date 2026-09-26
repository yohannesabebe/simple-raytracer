"""
Pinhole Camera with spherical orbit, panning, zoom controls, and ray generation.
"""

from typing import Union, Tuple
import numpy as np
from .ray import Ray
from .math_utils import normalize, cross


class Camera:
    """
    Virtual pinhole camera model.
    Produces view rays for every screen pixel coordinate.
    """
    def __init__(
        self,
        eye: Union[np.ndarray, list, tuple] = (0.0, 2.5, 6.0),
        target: Union[np.ndarray, list, tuple] = (0.0, 0.5, 0.0),
        up: Union[np.ndarray, list, tuple] = (0.0, 1.0, 0.0),
        fov_degrees: float = 55.0,
        aspect_ratio: float = 4.0 / 3.0
    ):
        self.eye = np.asarray(eye, dtype=np.float32)
        self.target = np.asarray(target, dtype=np.float32)
        self.world_up = normalize(np.asarray(up, dtype=np.float32))
        self.fov_degrees = float(fov_degrees)
        self.aspect_ratio = float(aspect_ratio)
        
        # Calculate spherical coordinates relative to target for intuitive orbit
        offset = self.eye - self.target
        self.radius = float(np.linalg.norm(offset))
        if self.radius > 1e-4:
            self.pitch = float(np.arcsin(np.clip(offset[1] / self.radius, -0.99, 0.99)))
            self.yaw = float(np.arctan2(offset[0], offset[2]))
        else:
            self.pitch = 0.2
            self.yaw = 0.0
            self.radius = 5.0
            
        self._update_vectors()

    def _update_vectors(self):
        """
        Recomputes camera orthonormal coordinate system (u, v, forward).
        """
        # Calculate eye position from spherical coordinates
        cos_pitch = np.cos(self.pitch)
        x = self.radius * cos_pitch * np.sin(self.yaw)
        y = self.radius * np.sin(self.pitch)
        z = self.radius * cos_pitch * np.cos(self.yaw)
        self.eye = self.target + np.array([x, y, z], dtype=np.float32)
        
        # Camera look direction
        self.forward = normalize(self.target - self.eye)
        # Right direction
        self.right = normalize(cross(self.forward, self.world_up))
        # Camera local up direction
        self.up = cross(self.right, self.forward)
        
        # Viewport dimensions at distance = 1
        theta = np.radians(self.fov_degrees)
        self.viewport_height = 2.0 * np.tan(theta / 2.0)
        self.viewport_width = self.viewport_height * self.aspect_ratio

    def orbit(self, delta_yaw: float, delta_pitch: float):
        """
        Rotates camera around target.
        """
        self.yaw += delta_yaw
        # Constrain pitch to avoid flipping over poles (-89 to +89 degrees)
        max_pitch = np.radians(89.0)
        self.pitch = float(np.clip(self.pitch + delta_pitch, -max_pitch, max_pitch))
        self._update_vectors()

    def zoom(self, delta_radius: float):
        """
        Zooms closer to or farther from target.
        """
        self.radius = float(np.clip(self.radius + delta_radius, 0.5, 50.0))
        self._update_vectors()

    def pan(self, delta_x: float, delta_y: float):
        """
        Pans camera and target along the camera's local right and up axes.
        """
        offset = -self.right * delta_x + self.up * delta_y
        self.target += offset
        self._update_vectors()

    def set_aspect_ratio(self, width: int, height: int):
        """
        Updates viewport aspect ratio.
        """
        self.aspect_ratio = float(width) / float(max(height, 1))
        self._update_vectors()

    def generate_rays(self, width: int, height: int, jitter: bool = False) -> Ray:
        """
        Generates 2D array of camera rays for all pixels in screen grid (height, width).
        
        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            jitter: If True, adds sub-pixel jitter for stochastic anti-aliasing.
            
        Returns:
            Ray object with origins (height, width, 3) and directions (height, width, 3).
        """
        # Normalized device coordinates from -0.5 to +0.5
        u_vals = np.linspace(-0.5, 0.5, width, endpoint=False, dtype=np.float32) + (0.5 / width)
        v_vals = np.linspace(0.5, -0.5, height, endpoint=False, dtype=np.float32) - (0.5 / height)
        
        u_grid, v_grid = np.meshgrid(u_vals, v_vals)
        
        if jitter:
            # Subpixel jitter for anti-aliasing
            u_grid += (np.random.rand(height, width).astype(np.float32) - 0.5) / width
            v_grid += (np.random.rand(height, width).astype(np.float32) - 0.5) / height
            
        # Scale to viewport dimensions
        u_scaled = u_grid[..., np.newaxis] * self.viewport_width
        v_scaled = v_grid[..., np.newaxis] * self.viewport_height
        
        # Ray direction: forward + u * right + v * up
        directions = self.forward + u_scaled * self.right + v_scaled * self.up
        directions = normalize(directions, axis=-1)
        
        origins = np.broadcast_to(self.eye, directions.shape)
        
        return Ray(origins, directions, is_normalized=True)
