"""
Scene management and preset test scenes for computer graphics demonstration.
"""

from typing import List, Union
import numpy as np

from .primitives import Hittable, Sphere, Plane
from .light import PointLight, DirectionalLight, AmbientLight
from .material import Material


class Scene:
    """
    Container for all 3D geometry and lights in the ray-traced environment.
    """
    def __init__(
        self,
        name: str = "Scene",
        ambient_light: AmbientLight = None,
        background_color: Union[np.ndarray, list, tuple] = (0.05, 0.07, 0.12)
    ):
        self.name = name
        self.objects: List[Hittable] = []
        self.lights: List[Union[PointLight, DirectionalLight]] = []
        self.ambient_light = ambient_light or AmbientLight(color=(1.0, 1.0, 1.0), intensity=0.15)
        self.background_color = np.asarray(background_color, dtype=np.float32)

    def add_object(self, obj: Hittable):
        self.objects.append(obj)

    def add_light(self, light: Union[PointLight, DirectionalLight]):
        self.lights.append(light)


def create_showcase_scene() -> Scene:
    """
    Comprehensive showcase scene featuring:
    - Chrome mirror sphere (high reflectivity)
    - Glossy ruby plastic sphere (diffuse + sharp specular highlight)
    - Polished gold metallic sphere
    - Emerald sphere
    - Reflective checkerboard ground plane
    - Dual point lights for multi-colored specular highlights and overlapping shadows
    """
    scene = Scene(name="Showcase Studio", ambient_light=AmbientLight(color=(1.0, 1.0, 1.0), intensity=0.12))

    # Checkerboard floor
    floor_material = Material(
        diffuse=(0.8, 0.8, 0.8),
        specular=(0.4, 0.4, 0.4),
        shininess=32.0,
        reflectivity=0.25,
        is_checkerboard=True,
        checker_color1=(0.95, 0.95, 0.95),
        checker_color2=(0.12, 0.12, 0.15),
        checker_scale=0.5
    )
    scene.add_object(Plane(point=(0.0, 0.0, 0.0), normal=(0.0, 1.0, 0.0), material=floor_material))

    # Chrome Mirror Sphere (Center-Left)
    mirror_material = Material(
        diffuse=(0.1, 0.1, 0.1),
        specular=(1.0, 1.0, 1.0),
        shininess=128.0,
        reflectivity=0.85
    )
    scene.add_object(Sphere(center=(-1.2, 1.0, 0.5), radius=1.0, material=mirror_material))

    # Glossy Ruby Red Sphere (Center-Right)
    ruby_material = Material(
        diffuse=(0.85, 0.12, 0.15),
        specular=(1.0, 0.9, 0.9),
        shininess=64.0,
        reflectivity=0.15
    )
    scene.add_object(Sphere(center=(1.2, 1.0, -0.2), radius=1.0, material=ruby_material))

    # Polished Gold Metallic Sphere (Back Center)
    gold_material = Material(
        diffuse=(0.85, 0.65, 0.15),
        specular=(1.0, 0.85, 0.5),
        shininess=96.0,
        reflectivity=0.55
    )
    scene.add_object(Sphere(center=(0.0, 1.5, -2.2), radius=1.5, material=gold_material))

    # Small Emerald Sphere (Front)
    emerald_material = Material(
        diffuse=(0.1, 0.75, 0.35),
        specular=(0.9, 1.0, 0.9),
        shininess=48.0,
        reflectivity=0.3
    )
    scene.add_object(Sphere(center=(0.2, 0.5, 2.0), radius=0.5, material=emerald_material))

    # 3-Point lighting setup (Key, Fill, and Back rim light) for full 360-degree orbit coverage
    scene.add_light(PointLight(position=(-5.0, 8.0, 4.0), color=(1.0, 0.95, 0.85), intensity=1.1))
    scene.add_light(PointLight(position=(5.0, 6.0, 2.0), color=(0.7, 0.85, 1.0), intensity=0.9))
    scene.add_light(PointLight(position=(0.0, 7.0, -5.0), color=(0.85, 0.9, 1.0), intensity=0.6))

    return scene


