import importlib
import os
import sys
from types import ModuleType

import pytest


def test_modules_import_without_gl_context(monkeypatch):
    """Engine modules should import without touching GLFW/OpenGL."""

    class GuardModule(ModuleType):
        def __getattr__(self, name):  # pragma: no cover - defensive
            raise RuntimeError(f"Access to {name} is not allowed during import")

    # Inject guard modules to ensure imports avoid GLFW/GL until used.
    monkeypatch.setitem(sys.modules, "glfw", GuardModule("glfw"))
    monkeypatch.setitem(sys.modules, "OpenGL", GuardModule("OpenGL"))

    import engine.core.application
    import engine.graphics.renderer

    importlib.reload(engine.core.application)
    importlib.reload(engine.graphics.renderer)


def test_application_respects_headless_env(monkeypatch):
    from engine.core.application import Application, ApplicationMode

    monkeypatch.setenv("HEADLESS", "1")
    app = Application(ApplicationMode.from_env())

    app.initialize()
    app.run()

    assert app.renderer.has_rendered is True
    app.shutdown()
    assert app.renderer.has_rendered is False


def test_renderer_guardrails():
    from engine.graphics.renderer import Renderer

    renderer = Renderer(headless=True)
    renderer.render_headless_frame()
    assert renderer.has_rendered is True

    renderer.shutdown()
    assert renderer.has_rendered is False

    non_headless = Renderer(headless=False)
    with pytest.raises(RuntimeError):
        non_headless.render_headless_frame()
