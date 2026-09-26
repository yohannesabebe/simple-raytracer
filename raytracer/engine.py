"""
Core Ray Tracing Engine implementing the Blinn-Phong illumination model,
hard shadow casting, and recursive specular reflections.
"""

from typing import Tuple, List, Optional
import numpy as np

from .ray import Ray
from .scene import Scene
from .material import Material
from .math_utils import dot, normalize, reflect, clamp


class RayTracer:
    """
    High-performance ray tracer with analytical intersection,
    shadow rays, Blinn-Phong shading, and recursive reflection.
    """
    def __init__(self, scene: Scene):
        self.scene = scene

    def trace_rays(
        self,
        ray: Ray,
        max_bounces: int = 3,
        enable_shadows: bool = True,
        enable_reflections: bool = True,
        depth: int = 0
    ) -> np.ndarray:
        """
        Traces a batch of rays through the scene.
        
        Args:
            ray: Ray batch with shape (..., 3).
            max_bounces: Maximum recursive reflection depth.
            enable_shadows: If True, evaluates shadow ray occlusion.
            enable_reflections: If True, traces secondary reflection rays.
            depth: Current recursion depth.
            
        Returns:
            Color array of shape (..., 3) with RGB values in [0, 1].
        """
        shape = ray.direction.shape
        num_rays_shape = shape[:-1]
        
        # Default color is scene background
        colors = np.broadcast_to(self.scene.background_color, shape).copy()
        
        # 1. Find nearest intersection for all rays
        hit_t, hit_points, hit_normals, hit_obj_indices = self._find_nearest_hits(ray)
        hit_mask = np.isfinite(hit_t)
        
        if not np.any(hit_mask):
            return colors

        # Extract only active hitting rays for lighting calculation
        # To maintain vectorized clarity, we evaluate per object type or grouped masks
        local_colors = np.zeros_like(colors)
        
        for obj_idx, obj in enumerate(self.scene.objects):
            obj_mask = hit_mask & (hit_obj_indices == obj_idx)
            if not np.any(obj_mask):
                continue
                
            pts = hit_points[obj_mask]
            norms = hit_normals[obj_mask]
            dirs = ray.direction[obj_mask]
            mat = obj.material
            
            # --- Ambient Component ---
            ambient_contrib = self.scene.ambient_light.get_contribution() * mat.get_ambient(pts)
            obj_color = ambient_contrib.copy()
            
            # --- Direct Light Illumination (Diffuse + Specular) ---
            view_dirs = -dirs  # Vector pointing towards viewer / camera
            diffuse_color = mat.get_diffuse(pts)
            specular_color = mat.specular
            shininess = mat.shininess
            
            for light in self.scene.lights:
                light_dirs, light_dists = light.get_light_direction_and_distance(pts)
                
                # Check shadow occlusion
                if enable_shadows:
                    in_shadow = self._check_shadows(pts, norms, light_dirs, light_dists)
                else:
                    in_shadow = np.zeros(pts.shape[:-1], dtype=bool)
                    
                lit_mask = ~in_shadow
                if not np.any(lit_mask):
                    continue
                    
                l_dirs = light_dirs[lit_mask]
                l_norms = norms[lit_mask]
                v_dirs = view_dirs[lit_mask]
                
                # Lambertian Diffuse: N . L
                n_dot_l = np.maximum(dot(l_norms, l_dirs, keepdims=True), 0.0)
                diffuse_term = diffuse_color[lit_mask] * (light.color * light.intensity) * n_dot_l
                
                # Blinn-Phong Specular: (N . H)^shininess where H = normalize(L + V)
                half_vectors = normalize(l_dirs + v_dirs)
                n_dot_h = np.maximum(dot(l_norms, half_vectors, keepdims=True), 0.0)
                specular_term = specular_color * (light.color * light.intensity) * (n_dot_h ** shininess)
                
                # Add light contribution to lit points
                light_contribution = diffuse_term + specular_term
                obj_color[lit_mask] += light_contribution
                
            # Place computed local illumination back into output
            local_colors[obj_mask] = obj_color
            
        colors[hit_mask] = local_colors[hit_mask]

        # 2. Recursive Specular Reflection
        if enable_reflections and depth < max_bounces:
            # Trace reflections for surfaces with reflectivity > 0
            for obj_idx, obj in enumerate(self.scene.objects):
                refl = obj.material.reflectivity
                if refl <= 0.001:
                    continue
                    
                obj_mask = hit_mask & (hit_obj_indices == obj_idx)
                if not np.any(obj_mask):
                    continue
                    
                pts = hit_points[obj_mask]
                norms = hit_normals[obj_mask]
                dirs = ray.direction[obj_mask]
                
                # Reflected direction: R = D - 2 * (D . N) * N
                refl_dirs = reflect(dirs, norms)
                # Offset ray origin slightly along normal to prevent self-intersection acne
                refl_origins = pts + 2e-3 * norms
                
                reflected_rays = Ray(refl_origins, refl_dirs, is_normalized=True)
                
                # Recursive call
                refl_colors = self.trace_rays(
                    reflected_rays,
                    max_bounces=max_bounces,
                    enable_shadows=enable_shadows,
                    enable_reflections=enable_reflections,
                    depth=depth + 1
                )
                
                # Linear blend between local Phong color and reflected color
                blended = (1.0 - refl) * colors[obj_mask] + refl * refl_colors
                colors[obj_mask] = blended

        return clamp(colors, 0.0, 1.0)

    def _find_nearest_hits(self, ray: Ray, t_min: float = 1e-3) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Finds the closest primitive intersection for all rays.
        
        Returns:
            Tuple of:
            - min_t: Smallest positive intersection distance (inf if miss)
            - hit_points: 3D coordinates of hit points
            - hit_normals: Unit surface normals at hit points
            - hit_indices: Integer index of hit primitive (-1 if miss)
        """
        shape = ray.direction.shape[:-1] if ray.direction.ndim > 1 else ()
        min_t = np.full(shape, np.inf, dtype=np.float32)
        hit_points = np.zeros(ray.direction.shape, dtype=np.float32)
        hit_normals = np.zeros(ray.direction.shape, dtype=np.float32)
        hit_indices = np.full(shape, -1, dtype=np.int32)
        
        for idx, obj in enumerate(self.scene.objects):
            t_obj, pts_obj, norms_obj = obj.intersect(ray, t_min=t_min)
            closer = (t_obj < min_t) & (t_obj > t_min)
            if np.any(closer):
                min_t[closer] = t_obj[closer]
                hit_points[closer] = pts_obj[closer]
                hit_normals[closer] = norms_obj[closer]
                hit_indices[closer] = idx
                
        return min_t, hit_points, hit_normals, hit_indices

    def _check_shadows(
        self,
        hit_points: np.ndarray,
        normals: np.ndarray,
        light_dirs: np.ndarray,
        light_dists: np.ndarray
    ) -> np.ndarray:
        """
        Casts shadow rays from surface towards light source to determine occlusion.
        
        Args:
            hit_points: Intersection points on surface.
            normals: Surface normals (used for shadow acne bias offset).
            light_dirs: Directions towards light source.
            light_dists: Distances to light source.
            
        Returns:
            Boolean array: True if point is in shadow (occluded), False if lit.
        """
        # Bias surface point along normal to avoid self-intersection
        shadow_origins = hit_points + 2e-3 * normals
        shadow_rays = Ray(shadow_origins, light_dirs, is_normalized=True)
        
        in_shadow = np.zeros(hit_points.shape[:-1], dtype=bool)
        
        for obj in self.scene.objects:
            t_obj, _, _ = obj.intersect(shadow_rays, t_min=2e-3, t_max=1e9)
            # Occluded if object is between surface and light source
            occluded = (t_obj > 2e-3) & (t_obj < light_dists)
            in_shadow |= occluded
            
            # Early exit if all points are already occluded
            if np.all(in_shadow):
                break
                
        return in_shadow
