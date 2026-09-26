"""
Main Entry Point for the Python OpenGL Ray Tracer.

Supports both:
  1. Interactive OpenGL GUI window with real-time camera controls:
     python main.py

  2. Command-line offline high-resolution rendering:
     python main.py --render --scene 1 --output showcase.png --width 1280 --height 720 --samples 2
"""

import argparse
import sys
import time

from raytracer.camera import Camera
from raytracer.renderer import Renderer
from raytracer.scene import (
    create_showcase_scene,
    create_classic_three_spheres_scene,
    create_reflective_infinity_scene
)


def run_cli_render(args):
    """
    Headless batch rendering to output file.
    """
    scenes = {
        1: create_showcase_scene,
        2: create_classic_three_spheres_scene,
        3: create_reflective_infinity_scene
    }
    
    scene_factory = scenes.get(args.scene, create_showcase_scene)
    scene = scene_factory()
    print(f"[CLI Render] Loaded Scene: '{scene.name}'")
    
    camera = Camera(
        eye=(0.0, 2.5, 6.0),
        target=(0.0, 0.8, 0.0),
        up=(0.0, 1.0, 0.0),
        fov_degrees=50.0,
        aspect_ratio=args.width / args.height
    )
    
    renderer = Renderer(scene)
    
    print(f"[CLI Render] Rendering {args.width}x{args.height} image with {args.samples} sample(s)/px, {args.bounces} bounces...")
    t0 = time.perf_counter()
    image = renderer.render(
        camera=camera,
        width=args.width,
        height=args.height,
        max_bounces=args.bounces,
        enable_shadows=not args.no_shadows,
        enable_reflections=not args.no_reflections,
        samples_per_pixel=args.samples
    )
    elapsed = time.perf_counter() - t0
    print(f"[CLI Render] Render completed in {elapsed:.2f} seconds!")
    
    Renderer.save_image(args.output, image)
    print(f"[CLI Render] Result saved to: {args.output}")


def run_interactive_viewer(args):
    """
    Launches GLFW + OpenGL interactive GUI.
    """
    from viewer.gl_display import GLViewer
    viewer = GLViewer(window_width=args.width, window_height=args.height)
    viewer.run()


def main():
    parser = argparse.ArgumentParser(
        description="Python OpenGL Ray Tracer - Computer Graphics Project",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--render", action="store_true",
        help="Run headless offline render and save image instead of opening GUI window"
    )
    parser.add_argument(
        "--scene", type=int, default=1, choices=[1, 2, 3],
        help="Preset scene number (1: Showcase Studio, 2: Three Spheres, 3: Reflective Mirrors)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="render_output.png",
        help="Output image filename for offline render"
    )
    parser.add_argument(
        "--width", "-W", type=int, default=800,
        help="Viewport / image width in pixels"
    )
    parser.add_argument(
        "--height", "-H", type=int, default=600,
        help="Viewport / image height in pixels"
    )
    parser.add_argument(
        "--bounces", type=int, default=3,
        help="Maximum recursive reflection bounces"
    )
    parser.add_argument(
        "--samples", type=int, default=2,
        help="Anti-aliasing samples per pixel for offline render"
    )
    parser.add_argument(
        "--no-shadows", action="store_true",
        help="Disable shadow ray calculation"
    )
    parser.add_argument(
        "--no-reflections", action="store_true",
        help="Disable specular recursive reflections"
    )
    
    args = parser.parse_args()
    
    if args.render:
        run_cli_render(args)
    else:
        run_interactive_viewer(args)


if __name__ == "__main__":
    main()
