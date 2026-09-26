"""
Interactive OpenGL + GLFW display window for CPU ray tracer.
Renders ray-traced pixels into an OpenGL texture mapped onto a screen-filling quad,
supporting mouse orbit, zoom, pan, real-time preview, and high-res image export.
"""

import sys
import time
import os
from datetime import datetime
import numpy as np
import glfw
from OpenGL.GL import *

from raytracer.camera import Camera
from raytracer.scene import (
    create_showcase_scene,
    create_classic_three_spheres_scene,
    create_reflective_infinity_scene
)
from raytracer.renderer import Renderer


class GLViewer:
    """
    OpenGL-based viewport window displaying the ray-traced scene in real-time.
    """
    def __init__(self, window_width: int = 800, window_height: int = 600, title: str = "Python OpenGL Ray Tracer"):
        self.window_width = window_width
        self.window_height = window_height
        self.title = title
        
        # Scenes list
        self.scenes = [
            create_showcase_scene(),
            create_classic_three_spheres_scene(),
            create_reflective_infinity_scene()
        ]
        self.current_scene_idx = 0
        self.scene = self.scenes[self.current_scene_idx]
        self.renderer = Renderer(self.scene)
        
        # Camera
        self.camera = Camera(
            eye=(0.0, 2.5, 6.0),
            target=(0.0, 0.8, 0.0),
            up=(0.0, 1.0, 0.0),
            fov_degrees=50.0,
            aspect_ratio=window_width / window_height
        )
        
        # Render resolution settings
        self.preview_scale = 0.25  # Lower resolution while dragging for fast interactive FPS
        self.full_width = window_width
        self.full_height = window_height
        self.preview_width = max(80, int(window_width * self.preview_scale))
        self.preview_height = max(60, int(window_height * self.preview_scale))
        
        # Ray tracing parameters
        self.max_bounces = 3
        self.enable_shadows = True
        self.enable_reflections = True
        
        # State tracking
        self.is_interacting = False
        self.needs_render = True
        self.last_mouse_x = 0.0
        self.last_mouse_y = 0.0
        self.mouse_left_down = False
        self.mouse_right_down = False
        
        # Performance metrics
        self.last_frame_time = time.perf_counter()
        self.render_duration_ms = 0.0

    def init_gl(self):
        """
        Initializes GLFW window, OpenGL context, textures, and quad geometry.
        """
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
            
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
        self.window = glfw.create_window(self.window_width, self.window_height, self.title, None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
            
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)  # VSync
        
        # Register input callbacks
        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_key_callback(self.window, self._key_callback)
        glfw.set_framebuffer_size_callback(self.window, self._resize_callback)
        
        # Create OpenGL texture for ray tracer display
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Setup modern quad shaders
        vertex_shader_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        out vec2 TexCoord;
        void main() {
            gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        fragment_shader_source = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D screenTexture;
        void main() {
            FragColor = texture(screenTexture, TexCoord);
        }
        """
        
        self.shader_program = self._compile_shaders(vertex_shader_source, fragment_shader_source)
        
        # Fullscreen quad vertices: (x, y, u, v)
        # Inverted V coordinate to align standard top-to-bottom raster with OpenGL UV space
        quad_vertices = np.array([
            -1.0,  1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 1.0,
             1.0,  1.0, 1.0, 0.0
        ], dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
        
        # Position attribute
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        # Texture coord attribute
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def _compile_shaders(self, vertex_src: str, fragment_src: str) -> int:
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vertex_src)
        glCompileShader(vs)
        if not glGetShaderiv(vs, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(vs).decode())
            
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fragment_src)
        glCompileShader(fs)
        if not glGetShaderiv(fs, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(fs).decode())
            
        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(program).decode())
            
        glDeleteShader(vs)
        glDeleteShader(fs)
        return program

    def _cursor_pos_callback(self, window, xpos, ypos):
        dx = xpos - self.last_mouse_x
        dy = ypos - self.last_mouse_y
        self.last_mouse_x = xpos
        self.last_mouse_y = ypos
        
        if self.mouse_left_down:
            # Orbit camera
            sensitivity = 0.005
            self.camera.orbit(delta_yaw=dx * sensitivity, delta_pitch=-dy * sensitivity)
            self.is_interacting = True
            self.needs_render = True
            
        elif self.mouse_right_down:
            # Pan camera
            pan_sensitivity = 0.005 * (self.camera.radius * 0.3)
            self.camera.pan(delta_x=dx * pan_sensitivity, delta_y=dy * pan_sensitivity)
            self.is_interacting = True
            self.needs_render = True

    def _mouse_button_callback(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.mouse_left_down = True
                self.is_interacting = True
            elif action == glfw.RELEASE:
                self.mouse_left_down = False
                self.is_interacting = False
                self.needs_render = True
                
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                self.mouse_right_down = True
                self.is_interacting = True
            elif action == glfw.RELEASE:
                self.mouse_right_down = False
                self.is_interacting = False
                self.needs_render = True

    def _scroll_callback(self, window, xoffset, yoffset):
        zoom_speed = 0.4
        self.camera.zoom(-yoffset * zoom_speed)
        self.needs_render = True

    def _key_callback(self, window, key, scancode, action, mods):
        if action != glfw.PRESS and action != glfw.REPEAT:
            return
            
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
            
        elif key == glfw.KEY_1:
            self._switch_scene(0)
        elif key == glfw.KEY_2:
            self._switch_scene(1)
        elif key == glfw.KEY_3:
            self._switch_scene(2)
            
        elif key == glfw.KEY_S:
            self.export_current_frame()
            
        elif key == glfw.KEY_P:
            self.enable_shadows = not self.enable_shadows
            print(f"[Controls] Shadows: {'ON' if self.enable_shadows else 'OFF'}")
            self.needs_render = True
            
        elif key == glfw.KEY_R:
            self.enable_reflections = not self.enable_reflections
            print(f"[Controls] Reflections: {'ON' if self.enable_reflections else 'OFF'}")
            self.needs_render = True
            
        elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            self.max_bounces = min(self.max_bounces + 1, 6)
            print(f"[Controls] Max Reflection Bounces: {self.max_bounces}")
            self.needs_render = True
            
        elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            self.max_bounces = max(self.max_bounces - 1, 0)
            print(f"[Controls] Max Reflection Bounces: {self.max_bounces}")
            self.needs_render = True
            
        elif key == glfw.KEY_SPACE:
            print("[Controls] Rendering High-Quality Anti-Aliased Frame (2x MSAA)...")
            self._render_high_quality()
            
        # Keyboard movement (WASD)
        elif key == glfw.KEY_W:
            self.camera.zoom(-0.5)
            self.needs_render = True
        elif key == glfw.KEY_S and (mods & glfw.MOD_CONTROL == 0):
            # Normal S without Ctrl zooms backward
            self.camera.zoom(0.5)
            self.needs_render = True
        elif key == glfw.KEY_A:
            self.camera.orbit(-0.08, 0.0)
            self.needs_render = True
        elif key == glfw.KEY_D:
            self.camera.orbit(0.08, 0.0)
            self.needs_render = True

    def _resize_callback(self, window, width, height):
        if width > 0 and height > 0:
            self.window_width = width
            self.window_height = height
            self.full_width = width
            self.full_height = height
            self.preview_width = max(80, int(width * self.preview_scale))
            self.preview_height = max(60, int(height * self.preview_scale))
            glViewport(0, 0, width, height)
            self.camera.set_aspect_ratio(width, height)
            self.needs_render = True

    def _switch_scene(self, idx: int):
        self.current_scene_idx = idx % len(self.scenes)
        self.scene = self.scenes[self.current_scene_idx]
        self.renderer = Renderer(self.scene)
        print(f"[Scene] Switched to Scene {idx + 1}: '{self.scene.name}'")
        self.needs_render = True

    def export_current_frame(self, filepath: str = None):
        """
        Renders a clean high-resolution anti-aliased frame and saves it as a PNG file.
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"render_{self.scene.name.lower().replace(' ', '_')}_{timestamp}.png"
            
        print(f"[Export] Baking HD render (800x600, anti-aliased) to '{filepath}'...")
        export_img = self.renderer.render(
            self.camera,
            width=800,
            height=600,
            max_bounces=self.max_bounces,
            enable_shadows=self.enable_shadows,
            enable_reflections=self.enable_reflections,
            samples_per_pixel=2
        )
        Renderer.save_image(filepath, export_img)
        print(f"[Export] Done! Saved render to {os.path.abspath(filepath)}")

    def _render_high_quality(self):
        """
        Forces a 2x anti-aliased render to current viewport.
        """
        t0 = time.perf_counter()
        img = self.renderer.render(
            self.camera,
            width=self.full_width,
            height=self.full_height,
            max_bounces=self.max_bounces,
            enable_shadows=self.enable_shadows,
            enable_reflections=self.enable_reflections,
            samples_per_pixel=2
        )
        self.render_duration_ms = (time.perf_counter() - t0) * 1000.0
        self._upload_texture(img, self.full_width, self.full_height)
        self.needs_render = False

    def _upload_texture(self, img_data: np.ndarray, width: int, height: int):
        """
        Uploads uint8 RGB numpy array into OpenGL texture.
        """
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data
        )

    def run(self):
        """
        Main application render loop.
        """
        self.init_gl()
        
        self.print_controls_banner()
        
        # Initial render
        self.needs_render = True
        
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            
            if self.needs_render:
                t0 = time.perf_counter()
                
                # If currently dragging camera, render at preview resolution for high responsiveness
                if self.is_interacting:
                    render_w = self.preview_width
                    render_h = self.preview_height
                    # Fast 1-bounce for preview during movement
                    preview_bounces = min(self.max_bounces, 1)
                    img = self.renderer.render(
                        self.camera,
                        width=render_w,
                        height=render_h,
                        max_bounces=preview_bounces,
                        enable_shadows=self.enable_shadows,
                        enable_reflections=self.enable_reflections,
                        samples_per_pixel=1
                    )
                else:
                    render_w = self.full_width
                    render_h = self.full_height
                    img = self.renderer.render(
                        self.camera,
                        width=render_w,
                        height=render_h,
                        max_bounces=self.max_bounces,
                        enable_shadows=self.enable_shadows,
                        enable_reflections=self.enable_reflections,
                        samples_per_pixel=1
                    )
                    self.needs_render = False
                    
                self.render_duration_ms = (time.perf_counter() - t0) * 1000.0
                self._upload_texture(img, render_w, render_h)
                
                # Update window title with live diagnostic metrics
                fps = 1000.0 / max(self.render_duration_ms, 0.1)
                status_title = (
                    f"Ray Tracer | {self.scene.name} | Res: {render_w}x{render_h} | "
                    f"Time: {self.render_duration_ms:.1f}ms ({fps:.1f} FPS) | "
                    f"Bounces: {self.max_bounces} | Shadows: {'ON' if self.enable_shadows else 'OFF'}"
                )
                glfw.set_window_title(self.window, status_title)

            # Draw screen quad with OpenGL texture
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader_program)
            glBindVertexArray(self.vao)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            
            glfw.swap_buffers(self.window)
            
        glfw.destroy_window(self.window)
        glfw.terminate()

    @staticmethod
    def print_controls_banner():
        banner = """
========================================================================
             PYTHON OPENGL RAY TRACER - INTERACTIVE VIEWER
========================================================================
 CONTROLS:
   - Left Click + Drag     : Orbit Camera (Pitch / Yaw)
   - Right Click + Drag    : Pan Camera
   - Scroll Wheel / W, S   : Zoom In / Out
   - Keys A, D             : Rotate Camera
   - Key 1, 2, 3           : Switch Scenes (1: Showcase, 2: Three Spheres, 3: Mirrors)
   - Key S                 : Save / Export HD Screenshot (.PNG)
   - Key P                 : Toggle Shadows ON / OFF
   - Key R                 : Toggle Reflections ON / OFF
   - Key '+' / '-'         : Increase / Decrease Reflection Bounces
   - Spacebar              : Force High-Quality Anti-Aliased Render (MSAA)
   - ESC                   : Exit Application
========================================================================
"""
        print(banner)
