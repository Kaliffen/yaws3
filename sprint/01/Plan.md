## Task 1 — Project Skeleton, Module Boundaries, and Hello-World Tests

Objective:
Create the baseline project structure and prove that all engine modules can be imported and unit-tested without executing rendering or windowing code.

Scope:

1. Create the exact directory structure:

```
project_root/
├─ engine/
│  ├─ core/
│  ├─ graphics/
│  │  ├─ passes/
│  ├─ window/
│  ├─ input/
│  ├─ camera/
├─ app/
└─ tests/
```

2. Add required `__init__.py` files.
3. Add minimal placeholder implementations (empty classes or methods) for:

  * `engine/core/application.py`
  * `engine/core/config.py`
  * `engine/core/lifecycle.py`
  * `engine/graphics/renderer.py`
  * `engine/graphics/frame_graph.py`
  * `engine/graphics/passes/base_pass.py`
4. Add unit tests under `tests/` that:

  * Import each module
  * Instantiate at least one class per module
  * Assert trivial conditions (object exists, methods callable)

---

## Task 2 — Core Runtime Authority (Config, Lifecycle, Application)

Objective:
Implement configuration loading, lifecycle control, and application time authority.

Scope:

engine/core/config.py

* Load `app/configuration.json`
* Provide defaults for:

  * `window.width`
  * `window.height`
  * `window.title`
  * `window.vsync`
* Track file modification time
* API:

  * `get(path: str, default=None)` using dot-notation
  * `has_changed() -> bool`
  * `reload() -> None`

engine/core/lifecycle.py

* Implement `LifecycleManager` with:

  * `register(subsystem)`
  * `initialize_all()`
  * `shutdown_all()`
* Shutdown order must be reverse of registration order

engine/core/application.py

* Implement `Application` that:

  * Is the sole authority for frame timing (`time.perf_counter()`)
  * Initializes subsystems in this exact order:

    1. Config
    2. Window
    3. Input
    4. Camera
    5. Renderer
  * Runs a main loop computing `delta_time`
  * Shuts down subsystems via `LifecycleManager`
* No OpenGL calls

Tests:

* Config reload detection
* Reverse shutdown order
* Delta time monotonicity

---

## Task 3 — Window and Input Subsystems

Objective:
Introduce GLFW windowing and input handling with strict ownership boundaries.

Scope:

engine/window/glfw_window.py

* Initialize and terminate GLFW
* Create OpenGL core-profile context
* Register framebuffer resize callback
* API:

  * `poll_events()`
  * `swap_buffers()`
  * `should_close()`

engine/input/input_manager.py

* Track key pressed/released state
* Track mouse deltas
* Reset mouse deltas each frame

Constraints:

* Window owns the OpenGL context
* Input manager must not initialize GLFW
* Tests must not create a window

Tests:

* Input state transitions without creating a window

---

## Task 4 — Fly Camera (Planetary Precision Rules)

Objective:
Implement a quaternion-based fly camera enforcing CPU/GPU space separation.

Scope:
engine/camera/fly_camera.py

* Camera position stored in CPU space (double precision)
* Orientation stored as normalized quaternion
* Controls:

  * WASD — planar movement
  * Ctrl/Space — vertical movement
  * Mouse — yaw/pitch
  * Q/E — roll
* Outputs:

  * View matrix assuming camera-relative GPU space
  * Projection and view-projection matrices

Constraints:

* No OpenGL usage
* Use `pyrr`

Tests:

* Quaternion normalization invariant
* View matrix places camera at origin

---

## Task 5 — Renderer Core and Frame Graph

Objective:
Implement renderer orchestration exactly matching the planetary design architecture.

Scope:

engine/graphics/frame_graph.py

* Maintain ordered list of render passes
* API:

  * `add_pass(pass)`
  * `initialize(render_context)`
  * `execute(delta_time)`
  * `shutdown()`
* Provide method to inspect pass order

engine/graphics/renderer.py

* Own a FrameGraph instance
* Build a `RenderContext` per frame containing:

  * framebuffer size
  * camera matrices
  * camera-relative planetary parameters (stub constants allowed)
  * time values
* Execute passes in strict order
* Contain no draw calls

engine/graphics/passes/base_pass.py

* Define interface:

  * `initialize(render_context)`
  * `execute(delta_time)`
  * `shutdown()`

Tests:

* Dummy pass ordering
* Initialize/execute/shutdown call sequencing

---

## Task 6 — Full Planetary Pipeline Skeleton (Design-Faithful Data Flow)

Objective:
Create all planetary rendering pipeline passes with implementations that match the design’s intended *data flow* and responsibilities. Passes may be crude, but must follow the correct computational approach (analytical intersections where required; bounded marching only where required).

Scope:
Create one class per pass under `engine/graphics/passes/`, wired in this exact order:
0. Planetary Depth & Geometry Classification Pass

1. Atmospheric Entry/Exit Cache Pass
2. Cloud Lighting & Shadow Prepass
3. Surface G-Buffer Pass
4. Deferred Surface Lighting Pass
5. Atmospheric & Volumetric Integration Pass
6. Composite & Tone Mapping Pass

Rules (apply to every pass):

* Each pass:

  * Is its own class
  * Owns its GPU resources (may be none)
  * Receives all inputs only via `RenderContext`
  * Deletes all GPU resources in `shutdown()`
* No global state or implicit cross-pass dependencies
* GPU space must be camera-relative

Minimum implementation requirements per pass:

Pass 0 — Planetary Depth & Geometry Classification (Fullscreen)

