## Codex Implementation Plan (PO Breakdown — Design‑Faithful Skeleton)

This plan delivers a **design‑faithful rendering pipeline** that structurally matches the full planetary renderer architecture. All pipeline stages exist, are ordered correctly, and exchange the correct data, but **most passes are skeletal or analytically stubbed**. The outcome proves architectural invariants, pass structure, data flow, and lifetime rules — not visual fidelity.

CODEX must assume **zero prior context** beyond this document.

---

## Non‑Negotiables (Global)

* Python 3.10
* Runtime libs: PyOpenGL, glfw, pyrr, numpy, imgui
* Tests run in **headless Linux CI** (no X11, no GL context)
* No file moves or renames
* No implicit global state

### Architectural Invariants to Enforce in Code

1. **CPU/GPU Space Separation**

    * Absolute/world coordinates exist only on CPU
    * GPU space is always camera‑relative
    * Camera is at or near origin in GPU space

2. **Time Authority**

    * `Application` is the sole source of frame time / delta

3. **Ownership & Lifetime**

    * Window owns GL context
    * Renderer owns FrameGraph
    * Each Pass owns and deletes its GPU resources
    * Shutdown order is reverse of initialization

4. **Explicit Data Flow**

    * Passes never access Application or Window
    * All data arrives via `RenderContext`

5. **Deterministic Pipeline**

    * Pass order is explicit, inspectable, immutable at runtime

---

## Task 1 — Infrastructure, Headless Safety, and CI (Foundation)

### Goal

Enable continuous validation while guaranteeing that architectural code is importable and testable without OpenGL.

### Scope

* Project packaging (`pyproject.toml` or requirements + pytest config)
* Add GitHub Actions workflow running `pytest` on Linux
* Enforce rule: **no GLFW/OpenGL calls at module import time**
* Define explicit headless execution mode for Application/Renderer

### Acceptance

* CI runs on push/PR
* `pytest` passes in a container with no display or GL
* Engine modules import cleanly in tests

---

## Task 2 — Core Runtime Authority (Config, Lifecycle, Application)

### Goal

Implement the non‑visual backbone that governs time, lifetime, and configuration.

### Scope

#### `engine/core/config.py`

* Load `app/configuration.json`
* Provide defaults for required fields:

    * `window.width`, `window.height`, `window.title`, `window.vsync`
* Track file modification time
* API:

    * `get(path, default=None)`
    * `has_changed()`
    * `reload()`

#### `engine/core/lifecycle.py`

* `LifecycleManager`
* Register subsystems with `initialize()` / `shutdown()`
* Enforce strict reverse teardown
* Support full `reinitialize()` with zero resource persistence

#### `engine/core/application.py`

* Sole time authority (`time.perf_counter()`)
* Initialize subsystems in order:

    1. Config
    2. Window
    3. Input
    4. Camera
    5. Renderer
* Explicit main loop
* Headless mode that skips Window + GL work

### Acceptance

* Lifecycle order is testable
* Delta time is deterministic and explicit
* No OpenGL usage

---

## Task 3 — Window and Input Boundaries

### Goal

Introduce platform interaction while keeping test isolation.

### Scope

#### `engine/window/glfw_window.py`

* GLFW init/terminate
* Core profile context creation
* Framebuffer resize callback
* API:

    * `poll_events()`, `swap_buffers()`, `should_close()`

#### `engine/input/input_manager.py`

* Track key states
* Track mouse deltas
* Reset deltas per frame

### Constraints

* Window owns the GL context
* Tests must not instantiate a window

---

## Task 4 — Camera System (Planet‑Scale Correctness)

### Goal

Provide a camera that obeys planetary precision rules.

### Scope

`engine/camera/fly_camera.py`

* CPU‑space position (double precision)
* Quaternion orientation (normalized)
* Controls: WASD, Ctrl/Space, mouse yaw/pitch, Q/E roll
* Outputs:

    * View matrix in camera‑relative GPU space
    * Projection and view‑projection matrices

### Acceptance

* Quaternion remains normalized
* View matrix keeps camera at origin in GPU space
* Fully unit‑testable

---

## Task 5 — Renderer Core and Frame Graph

### Goal

Establish the **exact pipeline structure** described by the planetary renderer design.

### Scope

#### `engine/graphics/frame_graph.py`

* Ordered pass storage
* Methods:

    * `add_pass(pass)`
    * `initialize(render_context)`
    * `execute(delta_time)`
    * `shutdown()`
* Inspection method returning ordered pass names

#### `engine/graphics/renderer.py`

* Own FrameGraph
* Build `RenderContext` per frame containing:

    * framebuffer size
    * camera matrices
    * camera‑relative planet parameters (stub values allowed)
    * time values
* No draw logic

#### `engine/graphics/passes/base_pass.py`

* Enforced interface:

    * `initialize(render_context)`
    * `execute(delta_time)`
    * `shutdown()`

### Acceptance

* Renderer can execute a multi‑pass pipeline deterministically
* Pass order is inspectable in tests

---

## Task 6 — Full Planetary Pipeline Skeleton (All Passes Exist)

### Goal

Create **all passes from the planetary design**, wired in correct order, with minimal or stubbed implementations.

### Required Passes (in this exact order)

0. **Planetary Depth & Geometry Classification Pass**
1. **Atmospheric Entry/Exit Cache Pass**
2. **Cloud Lighting & Shadow Prepass** (compute‑style stub)
3. **Surface G‑Buffer Pass**
4. **Deferred Surface Lighting Pass**
5. **Atmospheric & Volumetric Integration Pass**
6. **Composite & Tone Mapping Pass**

### Implementation Rules

* Each pass:

    * Is its own class under `engine/graphics/passes/`
    * Owns its GPU resources (if any)
    * May use placeholder shaders or even no‑op shaders
    * Receives all inputs via `RenderContext`
* No pass may assume outputs from previous passes via globals
* Buffers/textures may be allocated but filled with constants

### Visual Expectation

* Final output may be a flat color or crude sphere
* Correctness is architectural, not visual

---

## Task 7 — Minimal Geometry Proof (Sphere Integration)

### Goal

Provide a tangible geometric anchor without violating planetary rules.

### Scope

* Implement a **very crude** sphere draw inside the Surface G‑Buffer or a dedicated debug path
* Sphere positions must be camera‑relative
* Shaders may be trivial

---

## Task 8 — Demo Wiring

### Goal

Demonstrate the pipeline end‑to‑end.

### Scope

`app/main.py`

* Thin wiring only
* Instantiate Application
* Run

`app/configuration.json`

* Provide valid defaults

---

## Task 9 — Headless Tests for Architectural Contracts

### Goal

Prove invariants without graphics.

### Required Tests

* Config reload detection
* Lifecycle reverse teardown
* FrameGraph pass ordering
* Camera invariants (normalization, relative view)

### Constraints

* No OpenGL or GLFW usage

---

## Definition of Done

* All planetary pipeline passes exist and execute in order
* Renderer architecture matches design intent
* Camera‑relative math enforced structurally
* Demo runs locally with GL
* Tests pass headlessly in CI