def create_classic_three_spheres_scene() -> Scene:
    """
    Classic computer graphics lab benchmark scene:
    Three spheres (Red, Green, Blue) over a neutral ground.
    """
    scene = Scene(name="Three Spheres Lab", ambient_light=AmbientLight(intensity=0.18))

    # Matte ground
    ground_mat = Material(diffuse=(0.7, 0.7, 0.7), specular=(0.2, 0.2, 0.2), shininess=16.0, reflectivity=0.1)
    scene.add_object(Plane(point=(0.0, 0.0, 0.0), normal=(0.0, 1.0, 0.0), material=ground_mat))

    # Red diffuse sphere
    scene.add_object(Sphere(center=(-1.6, 1.0, 0.0), radius=1.0, material=Material(
        diffuse=(0.9, 0.1, 0.1), specular=(1.0, 1.0, 1.0), shininess=32.0, reflectivity=0.1
    )))

    # Green reflective sphere
    scene.add_object(Sphere(center=(0.0, 1.0, 0.0), radius=1.0, material=Material(
        diffuse=(0.1, 0.85, 0.2), specular=(1.0, 1.0, 1.0), shininess=64.0, reflectivity=0.45
    )))

    # Blue specular sphere
    scene.add_object(Sphere(center=(1.6, 1.0, 0.0), radius=1.0, material=Material(
        diffuse=(0.15, 0.3, 0.9), specular=(1.0, 1.0, 1.0), shininess=96.0, reflectivity=0.25
    )))

    scene.add_light(PointLight(position=(2.0, 6.0, 4.0), color=(1.0, 1.0, 1.0), intensity=1.1))
    scene.add_light(PointLight(position=(-2.0, 5.0, -4.0), color=(0.8, 0.85, 1.0), intensity=0.6))
    return scene


def create_reflective_infinity_scene() -> Scene:
    """
    Scene demonstrating deep recursive specular reflection with opposing reflective surfaces.
    """
    scene = Scene(name="Recursive Reflections", ambient_light=AmbientLight(intensity=0.12))

    # Mirror floor
    floor_mat = Material(
        diffuse=(0.2, 0.2, 0.25),
        specular=(1.0, 1.0, 1.0),
        shininess=128.0,
        reflectivity=0.75,
        is_checkerboard=True,
        checker_color1=(0.9, 0.9, 0.9),
        checker_color2=(0.1, 0.1, 0.1),
        checker_scale=1.0
    )
    scene.add_object(Plane(point=(0.0, 0.0, 0.0), normal=(0.0, 1.0, 0.0), material=floor_mat))

    # Central silver sphere
    scene.add_object(Sphere(center=(0.0, 1.2, 0.0), radius=1.2, material=Material(
        diffuse=(0.05, 0.05, 0.05), specular=(1.0, 1.0, 1.0), shininess=256.0, reflectivity=0.9
    )))

    # Orbiting colorful spheres
    scene.add_object(Sphere(center=(-2.2, 0.7, 1.0), radius=0.7, material=Material(
        diffuse=(1.0, 0.2, 0.2), specular=(1.0, 1.0, 1.0), shininess=64.0, reflectivity=0.4
    )))
    scene.add_object(Sphere(center=(2.2, 0.7, -1.0), radius=0.7, material=Material(
        diffuse=(0.2, 0.4, 1.0), specular=(1.0, 1.0, 1.0), shininess=64.0, reflectivity=0.4
    )))
    scene.add_object(Sphere(center=(0.0, 0.5, 2.5), radius=0.5, material=Material(
        diffuse=(1.0, 0.8, 0.1), specular=(1.0, 1.0, 1.0), shininess=64.0, reflectivity=0.5
    )))

    scene.add_light(PointLight(position=(0.0, 7.0, 0.0), color=(1.0, 1.0, 1.0), intensity=1.4))
    scene.add_light(PointLight(position=(-4.0, 4.0, 3.0), color=(0.4, 0.6, 1.0), intensity=0.7))
    scene.add_light(PointLight(position=(4.0, 5.0, -3.0), color=(0.9, 0.75, 0.5), intensity=0.6))

    return scene
