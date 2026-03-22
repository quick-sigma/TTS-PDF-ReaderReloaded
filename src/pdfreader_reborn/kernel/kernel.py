from collections.abc import Sequence
from pathlib import Path

import pluggy

from pdfreader_reborn.kernel.hooks import ToolbarHooks
from pdfreader_reborn.ui.button import Button

PM_NAME = "pdfreader_reborn"


class Kernel:
    """Microkernel that manages plugins via pluggy.

    The kernel owns the plugin manager and dispatches hooks to all
    registered plugins. Plugins are standard Python classes that
    implement methods decorated with ``@hookimpl`` matching the
    hookspecs in :mod:`pdfreader_reborn.kernel.hooks`.

    Usage::

        kernel = Kernel()
        kernel.register_plugin(MyPlugin())
        buttons = kernel.get_toolbar_buttons(icons_dir)
    """

    def __init__(self) -> None:
        """Initialize the kernel with an empty plugin manager."""
        self._pm = pluggy.PluginManager(PM_NAME)
        self._pm.add_hookspecs(ToolbarHooks)

    def register_plugin(self, plugin: object) -> None:
        """Register a plugin with the manager.

        Args:
            plugin: An object implementing one or more hook methods.
        """
        self._pm.register(plugin)

    def unregister_plugin(self, plugin: object) -> None:
        """Unregister a previously registered plugin.

        Args:
            plugin: The plugin instance to remove.
        """
        self._pm.unregister(plugin)

    def get_toolbar_buttons(self, icons_dir: Path) -> Sequence[Button]:
        """Collect toolbar buttons from all registered plugins.

        Args:
            icons_dir: Path to the icon directory, passed to plugins.

        Returns:
            A flat list of Button instances contributed by plugins.
        """
        results = self._pm.hook.provide_toolbar_buttons(icons_dir=icons_dir)
        buttons: list[Button] = []
        for group in results:
            buttons.extend(group)
        return buttons
