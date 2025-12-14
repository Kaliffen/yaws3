import time

from engine.core.config import Config
from engine.core.lifecycle import LifecycleManager
from engine.graphics.frame_graph import FrameGraph
from engine.graphics.renderer import Renderer


class _Subsystem:
    def __init__(self):
        self.initialized = False
        self.shutdown_called = False

    def initialize(self):
        self.initialized = True

    def shutdown(self):
        self.shutdown_called = True


class Application:
    def __init__(self, config=None):
        self.lifecycle = LifecycleManager()
        self.config = config or Config()
        self.window = _Subsystem()
        self.input = _Subsystem()
        self.camera = _Subsystem()
        self.renderer = Renderer(FrameGraph())
        self.delta_time = 0.0
        self.frame_count = 0

    def _initialize(self):
        self.lifecycle.register(self.config)
        self.lifecycle.register(self.window)
        self.lifecycle.register(self.input)
        self.lifecycle.register(self.camera)
        self.lifecycle.register(self.renderer)
        self.lifecycle.initialize_all()

    def run(self, frames=3):
        self._initialize()
        previous = time.perf_counter()
        for _ in range(frames):
            current = time.perf_counter()
            self.delta_time = max(0.0, current - previous)
            previous = current
            self.frame_count += 1
            render = getattr(self.renderer, "render", None)
            if callable(render):
                render()
        self.lifecycle.shutdown_all()
        return True
