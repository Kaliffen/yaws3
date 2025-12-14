from pathlib import Path
from typing import Iterable

import numpy as np
from OpenGL import GL as gl


class ShaderProgram:
    def __init__(self, vertex_path: Path, fragment_path: Path):
        self.program = gl.glCreateProgram()
        vs = self._compile_shader(vertex_path, gl.GL_VERTEX_SHADER)
        fs = self._compile_shader(fragment_path, gl.GL_FRAGMENT_SHADER)
        gl.glAttachShader(self.program, vs)
        gl.glAttachShader(self.program, fs)
        gl.glLinkProgram(self.program)
        if not gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS):
            log = gl.glGetProgramInfoLog(self.program).decode()
            raise RuntimeError(f"Link failed: {log}")
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

    def _compile_shader(self, path: Path, shader_type: int) -> int:
        shader = gl.glCreateShader(shader_type)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)
        if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
            log = gl.glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"Compile failed for {path}: {log}")
        return shader

    def use(self):
        gl.glUseProgram(self.program)

    def set_matrix4(self, name: str, value: Iterable[float]):
        loc = gl.glGetUniformLocation(self.program, name)
        data = np.array(value, dtype=np.float32, order="F")
        gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, data)

    def set_vector2(self, name: str, value: Iterable[float]):
        loc = gl.glGetUniformLocation(self.program, name)
        gl.glUniform2f(loc, *value)

    def set_float(self, name: str, value: float):
        loc = gl.glGetUniformLocation(self.program, name)
        gl.glUniform1f(loc, value)

    def set_int(self, name: str, value: int):
        loc = gl.glGetUniformLocation(self.program, name)
        gl.glUniform1i(loc, value)
