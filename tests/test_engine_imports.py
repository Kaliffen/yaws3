from engine.core.application import Application
from engine.core.config import Config
from engine.core.lifecycle import Lifecycle
from engine.graphics.frame_graph import FrameGraph
from engine.graphics.renderer import Renderer
from engine.graphics.passes.base_pass import BasePass


def test_application_runs():
    app = Application()
    assert app.run() is True


def test_config_access():
    config = Config({"value": 1})
    assert config.get("value") == 1


def test_lifecycle_transitions():
    lifecycle = Lifecycle()
    lifecycle.start()
    lifecycle.stop()
    assert lifecycle.started is True and lifecycle.stopped is True


def test_frame_graph_tracks_passes():
    frame_graph = FrameGraph()
    render_pass = BasePass()
    frame_graph.add_pass(render_pass)
    assert render_pass in frame_graph.passes


def test_renderer_rendering():
    renderer = Renderer(FrameGraph())
    assert renderer.render() is True


def test_base_pass_executes():
    render_pass = BasePass()
    assert render_pass.execute() is True
