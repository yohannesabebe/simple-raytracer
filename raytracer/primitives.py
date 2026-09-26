"""
Geometric primitives and intersection calculations for ray tracing.
Implements Sphere and Plane geometry with analytical ray intersection solutions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
import numpy as np

from .ray import Ray
from .material import Material
from .math_utils import dot, normalize


class HitRecord:
    """
    Stores ray-primitive intersection data.
    """
    def __init__(
        self,
        t: np.ndarray,
        point: np.ndarray,
        normal: np.ndarray,
        material: Material
    ):
        self.t = t
        self.point = point
        self.normal = normal
        self.material = material


class Hittable(ABC):
    """
    Abstract base class for 3D renderable surfaces.
    """
    def __init__(self, material: Material):
        self.material = material

    @abstractmethod
    def intersect(self, ray: Ray, t_min: float = 1e-4, t_max: float = 1e9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates intersection of ray with primitive.
        
        Args:
            ray: Ray instance (origin and direction arrays).
            t_min: Minimum valid intersection distance (bias to prevent self-shadowing).
            t_max: Maximum distance to consider.
            
        Returns:
            Tuple of:
            - t: Intersection distances (float array, inf where no hit)
            - points: 3D hit positions (array of shape (..., 3))
            - normals: Surface unit normals at hit points (shape (..., 3))
        """
        pass


class Sphere(Hittable):
    """
    3D Sphere primitive defined by center and radius.
    """
    def __init__(self, center: Union[np.ndarray, list, tuple], radius: float, material: Material):
        super().__init__(material)
        self.center = np.asarray(center, dtype=np.float32)
        self.radius = float(radius)
        self.radius_sq = self.radius * self.radius

    def intersect(self, ray: Ray, t_min: float = 1e-4, t_max: float = 1e9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Analytical Ray-Sphere intersection using quadratic equation:
        |P(t) - C|^2 = r^2
        """
        # Vector from sphere center to ray origin: V = O - C
        oc = ray.origin - self.center
        
        # Coefficients of quadratic equation a*t^2 + 2*half_b*t + c = 0
        # Since ray.direction is normalized, a = |D|^2 = 1.0
        half_b = dot(ray.direction, oc)
        c = dot(oc, oc) - self.radius_sq
        discriminant = half_b * half_b - c
        
        hit_mask = discriminant >= 0.0
        
        # Initialize result buffers with inf (miss)
        shape = ray.direction.shape[:-1] if ray.direction.ndim > 1 else ()
        t_out = np.full(shape, np.inf, dtype=np.float32)
        points_out = np.zeros(ray.direction.shape, dtype=np.float32)
        normals_out = np.zeros(ray.direction.shape, dtype=np.float32)
        
        if not np.any(hit_mask):
            return t_out, points_out, normals_out
            
        sqrt_disc = np.zeros_like(discriminant)
        sqrt_disc[hit_mask] = np.sqrt(discriminant[hit_mask])
        
        # Check nearest root first: t1 = -half_b - sqrt(disc)
        t1 = -half_b - sqrt_disc
        valid_t1 = hit_mask & (t1 > t_min) & (t1 < t_max)
        
        # Check second root if nearest is behind ray: t2 = -half_b + sqrt(disc)
        t2 = -half_b + sqrt_disc
        valid_t2 = hit_mask & (~valid_t1) & (t2 > t_min) & (t2 < t_max)
        
        # Assign minimum positive distance
        t_out[valid_t1] = t1[valid_t1]
        t_out[valid_t2] = t2[valid_t2]
        
        has_hit = valid_t1 | valid_t2
        if np.any(has_hit):
            # Compute hit points: P = O + t * D
            t_expanded = t_out[..., np.newaxis]
            pts = ray.origin + t_expanded * ray.direction
            points_out[has_hit] = pts[has_hit]
            
            # Outward surface normal: N = (P - C) / radius
            sphere_center = self.center
            norms = (pts - sphere_center) / self.radius
            normals_out[has_hit] = norms[has_hit]
            
        return t_out, points_out, normals_out


class Plane(Hittable):
    """
    Infinite 3D Plane primitive defined by a point on the plane and surface normal.
    """
    def __init__(self, point: Union[np.ndarray, list, tuple], normal: Union[np.ndarray, list, tuple], material: Material):
        super().__init__(material)
        self.point = np.asarray(point, dtype=np.float32)
        self.normal = normalize(np.asarray(normal, dtype=np.float32))

    def intersect(self, ray: Ray, t_min: float = 1e-4, t_max: float = 1e9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Analytical Ray-Plane intersection:
        (P(t) - P0) . N = 0  =>  t = ((P0 - O) . N) / (D . N)
        """
        denom = dot(ray.direction, self.normal)
        
        # Avoid division by zero if ray is parallel to plane
        parallel_mask = np.abs(denom) < 1e-6
        
        # Vector from ray origin to plane reference point
        p0_minus_o = self.point - ray.origin
        numerator = dot(p0_minus_o, self.normal)
        
        # Safe division
        safe_denom = np.where(parallel_mask, 1.0, denom)
        t = numerator / safe_denom
        
        shape = ray.direction.shape[:-1] if ray.direction.ndim > 1 else ()
        t_out = np.full(shape, np.inf, dtype=np.float32)
        points_out = np.zeros(ray.direction.shape, dtype=np.float32)
        normals_out = np.zeros(ray.direction.shape, dtype=np.float32)
        
        valid_hit = (~parallel_mask) & (t > t_min) & (t < t_max)
        
        if np.any(valid_hit):
            t_out[valid_hit] = t[valid_hit]
            t_expanded = t_out[..., np.newaxis]
            pts = ray.origin + t_expanded * ray.direction
            points_out[valid_hit] = pts[valid_hit]
            
            # Plane normal oriented towards incident ray
            norm_tile = np.broadcast_to(self.normal, ray.direction.shape).copy()
            # If ray direction and normal point in same direction, flip normal
            flip_mask = denom > 0.0
            norm_tile[flip_mask] = -norm_tile[flip_mask]
            normals_out[valid_hit] = norm_tile[valid_hit]
            
        return t_out, points_out, normals_out
