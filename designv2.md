# Planetary Renderer Design Document (Revised, Full)

## 1. Purpose and Scope

This document specifies a **real‑time, world‑scale planetary rendering architecture** built on modern OpenGL. The system is designed for:

* Planet radii on the order of 10^6–10^7 meters
* Camera transitions from orbit to ground level
* Physically grounded atmosphere, clouds, terrain, and water
* Real‑time performance via aggressive analytical bounds, SDF usage, and multipass specialization

The intent is to provide sufficient detail for direct implementation by an experienced graphics programmer.

---

## 2. High‑Level Architectural Goals

1. Avoid brute‑force ray marching across empty space
2. Exploit known planetary structure (spherical shells, altitude bands)
3. Separate geometry, lighting, and volumetric integration into specialized passes
4. Preserve numerical stability at extreme scales
5. Approximate global illumination using domain‑specific energy transfer, not general path tracing

---

## 2.1 Rendering Responsibility Boundaries (Clarification)

This renderer is intentionally **bounded and layered**. Responsibilities are explicitly divided to ensure stability, predictable performance, and compatibility with a deferred shading pipeline.

* **Analytical SDFs** define global structure, ray limits, and classification (planet/atmosphere shells, horizon tests, terminator tests).
* **Rasterized meshes** provide all **primary surface visibility** (terrain and water) and stable derivatives.
* **Ray marching** is reserved for **bounded volumetric integration** (atmosphere and clouds) between analytically computed entry/exit points.
* **Deferred lighting** computes surface illumination and GI approximations after G‑buffer capture.

No primary surface visibility is resolved via unbounded iterative ray marching.

---

## 3. Coordinate Space Strategy (Precision Foundation)

This section defines all coordinate spaces used by the renderer, the **origin rebasing cadence**, and the cross-frame invariants required to guarantee temporal stability during long orbital flights and high-velocity camera motion.

### 3.1 Planet Space (CPU Only, Double Precision)

Used exclusively on the CPU:

* Planet center
* Camera position
* Orbital mechanics

```cpp
dvec3 planetCenter;
dvec3 cameraPosPlanet;
```

This space is never sent directly to the GPU.

---

### 3.2 Camera‑Relative World Space (GPU Primary Space)

All GPU calculations occur in camera‑relative space:

```
worldPos_gpu = worldPos_planet - cameraPos_planet
```

Properties:

* Camera remains near the origin
* All values fit safely in FP32
* Stable normals, derivatives, and depth

All G‑buffer positions and ray math use this space.

---

### 3.3 Optional Local Surface Space

When near the surface, terrain and water may be rendered in a **local tangent frame** to improve:

* Normal mapping precision
* Displacement stability
* Specular highlights

The local frame is defined by the planet normal at the camera anchor point. All local-space results are transformed back into camera-relative world space before writing to the G-buffer.

---

### 3.4 Origin Rebasing and Temporal Invariants

To maintain numerical stability during long-distance travel, **origin rebasing** is performed on the CPU:

* The camera-relative origin is shifted when the camera exceeds a configurable threshold (e.g., 1–5 km)
* Planet center, sun direction, and all world anchors are updated atomically
* No GPU state persists absolute world positions across frames

**Invariants:**

* The camera is always near the origin in GPU space
* Ray origins are always `(0,0,0)` in camera-relative space
* All directions are normalized after rebasing

When near the surface, terrain and water may be rendered in a **local tangent frame** to improve:

* Normal mapping precision
* Displacement stability
* Specular highlights

---

## 4. Scene Representation

### 4.1 Signed Distance Fields (Analytical)

**Planet SDF**

* Sphere (default) or oblate ellipsoid (optional)
* Used for ray–planet intersection, horizon tests, and terminator calculations

**Ellipsoid Handling Notes:**

* An oblate spheroid is defined by equatorial and polar radii
* All distance and intersection tests are performed in scaled space to reduce the ellipsoid to a unit sphere
* Normals are reconstructed in unscaled space to preserve correct lighting

**Atmosphere SDF**

* Spherical or ellipsoidal shell
* Inner surface matches the planet shape exactly
* Outer surface uses the same axis scaling to preserve constant-altitude layers

**Invariant:**

* Atmospheric shells must follow the same geometric model (sphere or ellipsoid) as the planet surface

These SDFs are evaluated analytically, never via iterative stepping.

**Planet SDF**

* Perfect sphere or ellipsoid
* Used for ray–planet intersection, horizon tests

**Atmosphere SDF**

