import glfw


class Window:
    def __init__(self, width: int, height: int, title: str):
        if not glfw.init():
            raise RuntimeError("Failed to init GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, 0)
        glfw.window_hint(glfw.SRGB_CAPABLE, glfw.FALSE)
        self._window = glfw.create_window(width, height, title, None, None)
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Failed to create window")
        glfw.make_context_current(self._window)
        glfw.swap_interval(0)
        glfw.set_input_mode(self._window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    @property
    def handle(self):
        return self._window

    def should_close(self) -> bool:
        return glfw.window_should_close(self._window) == 1

    def poll(self):
        glfw.poll_events()

    def get_framebuffer_size(self) -> tuple[int, int]:
        return glfw.get_framebuffer_size(self._window)

    def close(self):
        glfw.destroy_window(self._window)
        glfw.terminate()
