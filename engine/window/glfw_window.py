try:
    import glfw
except ImportError as exc:  # pragma: no cover - fallback for environments without GLFW
    class _GLFWStub:
        PRESS = 1
        RELEASE = 0
        REPEAT = 2
        TRUE = 1
        CONTEXT_VERSION_MAJOR = 0
        CONTEXT_VERSION_MINOR = 1
        OPENGL_PROFILE = 2
        OPENGL_CORE_PROFILE = 3
        OPENGL_FORWARD_COMPAT = 4

        def __getattr__(self, _):
            raise ImportError("glfw is required for windowing") from exc

    glfw = _GLFWStub()

from OpenGL.GL import glViewport


class GLFWWindow:
    def __init__(self, width=1280, height=720, title="YAWS3"):
        self.width = width
        self.height = height
        self.title = title
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