* Spherical shell
* Inner radius = planet radius
* Outer radius = top of atmosphere

These SDFs are evaluated analytically, never via iterative stepping.

---

### 4.2 Terrain

* Rendered as meshes (VBOs)
* Camera‑relative positions
* Height‑mapped or procedurally displaced

---

### 4.3 Water Surface

* Analytical ocean sphere or mesh
* Displacement in local space only
* No volumetric marching unless underwater

---

### 4.4 Clouds

* Procedural volumetric density fields
* Defined in altitude bands:

  * Low (stratus)
  * Mid (cumulus)
  * High (cirrus)

Clouds are never treated as a continuous global volume.

---

## 5. Analytical-First Rule (Explicit)

**Any ray segment whose entry and exit points can be computed analytically must never be raymarched.**

This applies to:

* Planet intersection and horizon tests
* Atmosphere entry/exit bounds
* Ocean intersection (if analytical)
* Day/night terminator tests (sun–planet intersection)
* Sun occlusion by the planet

Ray marching is reserved for bounded volumetric integration (atmosphere and clouds) between analytical limits.

---

## 6. Frame Graph Overview

```
Frame
 ├─ Pass 0: Planetary Depth & Geometry Classification
 ├─ Pass 1: Atmospheric Entry/Exit Cache
 ├─ Pass 2: Cloud Lighting & Shadow Prepass
 ├─ Pass 3: Surface G‑Buffer (Terrain + Water)
 ├─ Pass 4: Deferred Surface Lighting
 ├─ Pass 5: Atmospheric & Volumetric Integration
 ├─ Pass 6: Temporal Resolve, Composite & Tone Mapping
```

Each pass is purpose‑built and minimizes redundant computation.

---

## 6. Pass 0 – Planetary Depth & Geometry Classification

**Ray Parameterization:**

* Ray origin is always `(0,0,0)` in camera-relative space
* Ray direction is reconstructed per pixel from the inverse view-projection matrix and explicitly normalized
* Ray parameter `t` is measured in camera-relative world units

These conventions are mandatory for all analytical ray–sphere intersection tests in this pass and are relied upon by subsequent passes.

**Type:** Fullscreen fragment pass

**Purpose:**

* Determine which planetary domains each pixel intersects
* Compute analytical ray–sphere intersections

**Outputs (MRT):**

* `depth_planet`
* `depth_atmosphere_entry`
* `depth_atmosphere_exit`
* `geometry_mask`

**Geometry Mask Bits:**

* 0: Atmosphere hit
* 1: Terrain hit
* 2: Water hit
* 3: Space

No ray marching occurs in this pass.

---

## 7. Pass 1 – Atmospheric Entry/Exit Cache

**Purpose:**

* Cache per‑pixel atmosphere traversal bounds

**Inputs:**

* Outputs from Pass 0

**Outputs:**

* `atm_start_ws`
* `atm_end_ws`
* Optional coarse optical depth

Stored in FP16 where possible to reduce bandwidth.

---

## 8. Pass 2 – Cloud Lighting & Shadow Prepass

**Type:** Compute shader (½ or ¼ resolution)

**Purpose:**

* Resolve cloud lighting and shadowing once per frame

**Inputs:**

* Atmosphere bounds
* Sun direction
* Cloud noise textures
* Altitude band definitions

**Physical Model:**

* Single-scattering approximation
* Henyey–Greenstein phase function with fixed anisotropy `g` per cloud type

  * Low clouds: weak forward scattering
  * Mid clouds: moderate forward scattering
  * High clouds: strong forward scattering

**Outputs:**

* `cloud_transmittance`
* `cloud_scattered_light`
* `cloud_shadow_mask`

**Key Rules:**

* March only inside cloud altitude bands
* Fixed step count per band
* Early exit on opacity

**Type:** Compute shader (½ or ¼ resolution)

**Purpose:**

* Resolve cloud lighting and shadowing once per frame

**Inputs:**

* Atmosphere bounds
* Sun direction
* Cloud noise textures
* Altitude band definitions

**Outputs:**

* `cloud_transmittance`
* `cloud_scattered_light`
* `cloud_shadow_mask`

**Key Rules:**

* March only inside cloud altitude bands
* Fixed step count per band
* Early exit on opacity

---

## 9. Pass 3 – Surface G‑Buffer

**Purpose:**

* Capture surface geometry and material data

**Rendered Objects:**

* Terrain
* Water

**G‑Buffer Layout:**

* RT0: Depth or reconstructable position
* RT1: Normal (octahedral) + roughness
* RT2: Albedo + metalness
* RT3: Material ID

