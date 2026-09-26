# Computer Graphics Project Presentation: Simple Ray Tracer in Python & OpenGL

> **Format**: Slide-by-Slide Presentation Guide  
> **Target Audience**: Computer Graphics Professor, Lab Instructors, and Classmates  
> **Presentation Duration**: ~8–12 Minutes  
> **Tone**: Clear, intuitive, visual, and engaging (no heavy mathematical jargon)

---

## Slide 1: Title & Introduction

### 📌 Slide Content
- **Project Title**: Interactive 3D Ray Tracer in Python & OpenGL
- **Course**: Computer Graphics
- **Presenter**: Yohannes Abebe
- **Key Highlights**:
  - Built from scratch in Python
  - Real-time interactive 3D camera controls
  - Physically-based Blinn-Phong lighting, shadows, and mirror reflections
  - Hardware display using PyOpenGL & GLFW

### 🎙️ Speaker Notes (What to say)
> "Good morning/afternoon everyone. Today, I am excited to present my Computer Graphics project: an interactive 3D Ray Tracer built from the ground up using Python and displayed with OpenGL. 
> 
> Unlike traditional rasterization graphics where triangles are pushed through a GPU pipeline, ray tracing works by simulating the physical path of light. In this project, I developed the core mathematical engine for shooting rays, finding intersections, calculating lighting, casting shadows, and computing mirror reflections—paired with an interactive OpenGL window that lets us orbit around the scene in real time."

---

## Slide 2: How Ray Tracing Works (The Core Concept)

### 📌 Slide Content
- **Rasterization vs. Ray Tracing**:
  - *Rasterization*: "Here is a 3D triangle, where does it land on the screen?"
  - *Ray Tracing*: "For each pixel on screen, what does the camera see into the 3D world?"
- **The Ray-Tracer Loop in 3 Simple Steps**:
  1. **Shoot a Ray**: From the camera eye through each pixel on screen into the 3D world.
  2. **Find Nearest Hit**: Check which object (sphere or plane) the ray hits first.
  3. **Calculate Color**: Determine the color based on lights, shadows, and reflections.

### 🎙️ Speaker Notes
> "To understand how the code works, imagine your computer screen as a glass window looking into a virtual 3D room. 
> 
> For every single pixel on that screen, our camera fires an invisible laser beam—called a ray—out into the 3D world. We test whether that laser hits any sphere or ground plane in front of it. If it hits, we calculate how bright that spot is and what color it should be. If it misses everything, it simply displays the dark background sky."

---

## Slide 3: Project Architecture (Simple Code Structure)

### 📌 Slide Content
```
simple-ray-tracer/
├── raytracer/            <-- The "Brain" (Pure Math & Ray Tracing)
│   ├── ray.py            (Parametric ray with origin & direction)
│   ├── primitives.py     (Sphere and Plane intersection logic)
│   ├── light.py          (Point lights and ambient lighting)
│   ├── material.py       (Colors, shininess, and reflectivity)
│   ├── camera.py         (Pinhole camera with orbit and zoom)
│   ├── engine.py         (Lighting, shadows, and recursive reflections)
│   └── renderer.py       (Multi-sampling anti-aliasing & PNG saving)
│
└── viewer/               <-- The "Eyes" (OpenGL Display Window)
    └── gl_display.py     (GLFW window, OpenGL texture quad, mouse controls)
```

### 🎙️ Speaker Notes
> "The codebase is cleanly separated into two distinct layers:
> 
> 1. **The Ray Tracer Package (`raytracer/`)**: This is the pure mathematical engine. It knows nothing about windows or monitors. It only deals with 3D rays, geometric shapes, light rays, and colors.
> 2. **The Viewport (`viewer/`)**: This uses modern PyOpenGL and GLFW. It takes the array of colors produced by the ray tracer and maps it onto a fullscreen texture quad, letting us smoothly move the camera around with our mouse."

---

## Slide 4: Feature 1 – 3D Shapes & Intersections

### 📌 Slide Content
- **Primitives Supported**:
  - **Spheres**: Perfect curved mathematical geometry without polygonal edges.
  - **Infinite Planes**: Flat ground surfaces with procedural 2D checkerboard textures.
- **How Intersection Works in Code (`primitives.py`)**:
  - We plug the ray's line equation into the shape's formula.
  - For a sphere: We solve a simple quadratic equation. If the discriminant is positive, the ray hits the sphere! We pick the closest hit point.
  - We calculate the **Surface Normal** (the direction sticking straight out of the surface), which is essential for realistic lighting.

