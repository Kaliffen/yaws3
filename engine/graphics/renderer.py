import numpy as np

from engine.graphics.frame_graph import FrameGraph
from engine.graphics.render_context import RenderContext
from engine.graphics.passes.planetary_depth_geometry_pass import PlanetaryDepthGeometryPass
from engine.graphics.passes.atmospheric_entry_cache_pass import AtmosphericEntryCachePass
from engine.graphics.passes.cloud_lighting_pass import CloudLightingPass
from engine.graphics.passes.surface_gbuffer_pass import SurfaceGBufferPass
from engine.graphics.passes.deferred_surface_lighting_pass import DeferredSurfaceLightingPass
from engine.graphics.passes.atmospheric_integration_pass import AtmosphericIntegrationPass
from engine.graphics.passes.composite_tonemap_pass import CompositeTonemapPass


class Renderer:
    def __init__(self, frame_graph=None):
        self.frame_graph = frame_graph or FrameGraph()
        self.render_context = None
        self.initialized = False

    def initialize(self):
        self._build_passes()
        self.render_context = self._build_render_context()
        self.frame_graph.initialize(self.render_context)
        self.initialized = True
        return True

    def _build_passes(self):
        self.frame_graph.passes = []
        self.frame_graph.add_pass(PlanetaryDepthGeometryPass())
        self.frame_graph.add_pass(AtmosphericEntryCachePass())
        self.frame_graph.add_pass(CloudLightingPass())
        self.frame_graph.add_pass(SurfaceGBufferPass())
        self.frame_graph.add_pass(DeferredSurfaceLightingPass())
        self.frame_graph.add_pass(AtmosphericIntegrationPass())
        self.frame_graph.add_pass(CompositeTonemapPass())

    def _build_render_context(self):
        inv_view_proj = np.identity(4, dtype=np.float32)
        sun_dir_rel = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return RenderContext(width=1, height=1, inv_view_proj=inv_view_proj,
                             sun_dir_rel=sun_dir_rel, planet_radius=6371000.0,
                             atm_inner_radius=6371000.0, atm_outer_radius=6421000.0)

    def render(self, delta_time=0.0):
        if not self.initialized:
            self.initialize()
        self.render_context.update_time(delta_time)
        self.frame_graph.execute(delta_time, self.render_context)
        return True

    def shutdown(self):
        self.frame_graph.shutdown()
        self.initialized = False
        return True
