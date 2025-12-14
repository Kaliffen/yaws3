from engine.input.input_manager import InputManager


def test_key_state_transitions_without_window():
    manager = InputManager()
    manager.initialize()
    key = "SPACE"

    manager.on_key(key, 1)
    assert manager.is_key_pressed(key) is True

    manager.on_key(key, 2)
    assert manager.is_key_pressed(key) is True

    manager.on_key(key, 0)
    assert manager.is_key_pressed(key) is False


def test_mouse_delta_resets_each_frame():
    manager = InputManager()
    manager.initialize()

    manager.on_mouse_move(100.0, 200.0)
    manager.on_mouse_move(110.0, 215.0)
    assert manager.mouse_dx == 10.0
    assert manager.mouse_dy == 15.0

    manager.reset_deltas()
    assert manager.mouse_dx == 0.0
    assert manager.mouse_dy == 0.0

    manager.on_mouse_move(120.0, 230.0)
    assert manager.mouse_dx == 10.0
    assert manager.mouse_dy == 15.0
