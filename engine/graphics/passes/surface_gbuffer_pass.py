from engine.graphics.passes.base_pass import BasePass


class SurfaceGBufferPass(BasePass):
    def __init__(self):
        super().__init__("Surface G-Buffer Pass")
        self.resources = {}

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out float o_depth;
layout(location = 1) out vec4 o_normal_roughness;
layout(location = 2) out vec4 o_albedo_metalness;
layout(location = 3) out uint o_material_id;

void main() {
    o_depth = gl_FragCoord.z;
    o_normal_roughness = vec4(0.0, 1.0, 0.0, 0.5);
    o_albedo_metalness = vec4(vec3(0.5), 0.0);
    o_material_id = 1u;
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.shader_sources = {
            "vertex": self.fullscreen_vertex,
            "fragment": self._fragment_shader(),
        }
        self.resources = {
            "gbuffer_depth": {"format": "R32F"},
            "gbuffer_normal_roughness": {"format": "RGBA16F"},
            "gbuffer_albedo_metalness": {"format": "RGBA16F"},
            "gbuffer_material_id": {"format": "R8UI"},
            "shader_sources": self.shader_sources,
        }
        render_context.set_texture("gbuffer_depth", self.resources["gbuffer_depth"])
        render_context.set_texture("gbuffer_normal_roughness", self.resources["gbuffer_normal_roughness"])
        render_context.set_texture("gbuffer_albedo_metalness", self.resources["gbuffer_albedo_metalness"])
        render_context.set_texture("gbuffer_material_id", self.resources["gbuffer_material_id"])
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        render_context.set_texture("gbuffer_depth", self.resources["gbuffer_depth"])
        render_context.set_texture("gbuffer_normal_roughness", self.resources["gbuffer_normal_roughness"])
        render_context.set_texture("gbuffer_albedo_metalness", self.resources["gbuffer_albedo_metalness"])
        render_context.set_texture("gbuffer_material_id", self.resources["gbuffer_material_id"])
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        self.shader_sources = {}
        return True
