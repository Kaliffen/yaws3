from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_COMPILE_STATUS,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRAMEBUFFER,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_LINK_STATUS,
    GL_RGBA,
    GL_RGBA16F,
    GL_STATIC_DRAW,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE2,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TRIANGLE_STRIP,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindBuffer,
    glBindFramebuffer,
    glBindTexture,
    glBindVertexArray,
    glBufferData,
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
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)
import numpy as np

from engine.graphics.passes.base_pass import BasePass


class DeferredSurfaceLightingPass(BasePass):
    def __init__(self):
        super().__init__("Deferred Surface Lighting Pass")
        self.resources = {}
        self.program = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        self.texture = None

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

    def _allocate_target(self, width, height):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, width, height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        glDrawBuffers([GL_COLOR_ATTACHMENT0])
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _fragment_shader(self):
        return """#version 330 core
layout(location = 0) out vec4 o_surface_radiance;

uniform sampler2D u_gbuffer_depth;
uniform sampler2D u_gbuffer_normal_roughness;
uniform sampler2D u_gbuffer_albedo_metalness;
uniform vec3 u_sun_dir_rel;
uniform vec2 u_resolution;
uniform mat4 u_inv_view_proj;
uniform float u_time;

vec3 reconstruct_direction(vec2 frag_coord) {
    vec2 ndc = (frag_coord / u_resolution) * 2.0 - 1.0;
    vec4 clip = vec4(ndc, 1.0, 1.0);
    vec4 view = u_inv_view_proj * clip;
    return normalize(view.xyz / view.w);
}

vec3 sky_color(vec3 dir) {
    float grad = clamp(dir.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 horizon = vec3(0.25, 0.35, 0.5);
    vec3 zenith = vec3(0.05, 0.08, 0.12);
    vec3 base = mix(horizon, zenith, grad);
    float sun = pow(max(dot(normalize(dir), normalize(u_sun_dir_rel)), 0.0), 32.0);
    return base + vec3(0.8, 0.7, 0.5) * sun;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float depth = texture(u_gbuffer_depth, uv).r;
    if (depth > 1e20) {
        vec3 dir = reconstruct_direction(gl_FragCoord.xy);
        o_surface_radiance = vec4(sky_color(dir), 1.0);
        return;
    }
    vec3 normal = normalize(texture(u_gbuffer_normal_roughness, uv).xyz * 2.0 - 1.0);
    float roughness = texture(u_gbuffer_normal_roughness, uv).w;
    vec3 albedo = texture(u_gbuffer_albedo_metalness, uv).rgb;
    vec3 dir = reconstruct_direction(gl_FragCoord.xy);
    vec3 position = dir * depth;
    vec3 light_dir = normalize(u_sun_dir_rel);
    vec3 view_dir = normalize(-dir);
    float ndl = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = albedo * ndl;
    vec3 half_vec = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, half_vec), 0.0), mix(80.0, 8.0, roughness));
    vec3 reflection = reflect(-view_dir, normal);
    vec3 reflection_sky = sky_color(reflection);
    float fresnel = pow(1.0 - max(dot(normal, view_dir), 0.0), 5.0);
    vec3 light_color = vec3(1.0, 0.95, 0.9);
    vec3 shading = diffuse * light_color + spec * light_color * (0.1 + 0.6 * (1.0 - roughness));
    shading += reflection_sky * fresnel;
    float air = exp(-depth * 0.02);
    vec3 aerial = sky_color(dir);
    vec3 color = mix(aerial, shading, air);
    float phase = 0.1 * sin(u_time * 0.25 + position.y);
    color += phase;
    o_surface_radiance = vec4(color, 1.0);
}
"""

    def initialize(self, render_context):
        super().initialize(render_context)
        width = int(render_context.width)
        height = int(render_context.height)
        self.program = self._create_program()
        self._create_fullscreen_quad()
        self._allocate_target(width, height)
        self.resources = {"shader_sources": {"vertex": self.fullscreen_vertex, "fragment": self._fragment_shader()}}
        render_context.set_texture("surface_radiance", {"id": self.texture, "target": GL_TEXTURE_2D})
        return True

    def execute(self, delta_time=0.0, render_context=None):
        super().execute(delta_time, render_context)
        width = int(render_context.width)
        height = int(render_context.height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, width, height)
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.program)
        glActiveTexture(GL_TEXTURE0)
        g_depth = render_context.get_texture("gbuffer_depth")
        glBindTexture(GL_TEXTURE_2D, g_depth.get("id"))
        glUniform1i(glGetUniformLocation(self.program, "u_gbuffer_depth"), 0)
        glActiveTexture(GL_TEXTURE1)
        g_normal = render_context.get_texture("gbuffer_normal_roughness")
        glBindTexture(GL_TEXTURE_2D, g_normal.get("id"))
        glUniform1i(glGetUniformLocation(self.program, "u_gbuffer_normal_roughness"), 1)
        glActiveTexture(GL_TEXTURE2)
        g_albedo = render_context.get_texture("gbuffer_albedo_metalness")
        glBindTexture(GL_TEXTURE_2D, g_albedo.get("id"))
        glUniform1i(glGetUniformLocation(self.program, "u_gbuffer_albedo_metalness"), 2)
        inv_view_proj = render_context.inv_view_proj.astype(np.float32)
        glUniformMatrix4fv(glGetUniformLocation(self.program, "u_inv_view_proj"), 1, False, inv_view_proj)
        glUniform2f(glGetUniformLocation(self.program, "u_resolution"), float(width), float(height))
        light = render_context.sun_dir_rel.astype(np.float32)
        glUniform3f(glGetUniformLocation(self.program, "u_sun_dir_rel"), light[0], light[1], light[2])
        glUniform1f(glGetUniformLocation(self.program, "u_time"), float(render_context.time))
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        render_context.set_texture("surface_radiance", {"id": self.texture, "target": GL_TEXTURE_2D})
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
        if self.texture:
            glDeleteTextures([self.texture])
        self.resources = {}
        self.shader_sources = {}
        self.program = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        self.texture = None
        return True
