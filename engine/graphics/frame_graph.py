class FrameGraph:
    def __init__(self):
        self.passes = []

    def add_pass(self, render_pass):
        self.passes.append(render_pass)
