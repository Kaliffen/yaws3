class BasePass:
    def __init__(self, name="BasePass"):
        self.name = name
        self.initialized = False
        self.executed = False
        self.shutdown_called = False

    def initialize(self, render_context):
        self.initialized = True
        return True

    def execute(self, delta_time=0.0, render_context=None):
        self.executed = True
        return True

    def shutdown(self):
        self.shutdown_called = True
        return True
