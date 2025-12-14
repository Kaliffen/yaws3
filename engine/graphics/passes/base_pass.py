class BasePass:
    def __init__(self, name="BasePass"):
        self.name = name
        self.initialized = False
        self.executed = False
        self.shutdown_called = False
        self.shader_sources = {}

    @property
    def fullscreen_vertex(self):
        return """#version 330 core
layout (location = 0) in vec2 a_position;
out vec2 v_uv;
void main() {
    v_uv = a_position * 0.5 + 0.5;
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

    def initialize(self, render_context):
        self.initialized = True
        return True

    def execute(self, delta_time=0.0, render_context=None):
        self.executed = True
        return True

    def shutdown(self):
        self.shutdown_called = True
        return True
