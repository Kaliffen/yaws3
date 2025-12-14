from engine.graphics.passes.base_pass import BasePass


class CloudLightingPass(BasePass):
    def __init__(self):
        super().__init__("Cloud Lighting & Shadow Prepass")
        self.resources = {}

    def _compute_shader(self):
        return """#version 430 core
layout (local_size_x = 8, local_size_y = 8) in;

layout(binding = 0, rgba16f) writeonly uniform image2D o_cloud_transmittance;
layout(binding = 1, rgba16f) writeonly uniform image2D o_cloud_scattered_light;
layout(binding = 2, r16f) writeonly uniform image2D o_cloud_shadow_mask;

uniform sampler2D u_atm_start_ws;
uniform sampler2D u_atm_end_ws;
uniform vec3 u_sun_dir_rel;
uniform vec2 u_resolution;

float hash13(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}

void main() {
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(pixel, ivec2(u_resolution)))) {
        return;
    }
    vec2 uv = (vec2(pixel) + 0.5) / u_resolution;
    vec3 start_ws = texelFetch(u_atm_start_ws, pixel, 0).rgb;
    vec3 end_ws = texelFetch(u_atm_end_ws, pixel, 0).rgb;
    vec3 segment = end_ws - start_ws;
    float segment_length = length(segment);
    vec3 dir = segment_length > 0.0 ? segment / segment_length : vec3(0.0, 1.0, 0.0);

    const int steps = 32;
    float step_length = segment_length / float(steps);
    float transmittance = 1.0;
    vec3 scattered = vec3(0.0);

    for (int i = 0; i < steps; ++i) {
        vec3 sample_pos = start_ws + dir * (float(i) + 0.5) * step_length;
        float density = hash13(sample_pos * 0.001);
        float extinction = density * 0.05;
        float scatter_amount = max(dot(normalize(u_sun_dir_rel), dir), 0.0) * density;
        transmittance *= exp(-extinction * step_length);
        scattered += scatter_amount * transmittance * step_length;
        if (transmittance < 0.01) {
            break;
        }
    }

    imageStore(o_cloud_transmittance, pixel, vec4(vec3(transmittance), 1.0));
    imageStore(o_cloud_scattered_light, pixel, vec4(scattered, 1.0));
    imageStore(o_cloud_shadow_mask, pixel, vec4(transmittance));
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "compute": self._compute_shader(),
        }
        self.resources = {
            "cloud_transmittance": {"format": "RGBA16F"},
            "cloud_scattered_light": {"format": "RGBA16F"},
            "cloud_shadow_mask": {"format": "R16F"},
            "shader_sources": self.shader_sources,
        }
        render_context.set_texture("cloud_transmittance", self.resources["cloud_transmittance"])
        render_context.set_texture("cloud_scattered_light", self.resources["cloud_scattered_light"])
        render_context.set_texture("cloud_shadow_mask", self.resources["cloud_shadow_mask"])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        render_context.set_texture("cloud_transmittance", self.resources["cloud_transmittance"])
        render_context.set_texture("cloud_scattered_light", self.resources["cloud_scattered_light"])
        render_context.set_texture("cloud_shadow_mask", self.resources["cloud_shadow_mask"])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