Atmospheric effects are excluded entirely from this pass.

---

## 10. Pass 4 – Deferred Surface Lighting

**Purpose:**

* Compute direct and approximated indirect lighting for surfaces

**Lighting Components:**

* Direct sunlight
* Sky irradiance (from LUTs)
* Single‑bounce ground GI approximation

**Water:**

* Fresnel‑weighted sun reflection
* Sky reflection
* No diffuse GI

**Output:**

* `surface_radiance`

### 10.1 Micro‑Scale Terrain Shading (Mandatory)

At 1–10 meter scale, finite mesh resolution and heightfield displacement can produce perceptually flat surfaces unless high-frequency shading cues are introduced. The following are mandatory components of the surface lighting model (pure shading; no additional geometry):

* **Procedural micro-normal synthesis**

  * Slope-dependent noise
  * Curvature-aware blending
  * Independent of mesh resolution

* **Analytical cavity / bent-normal approximation**

  * Derived from height derivatives and/or procedural noise
  * Applied to ambient terms to simulate micro-occlusion

* **View-dependent horizon occlusion**

  * Cheap cone test / horizon term in tangent space and/or screen space
  * Stabilized temporally (see Pass 6)

These terms exist to preserve ground-scale detail perception without requiring extreme tessellation.

---

## 11. Pass 5 – Atmospheric & Volumetric Integration

**Purpose:**

* Integrate atmospheric scattering and compositing

**Inputs:**

* Atmosphere bounds
* Surface radiance
* Cloud buffers
* Atmospheric LUTs:

  * Transmittance
  * Multiple scattering
  * Phase functions

**Shadowing and Terminator Handling:**

* Terrain shadowing of the atmosphere (day/night terminator) is handled analytically via sun–planet intersection tests per pixel
* No shadow maps are sampled inside the atmosphere pass

**Process:**

1. March view ray only between cached bounds
2. Accumulate Rayleigh and Mie scattering
3. Apply multiple scattering LUT
4. Modulate by cloud transmittance
5. Composite surface contribution
6. Inject upward ground bounce energy

**Step size:** altitude-dependent, fixed max count

**Purpose:**

* Integrate atmospheric scattering and compositing

**Inputs:**

* Atmosphere bounds
* Surface radiance
* Cloud buffers
* Atmospheric LUTs:

  * Transmittance
  * Multiple scattering
  * Phase functions

**Process:**

1. March view ray only between cached bounds
2. Accumulate Rayleigh + Mie
3. Apply multiple scattering LUT
4. Modulate by cloud transmittance
5. Composite surface contribution
6. Inject upward ground bounce energy

**Step size:** altitude‑dependent, fixed max count

---

## 12. Pass 6 – Temporal Resolve, Composite & Tone Mapping

**Purpose:**

* Temporal stabilization and accumulation (mandatory)
* Final HDR composition
* Exposure and tone mapping

### 12.1 Temporal Accumulation (Mandatory)

Given screen-space constraints (GI, AO, horizon terms) and bounded volumetric marching, temporal accumulation is required for stability during camera motion and at grazing angles.

**History Buffers (recommended per-domain):**

* Surface radiance
* Indirect lighting (GI term)
* AO / cavity term
* Atmospheric scattering contribution
* Cloud transmittance / cloud scattering

**Reprojection:**

* Reproject using previous view-projection and current depth
* Use geometry mask to prevent cross-domain contamination (space/atmosphere/surface)

**Rejection / Clamping:**

* Reject history on large depth deltas
* Reject history on large normal deltas
* Reject history if geometry mask changes
* Clamp radiance deltas to reduce flicker

**Confidence-weighted blending:**

* Blend history and current values based on stability metrics
* Reduce history weight near silhouettes and disocclusions

---

## 13. Global Illumination Strategy

True path tracing is avoided.

Instead:

* A fraction of surface radiance is injected upward as diffuse hemispherical irradiance
* Injection strength is proportional to surface albedo and cosine-weighted normal
* Energy decays exponentially with altitude

Water contributes only specular energy via Fresnel reflection.

Multiple scattering is handled via LUTs, ensuring global energy consistency without stochastic noise.

True path tracing is avoided.

Instead:

* Ground albedo feeds upward irradiance into atmosphere
* Water reflects sun and sky analytically
* Multiple scattering handled via LUTs

This preserves energy consistency without stochastic noise.

### 13.1 Screen-Space GI Constraints (Explicit)

The GI approximation is intentionally:

