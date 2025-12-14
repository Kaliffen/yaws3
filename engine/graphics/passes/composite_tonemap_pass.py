from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRAMEBUFFER,
    GL_LINK_STATUS,
    GL_STATIC_DRAW,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TRIANGLE_STRIP,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindBuffer,
    glBindFramebuffer,
    glBindTexture,
    glBindVertexArray,
    glBufferData,
    glClear,
    glClearColor,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteBuffers,
    glDeleteProgram,
    glDeleteShader,
    glDeleteVertexArrays,
    glDetachShader,
    glDisable,
    glDrawArrays,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)
import numpy as np

from engine.graphics.passes.base_pass import BasePass


class CompositeTonemapPass(BasePass):
    def __init__(self):
        super().__init__("Composite & Tone Mapping Pass")
        self.resources = {}
        self.program = None
        self.vao = None
        self.vbo = None

    def _compile_shader(self, source, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        status = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not status:
            info = glGetShaderInfoLog(shader)
            raise RuntimeError(f"Shader compilation failed: {info}")
        return shader

    def _create_program(self):
        vertex_shader = self._compile_shader(self.fullscreen_vertex, GL_VERTEX_SHADER)
        fragment_shader = self._compile_shader(self._fragment_shader(), GL_FRAGMENT_SHADER)
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            info = glGetProgramInfoLog(program)
            raise RuntimeError(f"Program link failed: {info}")
        glDetachShader(program, vertex_shader)
        glDetachShader(program, fragment_shader)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        return program

    def _create_fullscreen_quad(self):
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype=np.float32)
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, False, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec4 o_color;

uniform sampler2D u_surface_radiance;
uniform float u_exposure;
uniform vec2 u_resolution;

vec3 tonemap(vec3 color) {
    vec3 x = color * u_exposure;
    return x / (x + vec3(1.0));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 c = texture(u_surface_radiance, uv).rgb;
    vec3 mapped = tonemap(c);
    mapped = pow(mapped, vec3(1.0 / 2.2));
    o_color = vec4(mapped, 1.0);
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.program = self._create_program()
        self._create_fullscreen_quad()
        self.resources = {"shader_sources": {"vertex": self.fullscreen_vertex, "fragment": self._fragment_shader()}}
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        width = int(render_context.width)
        height = int(render_context.height)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, width, height)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.02, 0.03, 0.05, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.program)
        glActiveTexture(GL_TEXTURE0)
        surface = render_context.get_texture("surface_radiance")
        glBindTexture(GL_TEXTURE_2D, surface.get("id"))
        glUniform1i(glGetUniformLocation(self.program, "u_surface_radiance"), 0)
        glUniform1f(glGetUniformLocation(self.program, "u_exposure"), 1.2)
        glUniform2f(glGetUniformLocation(self.program, "u_resolution"), float(width), float(height))
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glUseProgram(0)
        return True

    def shutdown(self):
        super().shutdown()
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.program:
            glDeleteProgram(self.program)
        self.resources = {}
        self.shader_sources = {}
        self.program = None
        self.vao = None
        self.vbo = None
        return True