* Must NOT raymarch empty space.
* Must implement **analytical ray–sphere intersections** in the fragment shader:

  * Ray origin is always `(0,0,0)` in camera-relative space.
  * Ray direction is reconstructed per pixel from `inv_view_proj` and explicitly normalized.
  * Compute intersections for planet sphere and atmosphere shell (inner/outer spheres) using closed-form quadratic.
* Must output minimal per-pixel buffers (choose formats as simple as possible):

  * `depth_planet` (float)
  * `depth_atm_entry` (float)
  * `depth_atm_exit` (float)
  * `geometry_mask` (uint bitmask: at least Atmosphere hit, Terrain hit, Water hit, Space)
* Buffers may be created as textures attached to an FBO.

Pass 1 — Atmospheric Entry/Exit Cache (Fullscreen)

* Must read `depth_atm_entry` / `depth_atm_exit` from Pass 0.
* Must reconstruct camera-relative positions:

  * `atm_start_ws` and `atm_end_ws` in camera-relative space using `inv_view_proj` and depth.
* Output two textures (RGB16F or equivalent): `atm_start_ws`, `atm_end_ws`.

Pass 2 — Cloud Lighting & Shadow Prepass (Compute-style or Fullscreen Stub)

* Must perform **bounded marching** only inside cloud altitude bands (may use a single “mid cloud” band initially).
* Inputs:

  * `atm_start_ws`, `atm_end_ws`
  * `sun_dir_rel` (camera-relative, normalized)
* Implementation can be crude:

  * fixed step count (e.g., 24–48)
  * simple procedural noise (cheap hash/noise in shader) or constant density
  * early exit on opacity
* Outputs (half res optional; full res allowed initially):

  * `cloud_transmittance` (RGBA16F or R16F acceptable)
  * `cloud_scattered_light` (RGBA16F or RGB16F acceptable)
  * `cloud_shadow_mask` (R8 or R16F acceptable)

Pass 3 — Surface G-Buffer (Crude)

* For now, may render nothing and write constant default material values to G-buffer targets, OR draw a trivial proxy surface.
* Must create G-buffer textures consistent with subsequent passes:

  * depth (or reconstructable depth)
  * normal/roughness
  * albedo/metalness
  * material id

Pass 4 — Deferred Surface Lighting (Crude)

* Must read from G-buffer and output `surface_radiance` (RGB16F acceptable).
* Can be minimal:

  * directional light from `sun_dir_rel`
  * simple lambert term

Pass 5 — Atmospheric & Volumetric Integration (Bounded Raymarch)

* Must perform **bounded marching** only between `atm_start_ws` and `atm_end_ws` (from Pass 1).
* Must NOT march outside those bounds.
* Inputs:

  * `atm_start_ws`, `atm_end_ws`
  * `surface_radiance`
  * `cloud_transmittance` and/or `cloud_scattered_light` (may be optional if stubbed)
  * `sun_dir_rel`
* Implementation can be crude:

  * fixed step count (e.g., 32–64)
  * accumulate simple Rayleigh-like scattering with exponential falloff by “height”
  * composite `surface_radiance` at the end

Pass 6 — Composite & Tone Mapping

* Must combine atmosphere result (from Pass 5) and output to default framebuffer.
* Can be minimal tone mapping (e.g., simple exposure + clamp).

Tests:

* Verify all pass classes exist and are registered in correct order.
* Verify renderer/framegraph call sequencing invokes initialize/execute/shutdown for each pass.
* Tests must not call OpenGL.

---

## Task 7 — Ray Construction + Analytical Intersection Utilities (CPU-Testable Contracts)

Objective:
Add CPU-side utilities and validation hooks that mirror the shader-side conventions required by the planetary design: per-pixel ray reconstruction and analytical ray–sphere intersections. This improves correctness and enables unit testing without OpenGL.

Scope:

1. Add a small utility module under `engine/graphics/` (choose one and create it; do not rename existing files):

  * Option A: `engine/graphics/ray_math.py`
  * Option B: `engine/graphics/math_utils.py`

2. Implement the following pure-Python functions (numpy allowed) with clear docstrings:

  * `reconstruct_view_ray(inv_view_proj: np.ndarray, ndc_xy: tuple[float,float]) -> np.ndarray`

    * Returns a normalized camera-relative direction.
    * Ray origin is implicitly (0,0,0) in camera-relative space.
    * Use near and far points in clip/NDC space and transform by `inv_view_proj`.
  * `ray_sphere_intersect(origin: np.ndarray, direction: np.ndarray, center: np.ndarray, radius: float) -> tuple[bool, float, float]`

    * Analytical quadratic solve.
    * Returns (hit, t_near, t_far) with `t_near <= t_far`.
    * Must handle no-hit and negative intersections robustly.

3. Update `engine/graphics/renderer.py` to validate that `RenderContext` provides the fields required by Pass 0 and Pass 1:

  * `inv_view_proj`
  * `sun_dir_rel`
  * `planet_center_rel`
  * `planet_radius`
  * `atm_inner_radius`
  * `atm_outer_radius`
    If missing, raise a clear `ValueError` naming the missing fields.

Constraints:

* These functions must be pure and unit-testable.
* Do not import or call OpenGL/GLFW in this utility module.

Tests:

* Unit tests for `ray_sphere_intersect` on known cases (hit through center, tangent, miss).
* Unit test for `reconstruct_view_ray` shape/normalization (direction length ~1).
* Unit test that renderer context validation raises clear errors when fields are missing.

---

## Task 8 — Demo Application Wiring — Demo Application Wiring Demo Application Wiring — Demo Application Wiring

Objective:
Provide a thin demo entry point.

Scope:
app/main.py

* Instantiate Application
* Call `run()`
* Contain no engine or rendering logic

app/configuration.json

* Provide valid defaults for required fields