* View-dependent
* Single-bounce
* Screen-space constrained

**Containment rules (mandatory):**

* Clamp indirect intensity
* Fade GI near silhouettes and in high-uncertainty regions
* Bias toward sky irradiance under uncertainty (avoid light leaks)

---

## 14. Precision Strategies (Mandatory)

1. Camera-relative coordinates everywhere on GPU

2. Double precision only on CPU

3. No `length()` on large vectors

4. Ray–sphere intersections in camera-relative space

5. Height computed via squared-distance formulation

6. Accumulate optical depth, not transmittance

7. Reversed-Z floating-point depth buffer

8. Aggressive clamping of dot products and exponentials

9. Avoid `acos`, `asin`, and `atan`; use dot-product–based formulations

10. Camera‑relative coordinates everywhere on GPU

11. Double precision only on CPU

12. No `length()` on large vectors

13. Ray–sphere intersections in camera‑relative space

14. Height computed via squared‑distance formulation

15. Accumulate optical depth, not transmittance

16. Reversed‑Z floating‑point depth buffer

17. Aggressive clamping of dot products and exponentials

---

## 15. Non‑Goals

* General path tracing
* Arbitrary volumetric GI
* Global SDF ray marching

These are intentionally excluded for performance and stability reasons.

---

## 16. Implementation Notes

* All sun directions are camera‑relative and normalized
* LUT domains are fixed and clamped
* Origin rebasing occurs on CPU only
* No per‑pixel sun marching inside atmosphere pass

---

## 17. Conclusion

This design treats planetary rendering as a **bounded, layered light transport problem**, not a generic ray‑marching problem. By combining analytical SDF intersections, multipass specialization, mandatory temporal stabilization, micro-scale surface shading, and precision‑aware math, the system achieves real‑time performance with physically plausible results across planetary scales.

This document defines a complete and implementable solution.

---

# Appendix A – Shader-by-Shader Breakdown (GLSL Pseudocode)

**Global Shader Assumptions:**

* All view rays originate at the camera-relative origin `(0,0,0)`
* All ray directions are reconstructed from the inverse projection matrix and explicitly normalized
* Camera-relative space is used consistently across all passes

These assumptions are relied upon implicitly in all shader pseudocode below and are required for numerical stability at planetary scale.

## A1. Pass 0 – Planetary Depth & Geometry Classification

**Assumptions:**

* Ray origin is `(0,0,0)` in camera-relative space
* Ray direction is reconstructed from inverse projection and normalized

**Vertex Shader (fullscreen triangle)**

**Vertex Shader (fullscreen triangle)**

```glsl
#version 450
const vec2 verts[3] = vec2[3](
    vec2(-1.0, -1.0),
    vec2( 3.0, -1.0),
    vec2(-1.0,  3.0)
);
void main() {
    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
}
```

**Fragment Shader**

```glsl
#version 450
layout(location = 0) out float depthPlanet;
layout(location = 1) out float depthAtmEntry;
layout(location = 2) out float depthAtmExit;
layout(location = 3) out uint  geometryMask;

uniform vec3 cameraPosRel;
uniform vec3 rayDir;
uniform float planetRadius;
uniform float atmInnerRadius;
uniform float atmOuterRadius;

void main() {
    // Ray–sphere intersection in camera-relative space
    // Solve analytically, write depths and mask bits
}
```

---

## A2. Pass 1 – Atmospheric Entry/Exit Cache

**Fragment Shader**

```glsl
#version 450
layout(location = 0) out vec3 atmStart;
layout(location = 1) out vec3 atmEnd;

uniform sampler2D depthBuffers;
uniform mat4 invViewProj;

void main() {
    // Reconstruct view ray
    // Use cached depths to compute entry/exit world positions
}
```

---

## A3. Pass 2 – Cloud Lighting & Shadow Prepass (Compute)

```glsl
#version 450
layout(local_size_x = 8, local_size_y = 8) in;

layout(rgba16f, binding = 0) writeonly uniform image2D cloudTransmittance;
layout(rgba16f, binding = 1) writeonly uniform image2D cloudScattering;

uniform vec3 sunDir;
uniform sampler3D cloudNoise;

void main() {
    ivec2 pix = ivec2(gl_GlobalInvocationID.xy);
    // Determine altitude band
    // March fixed steps inside cloud layer
    // Accumulate opacity and single-scattering
}
```

---

## A4. Pass 3 – Surface G-Buffer

**Vertex Shader (terrain/water)**

