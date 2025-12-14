import time

import glfw

from engine.camera.fly_camera import FlyCamera
from engine.core.config import Config
from engine.core.lifecycle import LifecycleManager
from engine.graphics.frame_graph import FrameGraph
from engine.graphics.renderer import Renderer
from engine.input.input_manager import InputManager
from engine.window.glfw_window import GLFWWindow


class Application:
    def __init__(self, config=None, headless=False):
        self.lifecycle = LifecycleManager()
        self.config = config or Config()
        self.headless = headless
        window_settings = self.config.get("window", {})
        self.window = GLFWWindow(
            width=window_settings.get("width", 800),
            height=window_settings.get("height", 600),
            title=window_settings.get("title", "YAWS3"),
            vsync=window_settings.get("vsync", True),
        )
        self.input = InputManager()
        self.camera = FlyCamera(position=[0.0, 0.0, 5.0])
        self.renderer = Renderer(FrameGraph(), enable_gl=not self.headless)
        self.delta_time = 0.0
        self.frame_count = 0

    def _bind_callbacks(self):
        handle = self.window.get_handle()

        def _on_key(_, key, _scancode, action, _mods):
            if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
                glfw.set_window_should_close(handle, True)
            self.input.on_key(key, action)

        def _on_cursor(_, x_pos, y_pos):
            self.input.on_mouse_move(x_pos, y_pos)

        glfw.set_key_callback(handle, _on_key)
        glfw.set_cursor_pos_callback(handle, _on_cursor)
        glfw.set_input_mode(handle, glfw.CURSOR, glfw.CURSOR_DISABLED)

    def _initialize(self):
        self.lifecycle.register(self.config)
        if not self.headless:
            self.lifecycle.register(self.window)
        self.lifecycle.register(self.input)
        self.lifecycle.register(self.camera)
        self.lifecycle.register(self.renderer)
        self.lifecycle.initialize_all()
        if not self.headless:
            self._bind_callbacks()
            self.renderer.initialize(self.window.width, self.window.height)
        else:
            self.renderer.initialize()

    def _update_camera(self):
        if self.window.height > 0:
            self.camera.aspect_ratio = float(self.window.width) / float(self.window.height)
        self.camera.update(self.input, self.delta_time)

    def _render_frame(self):
        if not self.headless:
            self.renderer.render_context.width = self.window.width
            self.renderer.render_context.height = self.window.height
        planet_center = [0.0, 0.0, 0.0]
        self.renderer.render(self.delta_time, self.camera, planet_center)

    def run(self, frames=None):
        self._initialize()
        previous = time.perf_counter()
        running = True
        while running:
            current = time.perf_counter()
            self.delta_time = max(0.0, current - previous)
            previous = current
            self.frame_count += 1

            if not self.headless:
                self.window.poll_events()
            self._update_camera()
            self._render_frame()
            if not self.headless:
                self.window.swap_buffers()
                running = not self.window.should_close()
            if frames is not None and self.frame_count >= frames:
                running = False
            self.input.reset_deltas()
        self.lifecycle.shutdown_all()
        return True
