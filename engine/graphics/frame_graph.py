class FrameGraph:
    def __init__(self):
        self.passes = []
        self.render_context = None

    def add_pass(self, render_pass):
        self.passes.append(render_pass)

    def initialize(self, render_context):
        self.render_context = render_context
        for render_pass in self.passes:
            initializer = getattr(render_pass, "initialize", None)
            if callable(initializer):
                initializer(render_context)
        return True

    def execute(self, delta_time=0.0, render_context=None):
        context = render_context if render_context is not None else self.render_context
        for render_pass in self.passes:
            executor = getattr(render_pass, "execute", None)
            if callable(executor):
                executor(delta_time, context)
        return True

    def shutdown(self):
        for render_pass in reversed(self.passes):
            shutdown = getattr(render_pass, "shutdown", None)
            if callable(shutdown):
                shutdown()
        return True

    def get_pass_order(self):
        return [render_pass.name for render_pass in self.passes]
