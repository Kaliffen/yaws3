from engine.graphics.passes.base_pass import BasePass


class DeferredSurfaceLightingPass(BasePass):
    def __init__(self):
        super().__init__("Deferred Surface Lighting Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec3 o_surface_radiance;

uniform sampler2D u_gbuffer_normal_roughness;
uniform sampler2D u_gbuffer_albedo_metalness;
uniform vec3 u_sun_dir_rel;
uniform vec2 u_resolution;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 normal = texture(u_gbuffer_normal_roughness, uv).xyz * 2.0 - 1.0;
    float roughness = texture(u_gbuffer_normal_roughness, uv).w;
    vec3 albedo = texture(u_gbuffer_albedo_metalness, uv).rgb;
    float ndl = max(dot(normalize(normal), normalize(u_sun_dir_rel)), 0.0);
    vec3 diffuse = albedo * ndl;
    o_surface_radiance = diffuse * (1.0 - roughness);
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "vertex": self.fullscreen_vertex,
            "fragment": self._fragment_shader(),
        }
        self.resources = {
            "surface_radiance": {"format": "RGB16F"},
            "shader_sources": self.shader_sources,
        }
        render_context.set_texture("surface_radiance", self.resources["surface_radiance"])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        render_context.set_texture("surface_radiance", self.resources["surface_radiance"])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
