from engine.core.glfw_provider import get_glfw

glfw = get_glfw()


class InputManager:
    def __init__(self):
        self.keys_down = set()
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
        self._last_mouse_pos = None
        self.initialized = False
        self._press_actions = {glfw.PRESS, getattr(glfw, "REPEAT", 2), 1, 2}
        self._release_actions = {glfw.RELEASE, 0}

    def initialize(self):
        self.initialized = True

    def shutdown(self):
        self.keys_down.clear()
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
        self._last_mouse_pos = None
        self.initialized = False

    def on_key(self, key, action):
        if action in self._press_actions:
            self.keys_down.add(key)
        if action in self._release_actions and key in self.keys_down:
            self.keys_down.remove(key)

    def is_key_pressed(self, key):
        return key in self.keys_down

    def on_mouse_move(self, x_pos, y_pos):
        if self._last_mouse_pos is None:
            self._last_mouse_pos = (x_pos, y_pos)
            return
        dx = x_pos - self._last_mouse_pos[0]
        dy = y_pos - self._last_mouse_pos[1]
        self.mouse_dx += dx
        self.mouse_dy += dy
        self._last_mouse_pos = (x_pos, y_pos)

    def reset_deltas(self):
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