```glsl
#version 450
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

uniform mat4 viewProj;
uniform vec3 cameraPosRel;

void main() {
    vec3 posRel = position - cameraPosRel;
    gl_Position = viewProj * vec4(posRel, 1.0);
}
```

**Fragment Shader**

```glsl
#version 450
layout(location = 0) out vec2 gNormal;
layout(location = 1) out vec4 gAlbedo;
layout(location = 2) out vec2 gMaterial;

void main() {
    // Encode normal octahedrally
    // Output albedo, roughness, material ID
}
```

---

## A5. Pass 4 – Deferred Surface Lighting

```glsl
#version 450
layout(location = 0) out vec3 surfaceRadiance;

uniform sampler2D gbufferNormal;
uniform sampler2D gbufferAlbedo;
uniform sampler2D depth;
uniform vec3 sunDir;

void main() {
    // Reconstruct position
    // Direct sun lighting
    // Sky irradiance lookup
    // Single-bounce GI approximation
}
```

---

## A6. Pass 5 – Atmospheric & Volumetric Integration

```glsl
#version 450
layout(location = 0) out vec3 finalColor;

uniform sampler2D atmStart;
uniform sampler2D atmEnd;
uniform sampler2D surfaceRadiance;
uniform sampler2D cloudTransmittance;

void main() {
    // March between atmStart and atmEnd
    // Accumulate Rayleigh + Mie
    // Apply multiple scattering LUT
    // Composite surface contribution
}
```

---

# Appendix B – Buffer Formats and Memory Budget

**Reference Resolution Memory Estimate (1920×1080):**

At 1920×1080 (~2.07 million pixels):

* G-buffer total (16 bytes/pixel): ~33.2 MB
* Atmospheric entry/exit buffers (2 × RGB16F): ~24.8 MB
* Cloud buffers at half resolution (RGBA16F × 2): ~8.3 MB

**Approximate total transient GPU memory:** ~66–70 MB

This budget excludes static resources such as LUTs, shadow maps, terrain meshes, and textures, which are amortized across frames.

---

## B1. G-Buffer Layout

| Buffer | Format | Description             | Bytes/pixel |
| ------ | ------ | ----------------------- | ----------- |
| Depth  | D32F   | Reversed-Z depth        | 4           |
| RT0    | RG16F  | Normal (oct)            | 4           |
| RT1    | RGBA8  | Albedo                  | 4           |
| RT2    | RG16F  | Roughness + Material ID | 4           |

**Total:** 16 bytes/pixel

---

## B2. Atmospheric Buffers

| Buffer             | Format  | Resolution | Purpose        |
| ------------------ | ------- | ---------- | -------------- |
| atmStart           | RGB16F  | Full       | Entry position |
| atmEnd             | RGB16F  | Full       | Exit position  |
| cloudTransmittance | RGBA16F | Half       | Cloud opacity  |
| cloudScattering    | RGBA16F | Half       | Cloud lighting |

---

# Appendix C – Atmospheric LUT Definitions

## C0. LUT Update Frequency and Lifetime

To manage runtime cost and integration complexity, each atmospheric LUT has a defined update cadence:

* **Transmittance LUT**

  * Update frequency: *Static*
  * Generated offline or once at load time
  * Assumes fixed atmospheric composition and scale heights

* **Multiple Scattering LUT**

  * Update frequency: *Per sun-angle change (coarse)*
  * Recomputed only when the sun zenith angle changes beyond a threshold
  * Can be amortized over multiple frames using compute shaders

* **Sky Irradiance LUT**

  * Update frequency: *Per frame or per sun-angle*
  * Depends on sun direction and atmospheric state
  * Typically low resolution and inexpensive to update

All LUTs are treated as read-only during the main render passes and are never updated mid-frame.

## C1. Transmittance LUT

**Dimensions:**

* X: height (0–1, ground → top)
* Y: cos(sun zenith)

**Format:** RG16F

**Stored:**

* RGB transmittance

---

## C2. Multiple Scattering LUT

**Dimensions:**

* X: height
* Y: cos(sun zenith)

**Format:** RGB16F

Stores integrated higher-order scattering energy.

---

## C3. Sky Irradiance LUT

**Dimensions:**

* X: cos(view zenith)
* Y: cos(sun zenith)

**Format:** RGB16F

Used for surface lighting and horizon glow.

---

## C4. Parameterization

* Heights normalized by atmosphere thickness
* Angles clamped to [-1, 1]
* LUTs generated offline or at load time using compute shaders

---

# End of Technical Appendix


![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)
![img_3.png](img_3.png)
![img_4.png](img_4.png)