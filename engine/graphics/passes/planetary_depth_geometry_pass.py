from engine.graphics.passes.base_pass import BasePass


class PlanetaryDepthGeometryPass(BasePass):
    ATMOSPHERE = 1
    TERRAIN = 2
    WATER = 4
    SPACE = 8

    def __init__(self):
        super().__init__("Planetary Depth & Geometry Classification Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out float o_depth_planet;
layout(location = 1) out float o_depth_atm_entry;
layout(location = 2) out float o_depth_atm_exit;
layout(location = 3) out uint o_geometry_mask;

uniform mat4 u_inv_view_proj;
uniform vec2 u_resolution;
uniform vec3 u_planet_center_rel;
uniform float u_planet_radius;
uniform float u_atm_inner_radius;
uniform float u_atm_outer_radius;

const uint MASK_ATMOSPHERE = 1u;
const uint MASK_TERRAIN = 2u;
const uint MASK_WATER = 4u;
const uint MASK_SPACE = 8u;

vec3 reconstruct_direction(vec2 frag_coord) {
    vec2 ndc = (frag_coord / u_resolution) * 2.0 - 1.0;
    vec4 clip = vec4(ndc, 1.0, 1.0);
    vec4 world = u_inv_view_proj * clip;
    vec3 dir = normalize(world.xyz / world.w);
    return dir;
}

bool intersect_sphere(vec3 origin, vec3 dir, vec3 center, float radius, out float t_near, out float t_far) {
    vec3 oc = origin - center;
    float a = dot(dir, dir);
    float b = 2.0 * dot(oc, dir);
    float c = dot(oc, oc) - radius * radius;
    float disc = b * b - 4.0 * a * c;
    if (disc < 0.0) {
        t_near = -1.0;
        t_far = -1.0;
        return false;
    }
    float sqrt_disc = sqrt(disc);
    t_near = (-b - sqrt_disc) / (2.0 * a);
    t_far = (-b + sqrt_disc) / (2.0 * a);
    if (t_near > t_far) {
        float tmp = t_near;
        t_near = t_far;
        t_far = tmp;
    }
    return true;
}

void main() {
    vec3 origin = vec3(0.0);
    vec3 dir = reconstruct_direction(gl_FragCoord.xy);
    float t_near_planet; float t_far_planet;
    float t_near_outer; float t_far_outer;
    float t_near_inner; float t_far_inner;
    bool hit_planet = intersect_sphere(origin, dir, u_planet_center_rel, u_planet_radius, t_near_planet, t_far_planet);
    bool hit_outer = intersect_sphere(origin, dir, u_planet_center_rel, u_atm_outer_radius, t_near_outer, t_far_outer);
    bool hit_inner = intersect_sphere(origin, dir, u_planet_center_rel, u_atm_inner_radius, t_near_inner, t_far_inner);

    o_geometry_mask = MASK_SPACE;
    o_depth_planet = 1e30;
    o_depth_atm_entry = 1e30;
    o_depth_atm_exit = 1e30;

    if (hit_outer && t_far_outer > 0.0) {
        float entry = max(t_near_outer, 0.0);
        float exit_t = t_far_outer;
        if (hit_inner && t_near_inner > 0.0) {
            entry = max(entry, t_near_inner);
            exit_t = min(exit_t, t_far_inner);
        }
        o_depth_atm_entry = entry;
        o_depth_atm_exit = exit_t;
        o_geometry_mask = MASK_ATMOSPHERE;
    }

    if (hit_planet && t_far_planet > 0.0) {
        o_depth_planet = max(t_near_planet, 0.0);
        o_geometry_mask |= MASK_TERRAIN;
    }
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "vertex": self.fullscreen_vertex,
            "fragment": self._fragment_shader(),
        }
        self.resources = {
            "depth_planet": {"format": "R32F"},
            "depth_atm_entry": {"format": "R32F"},
            "depth_atm_exit": {"format": "R32F"},
            "geometry_mask": {"format": "R8UI"},
            "shader_sources": self.shader_sources,
        }
        for name in ["depth_planet", "depth_atm_entry", "depth_atm_exit", "geometry_mask"]:
            render_context.set_texture(name, self.resources[name])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        for name in ["depth_planet", "depth_atm_entry", "depth_atm_exit", "geometry_mask"]:
            render_context.set_texture(name, self.resources[name])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
