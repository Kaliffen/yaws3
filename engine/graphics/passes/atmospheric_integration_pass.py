import numpy as np

from engine.graphics.passes.base_pass import BasePass


class AtmosphericIntegrationPass(BasePass):
    def __init__(self):
        super().__init__("Atmospheric & Volumetric Integration Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["atmosphere_radiance"] = np.zeros((h, w, 3), dtype=np.float32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        atm_start = render_context.get_texture("atm_start_ws")
        atm_end = render_context.get_texture("atm_end_ws")
        surface_radiance = render_context.get_texture("surface_radiance")
        cloud_trans = render_context.get_texture("cloud_transmittance")
        sun_dir = render_context.sun_dir_rel
        atmosphere_radiance = self.resources["atmosphere_radiance"]
        steps = 48
        h, w, _ = atmosphere_radiance.shape
        for y in range(h):
            for x in range(w):
                start = atm_start[y, x]
                end = atm_end[y, x]
                segment = end - start
                length = float(np.linalg.norm(segment))
                if length == 0.0:
                    transmittance = 1.0
                    scattering = np.zeros(3, dtype=np.float32)
                else:
                    direction = segment / length
                    step_size = length / steps
                    optical_depth = 0.0
                    scattering = np.zeros(3, dtype=np.float32)
                    for i in range(steps):
                        t = (i + 0.5) / steps
                        sample_pos = start + direction * (t * length)
                        height = max(0.0, np.linalg.norm(sample_pos) - render_context.planet_radius)
                        density = np.exp(-height * 0.0001)
                        optical_depth += density * step_size * 0.002
                        trans = np.exp(-optical_depth)
                        scattering += density * trans * max(0.0, np.dot(direction, sun_dir)) * step_size
                        if trans < 0.02:
                            break
                    transmittance = float(np.exp(-optical_depth))
                surface = surface_radiance[y, x] if surface_radiance is not None else np.zeros(3, dtype=np.float32)
                cloud_t = cloud_trans[y, x] if cloud_trans is not None else 1.0
                transmittance *= cloud_t
                atmosphere_radiance[y, x] = scattering + surface * transmittance
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
