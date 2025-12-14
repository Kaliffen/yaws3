import numpy as np

from engine.graphics.passes.base_pass import BasePass


class AtmosphericEntryCachePass(BasePass):
    def __init__(self):
        super().__init__("Atmospheric Entry/Exit Cache Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["atm_start_ws"] = np.zeros((h, w, 3), dtype=np.float32)
        self.resources["atm_end_ws"] = np.zeros((h, w, 3), dtype=np.float32)
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def _reconstruct_direction(self, inv_view_proj, x, y, width, height):
        ndc_x = (2.0 * ((x + 0.5) / float(width))) - 1.0
        ndc_y = (2.0 * ((y + 0.5) / float(height))) - 1.0
        far = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)
        far_world = inv_view_proj @ far
        far_world = far_world[:3] / far_world[3]
        length = np.linalg.norm(far_world)
        if length == 0.0:
            return np.array([0.0, 0.0, 1.0], dtype=np.float32)
        return far_world / length

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        width, height = render_context.width, render_context.height
        inv_view_proj = render_context.inv_view_proj
        depth_entry = render_context.get_texture("depth_atm_entry")
        depth_exit = render_context.get_texture("depth_atm_exit")
        atm_start = self.resources["atm_start_ws"]
        atm_end = self.resources["atm_end_ws"]
        for y in range(height):
            for x in range(width):
                direction = self._reconstruct_direction(inv_view_proj, x, y, width, height)
                entry_depth = depth_entry[y, x]
                exit_depth = depth_exit[y, x]
                if np.isfinite(entry_depth) and np.isfinite(exit_depth):
                    atm_start[y, x] = direction * entry_depth
                    atm_end[y, x] = direction * exit_depth
                else:
                    atm_start[y, x] = 0.0
                    atm_end[y, x] = 0.0
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
