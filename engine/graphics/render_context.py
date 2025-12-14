import numpy as np


class RenderContext:
    def __init__(self, width=1, height=1, inv_view_proj=None, sun_dir_rel=None,
                 planet_center_rel=None, planet_radius=1.0, atm_inner_radius=1.0,
                 atm_outer_radius=1.1):
        self.width = width
        self.height = height
        self.inv_view_proj = inv_view_proj if inv_view_proj is not None else np.identity(4, dtype=np.float32)
        self.sun_dir_rel = self._normalize(sun_dir_rel if sun_dir_rel is not None else np.array([0.0, 1.0, 0.0], dtype=np.float32))
        self.planet_center_rel = np.array(planet_center_rel if planet_center_rel is not None else [0.0, 0.0, 0.0], dtype=np.float32)
        self.planet_radius = float(planet_radius)
        self.atm_inner_radius = float(atm_inner_radius)
        self.atm_outer_radius = float(atm_outer_radius)
        self.time = 0.0
        self.textures = {}

    def _normalize(self, v):
        length = float(np.linalg.norm(v))
        if length == 0.0:
            return np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return np.array(v, dtype=np.float32) / length

    def update_time(self, delta_time):
        self.time += float(delta_time)

    def set_texture(self, name, value):
        self.textures[name] = value

    def get_texture(self, name, default=None):
        return self.textures.get(name, default)
