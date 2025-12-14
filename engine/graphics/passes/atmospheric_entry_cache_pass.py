from engine.graphics.passes.base_pass import BasePass


class AtmosphericEntryCachePass(BasePass):
    def __init__(self):
        super().__init__("Atmospheric Entry/Exit Cache Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec3 o_atm_start_ws;
layout(location = 1) out vec3 o_atm_end_ws;

uniform sampler2D u_depth_atm_entry;
uniform sampler2D u_depth_atm_exit;
uniform mat4 u_inv_view_proj;
uniform vec2 u_resolution;

vec3 reconstruct_direction(vec2 frag_coord) {
    vec2 ndc = (frag_coord / u_resolution) * 2.0 - 1.0;
    vec4 clip = vec4(ndc, 1.0, 1.0);
    vec4 world = u_inv_view_proj * clip;
    return normalize(world.xyz / world.w);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float depth_entry = texture(u_depth_atm_entry, uv).r;
    float depth_exit = texture(u_depth_atm_exit, uv).r;
    vec3 dir = reconstruct_direction(gl_FragCoord.xy);
    if (isinf(depth_entry) || isinf(depth_exit)) {
        o_atm_start_ws = vec3(0.0);
        o_atm_end_ws = vec3(0.0);
    } else {
        o_atm_start_ws = dir * depth_entry;
        o_atm_end_ws = dir * depth_exit;
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
            "atm_start_ws": {"format": "RGB16F"},
            "atm_end_ws": {"format": "RGB16F"},
            "shader_sources": self.shader_sources,
        }
        render_context.set_texture("atm_start_ws", self.resources["atm_start_ws"])
        render_context.set_texture("atm_end_ws", self.resources["atm_end_ws"])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        render_context.set_texture("atm_start_ws", self.resources["atm_start_ws"])
        render_context.set_texture("atm_end_ws", self.resources["atm_end_ws"])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
