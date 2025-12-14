import math
from typing import Tuple

import numpy as np
import pyrr


class Camera:
    def __init__(self, position: Tuple[float, float, float], fov_degrees: float):
        self.position = np.array(position, dtype=np.float64)
        self.fov = fov_degrees
        self.near = 0.1
        self.far = 1e7
        self.yaw = 0.0
        self.pitch = 0.0
        self.orientation = pyrr.quaternion.create_from_eulers([0.0, 0.0, 0.0], dtype=np.float64)

    def update_orientation(self, yaw_delta: float, pitch_delta: float):
        self.yaw += yaw_delta
        self.pitch = max(-math.pi * 0.499, min(math.pi * 0.499, self.pitch + pitch_delta))
        self.orientation = pyrr.quaternion.create_from_eulers([self.pitch, self.yaw, 0.0], dtype=np.float64)

    def basis(self):
        forward = pyrr.quaternion.apply_to_vector(self.orientation, np.array([0.0, 0.0, -1.0]))
        right = pyrr.quaternion.apply_to_vector(self.orientation, np.array([1.0, 0.0, 0.0]))
        up = pyrr.quaternion.apply_to_vector(self.orientation, np.array([0.0, 1.0, 0.0]))
        return forward, right, up

    def view_matrix(self) -> np.ndarray:
        rot = pyrr.matrix33.create_from_quaternion(pyrr.quaternion.inverse(self.orientation), dtype=np.float64)
        trans = rot @ (-self.position)
        view = np.identity(4, dtype=np.float64)
        view[:3, :3] = rot
        view[:3, 3] = trans
        return view.astype(np.float32)

    def projection_matrix(self, aspect: float) -> np.ndarray:
        return pyrr.matrix44.create_perspective_projection_matrix(self.fov, aspect, self.near, self.far, dtype=np.float32)

    def inv_view_proj(self, aspect: float) -> np.ndarray:
        view = self.view_matrix().astype(np.float64)
        proj = self.projection_matrix(aspect).astype(np.float64)
        inv = np.linalg.inv(proj @ view)
        return inv.astype(np.float32)
