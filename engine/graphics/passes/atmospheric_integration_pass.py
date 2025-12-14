from engine.graphics.passes.base_pass import BasePass


class AtmosphericIntegrationPass(BasePass):
    def __init__(self):
        super().__init__("Atmospheric & Volumetric Integration Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec3 o_atmosphere_color;

uniform sampler2D u_atm_start_ws;
uniform sampler2D u_atm_end_ws;
uniform sampler2D u_surface_radiance;
uniform sampler2D u_cloud_transmittance;
uniform sampler2D u_cloud_scattered_light;
uniform vec3 u_sun_dir_rel;
uniform vec2 u_resolution;

float density_profile(float height) {
    return exp(-height * 0.0001);
}

void main() {
    ivec2 pixel = ivec2(gl_FragCoord.xy);
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 start_ws = texelFetch(u_atm_start_ws, pixel, 0).rgb;
    vec3 end_ws = texelFetch(u_atm_end_ws, pixel, 0).rgb;
    vec3 segment = end_ws - start_ws;
    float segment_length = length(segment);
    vec3 dir = segment_length > 0.0 ? segment / segment_length : vec3(0.0, 1.0, 0.0);

    const int steps = 48;
    float step_length = segment_length / float(steps);
    vec3 scattering = vec3(0.0);
    float transmittance = 1.0;

    for (int i = 0; i < steps; ++i) {
        vec3 sample_pos = start_ws + dir * (float(i) + 0.5) * step_length;
        float height = length(sample_pos);
        float density = density_profile(height);
        float extinction = density * 0.02;
        float scatter_term = max(dot(normalize(u_sun_dir_rel), dir), 0.0) * density;
        transmittance *= exp(-extinction * step_length);
        scattering += scatter_term * transmittance * step_length;
    }

    vec3 surface_light = texture(u_surface_radiance, uv).rgb;
    vec3 cloud_light = texture(u_cloud_scattered_light, uv).rgb;
    float cloud_t = texture(u_cloud_transmittance, uv).r;

    vec3 color = scattering + cloud_light;
    color += surface_light * cloud_t;
    o_atmosphere_color = color;
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "vertex": self.fullscreen_vertex,
            "fragment": self._fragment_shader(),
        }
        self.resources = {
            "atmosphere_color": {"format": "RGB16F"},
            "shader_sources": self.shader_sources,
        }
        render_context.set_texture("atmosphere_color", self.resources["atmosphere_color"])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        render_context.set_texture("atmosphere_color", self.resources["atmosphere_color"])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
