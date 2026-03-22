from collections.abc import Callable, Sequence
from pathlib import Path

import pluggy

from pdfreader_reborn.ui.button import Button
from pdfreader_reborn.ui.icon import SVGIcon

hookimpl = pluggy.HookimplMarker("pdfreader_reborn")


class OpenFilePlugin:
    """Built-in plugin that contributes the Open PDF button.

    This plugin implements the ``provide_toolbar_buttons`` hook and
    returns a single "Open PDF" button. Its callback emits the
    ``open_file`` signal, which must be connected by the application.

    Usage::

        kernel = Kernel()
        kernel.register_plugin(OpenFilePlugin(on_open=open_file))
    """

    def __init__(self, on_open: Callable[[], None] | None = None) -> None:
        """Initialize with an optional open-file callback.

        Args:
            on_open: A callable invoked when the Open PDF button is clicked.
        """
        self._on_open = on_open

    @hookimpl
    def provide_toolbar_buttons(
        self,
        icons_dir: Path,
    ) -> Sequence[Button]:
        """Return the Open PDF button as the first toolbar element.

        Args:
            icons_dir: Path to the directory containing icon files.

        Returns:
            A list with a single Button for opening PDF files.
        """
        return [
            Button(
                icon=SVGIcon(icons_dir / "openFile.svg"),
                label="Open PDF",
                tooltip="Open PDF file (Ctrl+O)",
                on_click=self._on_open,
            ),
        ]
