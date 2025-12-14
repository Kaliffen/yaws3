import numpy as np

from engine.graphics.passes.base_pass import BasePass


class DeferredSurfaceLightingPass(BasePass):
    def __init__(self):
        super().__init__("Deferred Surface Lighting Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["surface_radiance"] = np.zeros((h, w, 3), dtype=np.float32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        sun_dir = render_context.sun_dir_rel
        normals = render_context.get_texture("gbuffer_normal_roughness")
        albedo = render_context.get_texture("gbuffer_albedo_metalness")
        surface_radiance = self.resources["surface_radiance"]
        h, w, _ = surface_radiance.shape
        for y in range(h):
            for x in range(w):
                n = normals[y, x][:3]
                color = albedo[y, x][:3]
                lambert = max(0.0, float(np.dot(n, sun_dir)))
                surface_radiance[y, x] = color * lambert
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
