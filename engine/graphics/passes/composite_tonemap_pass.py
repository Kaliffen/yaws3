from engine.graphics.passes.base_pass import BasePass


class CompositeTonemapPass(BasePass):
    def __init__(self):
        super().__init__("Composite & Tone Mapping Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec4 o_color;

uniform sampler2D u_atmosphere_color;
uniform float u_exposure;
uniform vec2 u_resolution;

vec3 tonemap(vec3 color) {
    color *= u_exposure;
    return color / (color + vec3(1.0));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 c = texture(u_atmosphere_color, uv).rgb;
    vec3 mapped = tonemap(c);
    o_color = vec4(mapped, 1.0);
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "vertex": self.fullscreen_vertex,
            "fragment": self._fragment_shader(),
        }
        self.resources = {"shader_sources": self.shader_sources}
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
