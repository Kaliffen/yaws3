import numpy as np

from engine.graphics.passes.base_pass import BasePass


class CompositeTonemapPass(BasePass):
    def __init__(self):
        super().__init__("Composite & Tone Mapping Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["final_color"] = np.zeros((h, w, 3), dtype=np.float32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        atmosphere = render_context.get_texture("atmosphere_radiance")
        final_color = self.resources["final_color"]
        exposure = 1.0
        h, w, _ = final_color.shape
        for y in range(h):
            for x in range(w):
                color = atmosphere[y, x] if atmosphere is not None else np.zeros(3, dtype=np.float32)
                mapped = 1.0 - np.exp(-color * exposure)
                final_color[y, x] = np.clip(mapped, 0.0, 1.0)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
