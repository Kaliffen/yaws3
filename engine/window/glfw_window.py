import glfw
from OpenGL.GL import glViewport


class GLFWWindow:
    def __init__(self, width=1280, height=720, title="YAWS3", vsync=True):
        self.width = width
        self.height = height
        self.title = title
        self.vsync = vsync
        self._window = None
        self.initialized = False

    def initialize(self):
        if self.initialized:
            return
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        self._window = glfw.create_window(self.width, self.height, self.title, None, None)
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        glfw.make_context_current(self._window)
        glfw.swap_interval(1 if self.vsync else 0)
        glfw.set_framebuffer_size_callback(self._window, self._framebuffer_size_callback)
        self.initialized = True

    def _framebuffer_size_callback(self, window, width, height):
        self.width = width
        self.height = height
        try:
            glViewport(0, 0, width, height)
        except Exception:
            pass

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self._window)

    def should_close(self):
        return glfw.window_should_close(self._window)

    def shutdown(self):
        if self._window:
            glfw.destroy_window(self._window)
            self._window = None
        glfw.terminate()
        self.initialized = False

    def get_handle(self):
        return self._window
