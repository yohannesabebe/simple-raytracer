"""
Ray Tracer Package
A modular, high-performance ray tracing engine with Blinn-Phong shading,
shadow casting, recursive reflections, and OpenGL viewport display.
"""

from .ray import Ray
from .material import Material
from .primitives import Hittable, Sphere, Plane, HitRecord
from .light import PointLight, DirectionalLight, AmbientLight
from .camera import Camera
from .scene import Scene
from .engine import RayTracer

__all__ = [
    "Ray",
    "Material",
    "Hittable",
    "Sphere",
    "Plane",
    "HitRecord",
    "PointLight",
    "DirectionalLight",
    "AmbientLight",
    "Camera",
    "Scene",
    "RayTracer"
]
