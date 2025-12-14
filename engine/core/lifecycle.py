class LifecycleManager:
    def __init__(self):
        self.subsystems = []
        self.started = False
        self.stopped = False

    def register(self, subsystem):
        self.subsystems.append(subsystem)

    def initialize_all(self):
        self.started = True
        for subsystem in self.subsystems:
            initializer = getattr(subsystem, "initialize", None)
            if callable(initializer):
                initializer()

    def shutdown_all(self):
        self.stopped = True
        for subsystem in reversed(self.subsystems):
            shutdown = getattr(subsystem, "shutdown", None)
            if callable(shutdown):
                shutdown()

    def start(self):
        self.initialize_all()

    def stop(self):
        self.shutdown_all()


Lifecycle = LifecycleManager
