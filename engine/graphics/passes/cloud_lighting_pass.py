import numpy as np

from engine.graphics.passes.base_pass import BasePass


class CloudLightingPass(BasePass):
    def __init__(self):
        super().__init__("Cloud Lighting & Shadow Prepass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["cloud_transmittance"] = np.ones((h, w), dtype=np.float32)
        self.resources["cloud_scattered_light"] = np.zeros((h, w, 3), dtype=np.float32)
        self.resources["cloud_shadow_mask"] = np.ones((h, w), dtype=np.float32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        atm_start = render_context.get_texture("atm_start_ws")
        atm_end = render_context.get_texture("atm_end_ws")
        sun_dir = render_context.sun_dir_rel
        cloud_transmittance = self.resources["cloud_transmittance"]
        cloud_scattered = self.resources["cloud_scattered_light"]
        cloud_shadow = self.resources["cloud_shadow_mask"]
        steps = 32
        h, w, _ = atm_start.shape
        for y in range(h):
            for x in range(w):
                start = atm_start[y, x]
                end = atm_end[y, x]
                segment = end - start
                length = float(np.linalg.norm(segment))
                if length == 0.0:
                    cloud_transmittance[y, x] = 1.0
                    cloud_scattered[y, x] = 0.0
                    cloud_shadow[y, x] = 1.0
                    continue
                direction = segment / length
                optical_depth = 0.0
                scattered = np.zeros(3, dtype=np.float32)
                step_size = length / steps
                for i in range(steps):
                    t = (i + 0.5) / steps
                    sample_pos = start + direction * (t * length)
                    height = max(0.0, np.linalg.norm(sample_pos) - render_context.planet_radius)
                    if 1000.0 <= height <= 4000.0:
                        density = max(0.0, 1.0 - (height - 1000.0) / 3000.0)
                    else:
                        density = 0.0
                    optical_depth += density * step_size * 0.001
                    trans = np.exp(-optical_depth)
                    scattered += density * trans * max(0.0, np.dot(direction, sun_dir)) * step_size
                    if trans < 0.05:
                        break
                cloud_transmittance[y, x] = float(np.exp(-optical_depth))
                cloud_scattered[y, x] = scattered
                cloud_shadow[y, x] = cloud_transmittance[y, x]
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
