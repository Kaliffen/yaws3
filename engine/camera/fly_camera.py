import numpy as np
import glfw
from pyrr import Matrix44, matrix44, quaternion


class FlyCamera:
    def __init__(self, position=None, fov=60.0, aspect_ratio=1.0, near=0.1, far=10_000.0):
        self.position = np.array(position if position is not None else [0.0, 0.0, 0.0], dtype=np.float64)
        self.orientation = quaternion.create()
        self.fov = float(fov)
        self.aspect_ratio = float(aspect_ratio)
        self.near = float(near)
        self.far = float(far)
        self.movement_speed = 10.0
        self.rotation_speed = 0.002

    def _normalize_orientation(self):
        self.orientation = quaternion.normalize(self.orientation)

    def _axis_from_orientation(self, axis):
        return quaternion.apply_to_vector(self.orientation, axis)

    def _rotate(self, axis, angle):
        delta = quaternion.create_from_axis_rotation(axis, angle)
        self.orientation = quaternion.cross(delta, self.orientation)
        self._normalize_orientation()

    def _planar_direction(self, direction):
        planar = np.array(direction, dtype=np.float64)
        planar[1] = 0.0
        if np.linalg.norm(planar) > 0.0:
            planar = planar / np.linalg.norm(planar)
        return planar

    def update(self, input_manager, delta_time):
        forward = self._axis_from_orientation([0.0, 0.0, -1.0])
        right = self._axis_from_orientation([1.0, 0.0, 0.0])
        up = self._axis_from_orientation([0.0, 1.0, 0.0])

        movement = np.zeros(3, dtype=np.float64)
        if input_manager.is_key_pressed(glfw.KEY_W):
            movement += self._planar_direction(forward)
        if input_manager.is_key_pressed(glfw.KEY_S):
            movement -= self._planar_direction(forward)
        if input_manager.is_key_pressed(glfw.KEY_A):
            movement -= self._planar_direction(right)
        if input_manager.is_key_pressed(glfw.KEY_D):
            movement += self._planar_direction(right)
        if input_manager.is_key_pressed(glfw.KEY_SPACE):
            movement += up
        if input_manager.is_key_pressed(glfw.KEY_LEFT_CONTROL):
            movement -= up

        if np.linalg.norm(movement) > 0.0:
            movement = movement / np.linalg.norm(movement)
            self.position += movement * self.movement_speed * float(delta_time)

        yaw = -input_manager.mouse_dx * self.rotation_speed
        pitch = -input_manager.mouse_dy * self.rotation_speed
        if yaw != 0.0:
            self._rotate([0.0, 1.0, 0.0], yaw)
        if pitch != 0.0:
            self._rotate(right, pitch)
        if input_manager.is_key_pressed(glfw.KEY_Q):
            self._rotate(forward, self.rotation_speed)
        if input_manager.is_key_pressed(glfw.KEY_E):
            self._rotate(forward, -self.rotation_speed)

    def get_view_matrix(self):
        rotation = matrix44.create_from_quaternion(quaternion.inverse(self.orientation), dtype=np.float32)
        translation = Matrix44.from_translation(-self.position.astype(np.float32))
        return matrix44.multiply(rotation, translation)

    def get_projection_matrix(self):
        return matrix44.create_perspective_projection(self.fov, self.aspect_ratio, self.near, self.far, dtype=np.float32)

    def get_view_projection_matrix(self):
        return matrix44.multiply(self.get_projection_matrix(), self.get_view_matrix())
