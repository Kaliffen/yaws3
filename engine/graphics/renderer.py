import numpy as np

from engine.graphics.frame_graph import FrameGraph
from engine.graphics.render_context import RenderContext
from engine.graphics.passes import (
    CompositeTonemapPass,
    DeferredSurfaceLightingPass,
    SurfaceGBufferPass,
)


class Renderer:
    def __init__(self, frame_graph=None, enable_gl=True):
        self.frame_graph = frame_graph or FrameGraph()
        self.render_context = RenderContext(width=1, height=1,
                                            planet_radius=2.5,
                                            atm_inner_radius=2.5,
                                            atm_outer_radius=3.0)
        self.initialized = False
        self.enable_gl = enable_gl

    def initialize(self, width=1, height=1):
        if self.initialized:
            return True
        if not self.enable_gl:
            self.initialized = True
            return True
        self.render_context.width = width
        self.render_context.height = height
        self._build_passes()
        self.frame_graph.initialize(self.render_context)
        self.initialized = True
        return True

    def _build_passes(self):
        self.frame_graph.passes = []
        self.frame_graph.add_pass(SurfaceGBufferPass())
        self.frame_graph.add_pass(DeferredSurfaceLightingPass())
        self.frame_graph.add_pass(CompositeTonemapPass())

    def render(self, delta_time=0.0, camera=None, planet_center=None):
        if not self.initialized:
            self.initialize()
        self.render_context.update_time(delta_time)
        if camera is not None:
            self.render_context.update_camera(
                camera, planet_center=planet_center,
                width=self.render_context.width,
                height=self.render_context.height,
            )
        if not self.enable_gl:
            return True
        self.frame_graph.execute(delta_time, self.render_context)
        return True

    def shutdown(self):
        if self.enable_gl:
            self.frame_graph.shutdown()
        self.initialized = False
        return True
