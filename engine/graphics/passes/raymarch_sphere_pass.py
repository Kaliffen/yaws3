from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_STATIC_DRAW,
    GL_TRIANGLE_STRIP,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindBuffer,
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
    glUniform2f,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
)
import numpy as np

from engine.graphics.passes.base_pass import BasePass


class RaymarchSpherePass(BasePass):
    def __init__(self):
        super().__init__("Raymarch Sphere Pass")
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

uniform mat4 u_inv_view_proj;
uniform vec2 u_resolution;
uniform vec3 u_sphere_center;
uniform float u_sphere_radius;
uniform vec3 u_light_dir;
uniform float u_time;

vec3 reconstruct_direction(vec2 frag_coord) {
    vec2 ndc = (frag_coord / u_resolution) * 2.0 - 1.0;
    vec4 clip = vec4(ndc, 1.0, 1.0);
    vec4 view = u_inv_view_proj * clip;
    return normalize(view.xyz / view.w);
}

float sdf_sphere(vec3 p) {
    return length(p - u_sphere_center) - u_sphere_radius;
}

vec3 estimate_normal(vec3 p) {
    const float e = 0.001;
    vec2 h = vec2(e, 0.0);
    return normalize(vec3(
        sdf_sphere(p + h.xyy) - sdf_sphere(p - h.xyy),
        sdf_sphere(p + h.yxy) - sdf_sphere(p - h.yxy),
        sdf_sphere(p + h.yyx) - sdf_sphere(p - h.yyx)
    ));
}

float march(vec3 ro, vec3 rd, out vec3 hit_pos) {
    float t = 0.0;
    for (int i = 0; i < 128; ++i) {
        vec3 p = ro + rd * t;
        float d = sdf_sphere(p);
        if (d < 0.001) {
            hit_pos = p;
            return t;
        }
        t += d;
        if (t > 200.0) break;
    }
    return -1.0;
}

void main() {
    vec3 ro = vec3(0.0);
    vec3 rd = reconstruct_direction(gl_FragCoord.xy);
    vec3 hit_pos = vec3(0.0);
    float t = march(ro, rd, hit_pos);
    if (t > 0.0) {
        vec3 normal = estimate_normal(hit_pos);
        float diffuse = max(dot(normalize(u_light_dir), normal), 0.0);
        vec3 color = vec3(0.3, 0.6, 1.0) * diffuse + vec3(0.05 * sin(u_time * 0.5) + 0.2);
        o_color = vec4(color, 1.0);
    } else {
        float grad = 0.5 + 0.5 * rd.y;
        vec3 sky = mix(vec3(0.05, 0.05, 0.08), vec3(0.2, 0.4, 0.8), grad);
        o_color = vec4(sky, 1.0);
    }
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        self.program = self._create_program()
        self._create_fullscreen_quad()
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        glClearColor(0.02, 0.02, 0.03, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.program)

        inv_view_proj = render_context.inv_view_proj.astype(np.float32)
        u_inv_view_proj = glGetUniformLocation(self.program, "u_inv_view_proj")
        glUniformMatrix4fv(u_inv_view_proj, 1, False, inv_view_proj)

        u_resolution = glGetUniformLocation(self.program, "u_resolution")
        glUniform2f(u_resolution, float(render_context.width), float(render_context.height))

        u_center = glGetUniformLocation(self.program, "u_sphere_center")
        center = render_context.planet_center_rel.astype(np.float32)
        glUniform3f(u_center, center[0], center[1], center[2])

        u_radius = glGetUniformLocation(self.program, "u_sphere_radius")
        glUniform1f(u_radius, float(render_context.planet_radius))

        light = render_context.sun_dir_rel.astype(np.float32)
        u_light = glGetUniformLocation(self.program, "u_light_dir")
        glUniform3f(u_light, light[0], light[1], light[2])

        u_time = glGetUniformLocation(self.program, "u_time")
        glUniform1f(u_time, float(render_context.time))

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glUseProgram(0)
        return True

    def shutdown(self):
        super().shutdown()
        if self.vbo:
            glDeleteBuffers(1, np.array([self.vbo], dtype=np.uint32))
            self.vbo = None
        if self.vao:
            glDeleteVertexArrays(1, np.array([self.vao], dtype=np.uint32))
            self.vao = None
        if self.program:
            glDeleteProgram(self.program)
            self.program = None
        return True
