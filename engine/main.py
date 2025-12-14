import sys
from pathlib import Path

import glfw
import numpy as np
from OpenGL import GL as gl

from .camera import Camera
from .framebuffer import Framebuffer
from .shader import ShaderProgram
from .window import Window


def main():
    window = Window(1280, 720, "YAWS3 Minimal Renderer")
    vao = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(vao)
    gl.glDisable(gl.GL_FRAMEBUFFER_SRGB)
    gl.glEnable(gl.GL_DEPTH_TEST)

    shader_root = Path(__file__).resolve().parent / "shaders"
    sdf_shader = ShaderProgram(shader_root / "fullscreen.vert", shader_root / "sdf_sphere.frag")
    blit_shader = ShaderProgram(shader_root / "fullscreen.vert", shader_root / "blit.frag")

    fb_width, fb_height = window.get_framebuffer_size()
    framebuffer = Framebuffer(fb_width, fb_height)

    camera = Camera((0.0, 0.0, 5.0), 60.0)
    last_time = glfw.get_time()
    last_cursor = glfw.get_cursor_pos(window.handle)
    move_speed = 100.0
    look_sensitivity = 0.0025
    sphere_radius = 1.0

    while not window.should_close():
        window.poll()
        now = glfw.get_time()
        dt = max(1e-6, now - last_time)
        last_time = now

        cursor = glfw.get_cursor_pos(window.handle)
        if last_cursor is not None:
            dx = (cursor[0] - last_cursor[0]) * look_sensitivity
            dy = (cursor[1] - last_cursor[1]) * look_sensitivity
            camera.update_orientation(dx, -dy)
        last_cursor = cursor

        forward, right, up = camera.basis()
        velocity = np.zeros(3, dtype=np.float64)
        if glfw.get_key(window.handle, glfw.KEY_W) == glfw.PRESS:
            velocity += forward
        if glfw.get_key(window.handle, glfw.KEY_S) == glfw.PRESS:
            velocity -= forward
        if glfw.get_key(window.handle, glfw.KEY_A) == glfw.PRESS:
            velocity -= right
        if glfw.get_key(window.handle, glfw.KEY_D) == glfw.PRESS:
            velocity += right
        if glfw.get_key(window.handle, glfw.KEY_SPACE) == glfw.PRESS:
            velocity += up
        if glfw.get_key(window.handle, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
            velocity -= up
        if np.linalg.norm(velocity) > 0.0:
            velocity = velocity / np.linalg.norm(velocity)
            camera.position += velocity * move_speed * dt

        fb_width, fb_height = window.get_framebuffer_size()
        framebuffer.resize(fb_width, fb_height)
        aspect = fb_width / max(1.0, fb_height)
        inv_view_proj = camera.inv_view_proj(aspect)

        framebuffer.bind()
        gl.glViewport(0, 0, fb_width, fb_height)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        sdf_shader.use()
        sdf_shader.set_matrix4("invViewProj", inv_view_proj)
        sdf_shader.set_float("sphereRadius", sphere_radius)
        sdf_shader.set_vector2("resolution", (fb_width, fb_height))
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
        framebuffer.unbind()

        gl.glViewport(0, 0, fb_width, fb_height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDisable(gl.GL_DEPTH_TEST)
        blit_shader.use()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, framebuffer.color)
        blit_shader.set_int("colorTex", 0)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
        gl.glEnable(gl.GL_DEPTH_TEST)

        glfw.swap_buffers(window.handle)

        if glfw.get_key(window.handle, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window.handle, 1)

    window.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc)
        sys.exit(1)
