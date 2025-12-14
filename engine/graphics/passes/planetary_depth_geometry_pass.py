import numpy as np

from engine.graphics.passes.base_pass import BasePass


class PlanetaryDepthGeometryPass(BasePass):
    ATMOSPHERE = 1
    TERRAIN = 2
    WATER = 4
    SPACE = 8

    def __init__(self):
        super().__init__("Planetary Depth & Geometry Classification Pass")
        self.resources = {}

    def initialize(self, render_context):
        super().initialize(render_context)
        w, h = render_context.width, render_context.height
        self.resources["depth_planet"] = np.full((h, w), np.inf, dtype=np.float32)
        self.resources["depth_atm_entry"] = np.full((h, w), np.inf, dtype=np.float32)
        self.resources["depth_atm_exit"] = np.full((h, w), np.inf, dtype=np.float32)
        self.resources["geometry_mask"] = np.zeros((h, w), dtype=np.uint32)
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

    def _ray_sphere(self, origin, direction, center, radius):
        oc = origin - center
        a = float(np.dot(direction, direction))
        b = 2.0 * float(np.dot(oc, direction))
        c = float(np.dot(oc, oc) - radius * radius)
        disc = b * b - 4.0 * a * c
        if disc < 0.0:
            return False, np.inf, np.inf
        sqrt_disc = np.sqrt(disc)
        t0 = (-b - sqrt_disc) / (2.0 * a)
        t1 = (-b + sqrt_disc) / (2.0 * a)
        t_near = min(t0, t1)
        t_far = max(t0, t1)
        return True, t_near, t_far

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        if render_context is None:
            return True
        origin = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        center = render_context.planet_center_rel
        planet_radius = render_context.planet_radius
        atm_inner = render_context.atm_inner_radius
        atm_outer = render_context.atm_outer_radius
        width, height = render_context.width, render_context.height
        inv_view_proj = render_context.inv_view_proj
        depth_planet = self.resources["depth_planet"]
        depth_atm_entry = self.resources["depth_atm_entry"]
        depth_atm_exit = self.resources["depth_atm_exit"]
        geometry_mask = self.resources["geometry_mask"]
        for y in range(height):
            for x in range(width):
                direction = self._reconstruct_direction(inv_view_proj, x, y, width, height)
                hit_planet, t_near_planet, t_far_planet = self._ray_sphere(origin, direction, center, planet_radius)
                hit_atm_outer, t_near_outer, t_far_outer = self._ray_sphere(origin, direction, center, atm_outer)
                hit_atm_inner, t_near_inner, t_far_inner = self._ray_sphere(origin, direction, center, atm_inner)
                geometry_mask[y, x] = self.SPACE
                depth_planet[y, x] = np.inf
                depth_atm_entry[y, x] = np.inf
                depth_atm_exit[y, x] = np.inf
                if hit_atm_outer and t_far_outer > 0.0:
                    entry = max(t_near_outer, 0.0)
                    exit_t = t_far_outer
                    if hit_atm_inner and t_near_inner > 0.0:
                        entry = max(entry, t_near_inner)
                        exit_t = min(exit_t, t_far_inner)
                    depth_atm_entry[y, x] = entry
                    depth_atm_exit[y, x] = exit_t
                    geometry_mask[y, x] = self.ATMOSPHERE
                if hit_planet and t_far_planet > 0.0:
                    depth_planet[y, x] = max(t_near_planet, 0.0)
                    geometry_mask[y, x] |= self.TERRAIN
        for name, value in self.resources.items():
            render_context.set_texture(name, value)
        return True

    def shutdown(self):
        super().shutdown()
        self.resources = {}
        return True
