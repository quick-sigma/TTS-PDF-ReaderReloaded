from collections.abc import Sequence
from pathlib import Path

import pluggy
from PyQt6.QtWidgets import QToolBar

from pdfreader_reborn.ui.button import Button

hookspec = pluggy.HookspecMarker("pdfreader_reborn")


class ToolbarHooks:
    """Hook specifications for toolbar contributions by plugins."""

    @hookspec
    def provide_toolbar_buttons(
        self,
        icons_dir: Path,
    ) -> Sequence[Button]:
        """Return toolbar buttons that the plugin wants to contribute.

        Plugins implementing this hook can add buttons to the navigation
        toolbar. Buttons are prepended in plugin registration order before
        any built-in toolbar elements (zoom controls, etc.).

        Args:
            icons_dir: Path to the directory containing icon files.

        Returns:
            A sequence of Button instances to add to the toolbar.
        """
