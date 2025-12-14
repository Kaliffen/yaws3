# Revised Engine + Demo Implementation Plan (Integrated)

## Purpose

This plan defines the **complete, authoritative implementation roadmap** for the rendering framework and demo application. It fully incorporates the original plan *and* explicitly encodes all architectural invariants implied by the planetary renderer design. Nothing from the original plan is omitted, removed, or simplified; all additions exist solely to eliminate ambiguity and enforce correctness.

The demo is explicitly a **proof of architectural invariants**, not a feature showcase.

---

## Mandatory Directory Structure (Authoritative)

```
project_root/
│
├─ engine/
│  ├─ core/
│  │  ├─ application.py
│  │  ├─ config.py
│  │  ├─ lifecycle.py
│  │
│  ├─ graphics/
│  │  ├─ renderer.py
│  │  ├─ frame_graph.py
│  │  ├─ passes/
│  │  │  ├─ base_pass.py
│  │  │  ├─ clear_pass.py
│  │  │  └─ sphere_pass.py
│  │
│  ├─ window/
│  │  ├─ glfw_window.py
│  │
│  ├─ input/
│  │  ├─ input_manager.py
│  │
│  ├─ camera/
│  │  ├─ fly_camera.py
│
├─ app/
│  ├─ main.py
│  ├─ configuration.json
│
└─ tests/
   └─ test_config_reload.py
```

No file may be relocated or renamed.

---

## Global Design Invariants (Enforced, Not Optional)

These invariants are derived directly from the planetary renderer design and must be enforced structurally:

0. **TECH STACK**
   * python 3.10, Pyopengl, glfw, pyrr, Imgui, numpy
   
  
1. **CPU/GPU Space Separation**

  * Absolute/world-scale coordinates exist only on the CPU
  * GPU space is always camera-relative
  * Camera is at or near the origin in GPU space

2. **Time Authority**

  * The Application is the single authoritative source of frame time and delta
  * All subsystems receive time explicitly

3. **Ownership and Lifetime**

  * Window owns the OpenGL context
  * Renderer owns the frame graph
  * Each render pass owns and deletes its GPU resources
  * Shutdown order is strictly the reverse of initialization

4. **No Global or Hidden State**

  * No render pass may reach into Application or Window directly
  * All data flows through explicit context objects

5. **Deterministic Pass Execution**

  * Pass order is explicit and inspectable
  * No implicit dependencies between passes

---

## Task 1 – Application Bootstrap (`engine/core/application.py`)

### Purpose

Central authority for lifecycle, timing, and orchestration.

### Responsibilities

* Own the main loop
* Compute `delta_time`
* Initialize subsystems in strict order:

  1. Config
  2. Window
  3. Input
  4. Camera
  5. Renderer
* Propagate shutdown and reinitialization

### Explicit Rules

* No OpenGL calls
* No rendering logic
* Owns the authoritative frame clock

### Outcome

* `Application.run()` starts and stops cleanly
* Logs lifecycle transitions

---

## Task 2 – Configuration System (`engine/core/config.py`)

### Purpose

Load, validate, and monitor runtime configuration.

### Responsibilities

* Load `app/configuration.json`
* Provide defaults
* Track file modification time

### Required Fields

* `window.width`
* `window.height`
* `window.title`
* `window.vsync`

### Outcome

* Config reload detection works without OpenGL

---

## Task 3 – Lifecycle Control (`engine/core/lifecycle.py`)

### Purpose

Formalize subsystem teardown and rebuild.

### Responsibilities

* Define `initialize`, `shutdown`, `reinitialize`
* Enforce reverse-order destruction

### Explicit Rule

* No subsystem may persist resources across reinitialization

---

## Task 4 – GLFW Window Wrapper (`engine/window/glfw_window.py`)

### Purpose

Encapsulate window and OpenGL context creation.

### Responsibilities

* Initialize GLFW
* Create core-profile OpenGL context
* Handle framebuffer resize callbacks

### Explicit Rules

* Owns OpenGL context
* Emits framebuffer size, not window size

---

## Task 5 – Input Manager (`engine/input/input_manager.py`)

### Purpose

Abstract raw input.

### Responsibilities

* Track key states
* Track mouse deltas
* Reset deltas per frame

---

## Task 6 – Fly Camera (`engine/camera/fly_camera.py`)

### Purpose

Camera-relative quaternion fly camera.

### Responsibilities

* Position stored in CPU space
* Orientation as normalized quaternion
* Outputs view matrix assuming camera-relative GPU space

### Controls

* WASD: planar movement
* Ctrl/Space: vertical
* Mouse: yaw/pitch
* Q/E: roll

---

## Task 7 – Renderer Core (`engine/graphics/renderer.py`)

### Purpose

Coordinate render passes.

### Responsibilities

* Own FrameGraph
* Build RenderContext each frame
* Invoke passes in order

### Explicit Rules

* Renderer contains no draw logic
* All GPU state lives in passes

---

## Task 8 – Frame Graph Skeleton (`engine/graphics/frame_graph.py`)

### Purpose

Explicit pass ordering abstraction.

### Responsibilities

* Store ordered passes
* Expose inspection/debug capability

---

## Task 9 – Base Pass Interface (`engine/graphics/passes/base_pass.py`)

### Purpose

Enforce pass contract.

### Required Methods

* `initialize(render_context)`
* `execute(delta_time)`
* `shutdown()`

---

## Task 10 – Clear Pass (`engine/graphics/passes/clear_pass.py`)

### Purpose

Pipeline verification pass.

### Responsibilities

* Clear color and depth
* Enable depth testing

---

## Task 11 – Sphere Pass (`engine/graphics/passes/sphere_pass.py`)

### Purpose

Minimal geometry proof.

### Responsibilities

* Generate sphere mesh
* Compile shaders
* Use camera view-projection matrix

### Explicit Rule

* All positions are camera-relative before GPU upload

---

## Task 12 – Demo Application (`app/main.py`)

### Purpose

Thin wiring layer.

### Rules

* No engine logic
* No rendering logic
* Solely instantiates Application and runs it

---

## Task 13 – Configuration Reload Test (`tests/test_config_reload.py`)

### Purpose

Validate non-visual core logic.

### Responsibilities

* Modify config timestamp
* Assert reload detection

---

## Definition of Done

* Exact directory structure preserved
* Demo runs and renders a sphere
* Camera-relative math enforced
* Lifecycle reload works
* Renderer is pass-based and extensible
* Demo proves architectural invariants, not features
