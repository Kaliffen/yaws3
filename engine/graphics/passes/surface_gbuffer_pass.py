from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COMPILE_STATUS,
    GL_CLAMP_TO_EDGE,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRAMEBUFFER,
    GL_LINK_STATUS,
    GL_NEAREST,
    GL_RGBA,
    GL_RGBA16F,
    GL_R32F,
    GL_RED,
    GL_STATIC_DRAW,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRIANGLE_STRIP,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindBuffer,
    glBindFramebuffer,
    glBindTexture,
    glBindVertexArray,
    glBufferData,
    glClear,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteBuffers,
    glDeleteFramebuffers,
    glDeleteProgram,
    glDeleteShader,
    glDeleteTextures,
    glDeleteVertexArrays,
    glDetachShader,
    glDisable,
    glDrawArrays,
    glDrawBuffers,
    glEnableVertexAttribArray,
    glFramebufferTexture2D,
    glGenBuffers,
    glGenFramebuffers,
    glGenTextures,
    glGenVertexArrays,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glTexImage2D,
    glTexParameteri,
    glUniform1f,
    glUniform2f,
    glUniform3f,
    glUniformMatrix4fv,
    glUniform1i,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)
import numpy as np

from engine.graphics.passes.base_pass import BasePass


class SurfaceGBufferPass(BasePass):
    def __init__(self):
        super().__init__("Surface G-Buffer Pass")
        self.resources = {}
        self.program = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        self.textures = {}

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

    def _allocate_textures(self, width, height):
        formats = {
            "gbuffer_depth": (GL_R32F, GL_RED, GL_FLOAT),
            "gbuffer_normal_roughness": (GL_RGBA16F, GL_RGBA, GL_FLOAT),
            "gbuffer_albedo_metalness": (GL_RGBA16F, GL_RGBA, GL_FLOAT),
        }
        for name, (internal, fmt, t) in formats.items():
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(GL_TEXTURE_2D, 0, internal, width, height, 0, fmt, t, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            self.textures[name] = tex
        glBindTexture(GL_TEXTURE_2D, 0)

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out float o_depth;
layout(location = 1) out vec4 o_normal_roughness;
layout(location = 2) out vec4 o_albedo_metalness;

uniform mat4 u_inv_view_proj;
uniform vec2 u_resolution;
uniform vec3 u_sphere_center;
uniform float u_sphere_radius;
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
        if (d < 0.0005) {
            hit_pos = p;
            return t;
        }
        t += d;
        if (t > 200.0) break;
    }
    return -1.0;
}

vec3 albedo_for_point(vec3 p, vec3 normal) {
    float band = smoothstep(-0.1, 0.1, sin(p.y * 2.0 + u_time * 0.5));
    vec3 base = mix(vec3(0.35, 0.4, 0.6), vec3(0.6, 0.65, 0.7), band);
    float facing = 0.5 + 0.5 * normal.y;
    return mix(base, vec3(0.8, 0.85, 0.9), facing * 0.3);
}

void main() {
    vec3 ro = vec3(0.0);
    vec3 rd = reconstruct_direction(gl_FragCoord.xy);
    vec3 hit_pos = vec3(0.0);
    float t = march(ro, rd, hit_pos);
    if (t < 0.0) {
        o_depth = 1e30;
        o_normal_roughness = vec4(0.0, 0.0, 1.0, 1.0);
        o_albedo_metalness = vec4(0.0);
        return;
    }
    vec3 normal = estimate_normal(hit_pos);
    vec3 albedo = albedo_for_point(hit_pos, normal);
    float roughness = mix(0.15, 0.6, clamp(hit_pos.y * 0.2 + 0.5, 0.0, 1.0));
    o_depth = t;
    o_normal_roughness = vec4(normal * 0.5 + 0.5, roughness);
    o_albedo_metalness = vec4(albedo, 0.05);
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        width = int(render_context.width)
        height = int(render_context.height)
        self.program = self._create_program()
        self._create_fullscreen_quad()
        self._allocate_textures(width, height)
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textures["gbuffer_depth"], 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, self.textures["gbuffer_normal_roughness"], 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D, self.textures["gbuffer_albedo_metalness"], 0)
        glDrawBuffers([GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2])
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.resources = {"shader_sources": {"vertex": self.fullscreen_vertex, "fragment": self._fragment_shader()}}
        for name, tex in self.textures.items():
            render_context.set_texture(name, {"id": tex, "target": GL_TEXTURE_2D})
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        width = int(render_context.width)
        height = int(render_context.height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, width, height)
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.program)
        inv_view_proj = render_context.inv_view_proj.astype(np.float32)
        glUniformMatrix4fv(glGetUniformLocation(self.program, "u_inv_view_proj"), 1, False, inv_view_proj)
        glUniform2f(glGetUniformLocation(self.program, "u_resolution"), float(width), float(height))
        center = render_context.planet_center_rel.astype(np.float32)
        glUniform3f(glGetUniformLocation(self.program, "u_sphere_center"), center[0], center[1], center[2])
        glUniform1f(glGetUniformLocation(self.program, "u_sphere_radius"), float(render_context.planet_radius))
        glUniform1f(glGetUniformLocation(self.program, "u_time"), float(render_context.time))
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        for name, tex in self.textures.items():
            render_context.set_texture(name, {"id": tex, "target": GL_TEXTURE_2D})
        return True

    def shutdown(self):
        super().shutdown()
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.program:
            glDeleteProgram(self.program)
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
        if self.textures:
            glDeleteTextures(list(self.textures.values()))
        self.resources = {}
        self.shader_sources = {}
        self.textures = {}
        self.program = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        return True
