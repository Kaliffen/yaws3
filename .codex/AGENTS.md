Non-Negotiables (Global)

Python 3.10

Runtime libs: PyOpenGL, glfw, pyrr, numpy, imgui

Tests run in headless Linux CI (no X11, no GL context)

No file moves or renames

No implicit global state

Architectural Invariants to Enforce in Code

CPU/GPU Space Separation

Absolute/world coordinates exist only on CPU

GPU space is always camera-relative

Camera is at or near origin in GPU space

Time Authority

Application is the sole source of frame time / delta

Ownership & Lifetime

Window owns GL context

Renderer owns FrameGraph

Each Pass owns and deletes its GPU resources

Shutdown order is reverse of initialization

Explicit Data Flow

Passes never access Application or Window

All data arrives via RenderContext

Deterministic Pipeline

Pass order is explicit, inspectable, immutable at runtime