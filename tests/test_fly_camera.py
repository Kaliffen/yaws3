import numpy as np
import glfw

from engine.camera.fly_camera import FlyCamera
from engine.input.input_manager import InputManager


def build_input(mouse_dx=0.0, mouse_dy=0.0, keys=None):
    manager = InputManager()
    manager.initialize()
    manager.mouse_dx = mouse_dx
    manager.mouse_dy = mouse_dy
    for key in keys or []:
        manager.on_key(key, glfw.PRESS)
    return manager


def test_quaternion_normalization_invariant():
    camera = FlyCamera()
    input_state = build_input(mouse_dx=120.0, mouse_dy=-45.0, keys=[glfw.KEY_Q, glfw.KEY_E])

    camera.update(input_state, delta_time=0.016)
    camera.update(input_state, delta_time=0.016)

    norm = np.linalg.norm(camera.orientation)
    assert np.isclose(norm, 1.0, atol=1e-6)


def test_view_matrix_places_camera_at_origin():
    camera = FlyCamera(position=[10.5, -2.25, 3.75])
    input_state = build_input()

    camera.update(input_state, delta_time=0.0)
    view = camera.get_view_matrix()
    camera_point = np.append(camera.position.astype(np.float32), 1.0)
    transformed = camera_point @ np.asarray(view)

    assert np.allclose(transformed[:3], np.zeros(3), atol=1e-6)
