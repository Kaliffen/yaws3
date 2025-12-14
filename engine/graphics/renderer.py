"""Headless-friendly renderer scaffolding.

The renderer avoids importing or touching OpenGL/GLFW at module import
so it is safe to load in CI environments lacking a display server.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RendererConfig:
    headless: bool = False


class Renderer:
    """Minimal renderer placeholder with explicit headless mode."""

    def __init__(self, headless: bool = False) -> None:
        self.config = RendererConfig(headless=headless)
        self._has_rendered = False

    @property
    def headless(self) -> bool:
        return self.config.headless

    def render_headless_frame(self) -> None:
        """Record that a frame would have rendered without GL usage."""

        if not self.headless:
            raise RuntimeError("Headless rendering invoked while headless disabled.")
        self._has_rendered = True

    @property
    def has_rendered(self) -> bool:
        """Expose whether a frame has been processed."""

        return self._has_rendered

    def shutdown(self) -> None:
        """Placeholder for releasing renderer resources."""

        self._has_rendered = False