### 🎙️ Speaker Notes
> "Our scene supports two classic computer graphics primitives: Spheres and Planes.
> 
> Because we use pure mathematical formulas rather than 3D polygonal meshes with thousands of tiny triangles, our spheres have mathematically perfect curves with zero jagged edges, even when zooming right up to them. In `primitives.py`, when a ray hits a sphere, we calculate the surface normal—which is simply a unit arrow pointing from the center of the sphere out through the hit point."

---

## Slide 5: Feature 2 – Blinn-Phong Illumination Model

### 📌 Slide Content
- **Lighting is broken into 3 components**:
  $$\text{Total Color} = \text{Ambient} + \text{Diffuse} + \text{Specular}$$
- **1. Ambient**:
  - Soft background light so shadowed areas aren't pitch black.
- **2. Diffuse (Lambertian)**:
  - Matte brightness based on the angle between the surface normal and the light.
  - Brightest when facing directly toward the light source.
- **3. Specular (Blinn-Phong)**:
  - The bright, shiny highlight seen on glossy plastic and metal.
  - Uses the **Halfway Vector** between the light direction and the viewer direction.

### 🎙️ Speaker Notes
> "To give 3D objects depth, realism, and material variety, we implemented the industry-standard Blinn-Phong illumination model in `engine.py`.
> 
> It combines three layers:
> First, **Ambient light** provides a base level of illumination so objects in shadow still have visible shape.
> Second, **Diffuse reflection** mimics rough, matte surfaces like chalk or cloth—surfaces facing the light are bright, while surfaces angled away gradually fade.
> Third, **Specular highlights** create the sharp glossy glint you see on polished balls and cars. By tweaking the 'shininess' exponent, we can make surfaces look like soft rubber or high-gloss plastic."

---

## Slide 6: Feature 3 – Hard Shadow Rays

### 📌 Slide Content
- **The Shadow Ray Algorithm (`engine.py`)**:
  1. Once a ray hits a surface at point $P$, we want to know: *Is point $P$ in shadow?*
  2. We shoot a secondary ray from $P$ straight toward each light source.
  3. If another sphere is standing in the way before the light is reached $\rightarrow$ **Blocked!** Diffuse and specular light are set to 0.
  4. If the path is clear $\rightarrow$ **Lit!** Add full light contribution.
- **Shadow Acne Prevention**:
  - We offset the starting point slightly along the surface normal ($+2\times 10^{-3}$) so a sphere doesn't accidentally shadow itself!

### 🎙️ Speaker Notes
> "Shadows are one of the greatest strengths of ray tracing. In rasterization, shadows require complex shadow mapping buffers and filtering. In ray tracing, shadows are completely natural!
> 
> From the hit point, we shoot a 'shadow ray' directly toward the light bulb. If any other object blocks that path, that point is in shadow. In our showcase scene, we have two different colored lights—one warm white and one cool blue—which creates realistic overlapping colored shadows with darker core regions."

---

## Slide 7: Feature 4 – Recursive Specular Reflections

### 📌 Slide Content
- **Mirror Bounces**:
  - Polished materials (like chrome or polished gold) act like mirrors.
  - The ray reflects off the surface according to the law of reflection: $\text{Angle of Incidence} = \text{Angle of Reflection}$.
- **Recursive Ray Tracing**:
  - The reflected ray acts just like a new camera ray!
  - It searches the scene, hits another sphere, and bounces again.
  - Supports configurable bounce depths (up to 6 bounces).
- **Material Blending**:
  $$\text{Final Color} = (1 - \text{Reflectivity}) \times \text{Phong Color} + \text{Reflectivity} \times \text{Reflected Color}$$

### 🎙️ Speaker Notes
> "Next is recursive reflection. When light hits a reflective surface—like our silver chrome sphere—we compute the bounce direction and recursively call our ray tracer again.
> 
> This means our chrome sphere accurately reflects the ruby sphere, the golden sphere, the emerald sphere, the checkerboard floor, and even reflections inside reflections! We can adjust the bounce depth from 1 to 6 bounces in real-time."

---

## Slide 8: Feature 5 – Interactive OpenGL Viewport

### 📌 Slide Content
- **Bridging CPU Ray Tracing with OpenGL**:
  - The CPU computes the pixel colors using vectorized NumPy arrays.
  - The image array is uploaded to the GPU as an OpenGL 2D texture (`glTexImage2D`).
  - A screen-filling quad displays the texture using OpenGL shaders.
- **Dynamic Resolution Scaling (Fluid 30+ FPS)**:
  - **While moving the camera**: Viewport renders at a lightweight interactive preview resolution for instantaneous response.
  - **When the camera stops**: Automatically refines to full crisp resolution with multi-bounce reflections.
