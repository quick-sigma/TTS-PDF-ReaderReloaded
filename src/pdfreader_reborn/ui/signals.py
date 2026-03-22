from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Central signal hub for application-wide events.

    All UI actions that can be triggered by multiple sources (buttons,
    keyboard shortcuts, menus) are defined here as signals. This decouples
    the trigger from the handler, allowing any source to emit the same signal.

    Usage::

        signals = AppSignals()
        signals.zoom_in.connect(viewer.zoom_in)
        signals.zoom_out.connect(viewer.zoom_out)
    """

    zoom_in = pyqtSignal()
    """Emitted when the user requests zoom in."""

    zoom_out = pyqtSignal()
    """Emitted when the user requests zoom out."""

    open_file = pyqtSignal()
    """Emitted when the user requests opening a file."""

    close_document = pyqtSignal()
    """Emitted when the user requests closing the current document."""
