import numpy as np

from engine.graphics.passes.base_pass import BasePass


class SurfaceGBufferPass(BasePass):
    def __init__(self):
        super().__init__("Surface G-Buffer Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["gbuffer_depth"] = np.full((h, w), np.inf, dtype=np.float32)
        self.resources["gbuffer_normal_roughness"] = np.zeros((h, w, 4), dtype=np.float32)
        self.resources["gbuffer_albedo_metalness"] = np.zeros((h, w, 4), dtype=np.float32)
        self.resources["gbuffer_material_id"] = np.zeros((h, w), dtype=np.int32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        normal_roughness = self.resources["gbuffer_normal_roughness"]
        albedo_metalness = self.resources["gbuffer_albedo_metalness"]
        depth = self.resources["gbuffer_depth"]
        material_id = self.resources["gbuffer_material_id"]
        h, w = depth.shape
        for y in range(h):
            for x in range(w):
                depth[y, x] = 1.0
                normal_roughness[y, x] = np.array([0.0, 1.0, 0.0, 0.5], dtype=np.float32)
                albedo_metalness[y, x] = np.array([0.2, 0.4, 0.6, 0.0], dtype=np.float32)
                material_id[y, x] = 1
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