- **Camera Controls**:
  - **Left Click + Drag**: Spherical orbit around scene.
  - **Scroll Wheel / W, S**: Smooth zoom in and out.
  - **Right Click + Drag**: Pan camera horizontally and vertically.

### 🎙️ Speaker Notes
> "One common challenge with CPU ray tracers in Python is speed—calculating hundreds of thousands of rays per frame can be demanding. 
> 
> To solve this, we implemented dynamic resolution scaling: while you click and drag your mouse to orbit the camera, the engine renders a fast preview so your movement is smooth and responsive. The moment you release your mouse, it instantly refines into a crisp, high-resolution render. We also implemented intuitive spherical camera orbit controls so anyone can inspect the scene from any angle."

---

## Slide 9: Feature 6 – Scene Presets & Anti-Aliasing (MSAA)

### 📌 Slide Content
- **3 Built-in Benchmark Scenes**:
  1. **Showcase Studio**: Chrome mirror, ruby plastic, gold metal, emerald sphere on a reflective checkerboard with dual lights.
  2. **Three Spheres Lab**: The classic computer graphics benchmark (Diffuse Red, Reflective Green, Specular Blue).
  3. **Recursive Mirrors**: Opposing reflective spheres and floor demonstrating deep multi-bounce reflections.
- **Stochastic Anti-Aliasing (MSAA)**:
  - Firing multiple rays per pixel with subtle sub-pixel offsets removes jagged 'staircase' pixel artifacts on sphere silhouettes.
- **Instant Snapshot Export**:
  - Pressing `S` renders a studio-quality anti-aliased image and saves it to `.png`.

### 🎙️ Speaker Notes
> "We included three different preset scenes that can be switched instantly with keys 1, 2, and 3. This allows instructors to test different graphics properties—from simple diffuse shading to complex multi-bounce mirrors.
> 
> We also added stochastic anti-aliasing: by slightly jittering sub-pixel rays, we eliminate jagged edges along curved sphere borders. Pressing the 'S' key bakes and saves a clean high-resolution image to disk."

---

## Slide 10: Live Demonstration Plan

### 📌 Actions to Demonstrate During Presentation

| Action | Key / Mouse Gesture | What to Point Out to the Audience |
|---|---|---|
| **1. Orbit Scene** | Left-click + Drag | Show how specular highlights and reflections shift smoothly in real-time. |
| **2. Toggle Shadows** | Press `P` | Show the scene with and without shadows to highlight the shadow ray algorithm. |
| **3. Toggle Reflections** | Press `R` | Show chrome and ruby spheres turning matte vs. fully mirror-like. |
| **4. Adjust Bounces** | Press `+` and `-` | Point out the depth of reflections inside the chrome sphere. |
| **5. Switch Scenes** | Press `1`, `2`, `3` | Show the Three Spheres Lab benchmark and the Recursive Mirror scene. |
| **6. Save Image** | Press `S` | Show that an HD anti-aliased PNG was immediately exported to the project folder. |

### 🎙️ Speaker Notes
> "Now, let's switch to the live interactive demonstration. As I drag the mouse, you can see the camera smoothly orbiting our 3D space. Notice how the reflection of the red sphere moves across the surface of the silver sphere. 
> 
> When I press 'P', the shadows turn off, making the scene look flat—and when I press 'P' again, the shadow rays instantly restore physical depth. Pressing '2' switches to the three-sphere benchmark, and pressing 'S' saves our high-res frame to disk."

---

## Slide 11: Summary & Conclusion

### 📌 Slide Content
- **What We Achieved**:
  - Complete, functional ray tracing engine developed in pure Python.
  - Implemented core CG algorithms: Ray Generation, Quadratic Intersections, Blinn-Phong Shading, Shadow Rays, and Recursive Reflections.
  - Real-time interactive hardware display via PyOpenGL and GLFW.
  - Clean, modular, and maintainable object-oriented codebase.
- **Open Source Repository**:
  - [github.com/yohannesabebe/simple-raytracer](https://github.com/yohannesabebe/simple-raytracer)

### 🎙️ Speaker Notes
> "To conclude, this project successfully bridges mathematical ray tracing theory with an interactive OpenGL application. It demonstrates the fundamental principles of physical light simulation—from basic ray-geometry intersections to recursive multi-light illumination—all packaged in an intuitive, accessible codebase.
> 
> The entire project is open-source and available on GitHub. Thank you for your time, and I would be happy to answer any questions!"
