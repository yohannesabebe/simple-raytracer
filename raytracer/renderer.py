"""
High-level rendering manager with multi-sampling (anti-aliasing) and image export.
"""

from typing import Optional
import numpy as np
from PIL import Image

from .camera import Camera
from .scene import Scene
from .engine import RayTracer


class Renderer:
    """
    Manages image rendering passes, anti-aliasing, and disk export.
    """
    def __init__(self, scene: Scene):
        self.scene = scene
        self.engine = RayTracer(scene)

    def render(
        self,
        camera: Camera,
        width: int,
        height: int,
        max_bounces: int = 3,
        enable_shadows: bool = True,
        enable_reflections: bool = True,
        samples_per_pixel: int = 1
    ) -> np.ndarray:
        """
        Renders a full frame at the requested resolution.
        
        Args:
            camera: Pinhole camera setup.
            width: Viewport width.
            height: Viewport height.
            max_bounces: Maximum recursive reflection depth.
            enable_shadows: Enable/disable shadow rays.
            enable_reflections: Enable/disable reflections.
            samples_per_pixel: Anti-aliasing samples per pixel (1 = fast, >1 = supersampling).
            
        Returns:
            RGB uint8 array of shape (height, width, 3) ready for OpenGL texture display.
        """
        camera.set_aspect_ratio(width, height)
        
        if samples_per_pixel <= 1:
            # Single pass (fast interactive mode)
            rays = camera.generate_rays(width, height, jitter=False)
            color_buffer = self.engine.trace_rays(
                rays,
                max_bounces=max_bounces,
                enable_shadows=enable_shadows,
                enable_reflections=enable_reflections
            )
        else:
            # Multi-sample Anti-Aliasing (MSAA / Stochastic Super-Sampling)
            accumulated = np.zeros((height, width, 3), dtype=np.float32)
            for _ in range(samples_per_pixel):
                rays = camera.generate_rays(width, height, jitter=True)
                sample_color = self.engine.trace_rays(
                    rays,
                    max_bounces=max_bounces,
                    enable_shadows=enable_shadows,
                    enable_reflections=enable_reflections
                )
                accumulated += sample_color
            color_buffer = accumulated / float(samples_per_pixel)

        # Convert float [0.0, 1.0] to uint8 [0, 255]
        # In OpenGL coordinates, row 0 is at bottom or top depending on orientation.
        # We prepare in standard top-to-bottom raster order.
        uint8_image = np.ascontiguousarray(
            np.clip(color_buffer * 255.0, 0.0, 255.0).astype(np.uint8)
        )
        return uint8_image

    @staticmethod
    def save_image(filepath: str, rgb_array: np.ndarray):
        """
        Saves RGB uint8 array to image file (e.g. PNG).
        """
        img = Image.fromarray(rgb_array, mode="RGB")
        img.save(filepath)
        print(f"[Renderer] Successfully saved image to '{filepath}'")
