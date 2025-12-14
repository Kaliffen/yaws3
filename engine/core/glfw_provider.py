import importlib
import importlib.util


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

    def init(self):
        return False

    def window_hint(self, *_, **__):
        return None

    def create_window(self, *_, **__):
        return None

    def make_context_current(self, *_, **__):
        return None

    def set_framebuffer_size_callback(self, *_, **__):
        return None

    def poll_events(self):
        return None

    def swap_buffers(self, *_):
        return None

    def window_should_close(self, *_):
        return True

    def destroy_window(self, *_):
        return None

    def terminate(self):
        return None


def get_glfw():
    spec = importlib.util.find_spec("glfw")
    if spec is None:
        return _GLFWStub()
    return importlib.import_module("glfw")
