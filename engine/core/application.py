"""Application entry point with headless-friendly lifecycle hooks.

The Application class deliberately avoids invoking GLFW/OpenGL on import
so the module can be imported within headless test environments. A
headless flag steers initialization logic for callers that need to skip
window or rendering setup entirely.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from engine.graphics.renderer import Renderer


@dataclass(frozen=True)
class ApplicationMode:
    """Describes execution behavior for the application.

    Attributes:
        headless: When ``True`` the renderer will avoid any calls that
            require a graphics context or display surface.
    """

    headless: bool = False

    @staticmethod
    def from_env(default: bool = False) -> "ApplicationMode":
        """Create a mode using the ``HEADLESS`` environment flag.

        The environment variable is treated as truthy when set to any of
        ``{"1", "true", "yes"}`` (case-insensitive).
        """

        import os

        value = os.environ.get("HEADLESS")
        if value is None:
            return ApplicationMode(headless=default)
        normalized = value.strip().lower()
        return ApplicationMode(headless=normalized in {"1", "true", "yes"})


class Application:
    """Coordinates renderer lifecycle while respecting headless mode."""

    def __init__(self, mode: Optional[ApplicationMode] = None) -> None:
        self.mode = mode or ApplicationMode()
        # Renderer avoids GL-sensitive work when headless is true.
        self.renderer = Renderer(headless=self.mode.headless)

    def initialize(self) -> None:
        """Perform initialization.

        In headless mode the method returns immediately because there is
        no window or GL context to create yet. The non-headless path is
        intentionally a placeholder until windowing is introduced.
        """

        if self.mode.headless:
            return
        raise RuntimeError("Windowed initialization is not yet implemented.")

    def run(self) -> None:
        """Run a single headless frame.

        A minimal loop placeholder keeps future expansion simple while
        providing a deterministic hook for tests.
        """

        if self.mode.headless:
            self.renderer.render_headless_frame()
            return
        raise RuntimeError("Windowed execution is not yet implemented.")

    def shutdown(self) -> None:
        """Shut down renderer resources."""

        self.renderer.shutdown()
