from collections.abc import Callable

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent

from pdfreader_reborn.ui.signals import AppSignals


class KeyboardManager(QObject):
    """Maps keyboard shortcuts to application signals.

    Provides an abstract key-to-signal mapping that decouples keyboard
    input from application logic. Each key combination is stored as a
    string (e.g., "Ctrl+=") and maps to a signal that can have multiple
    connected handlers.

    Usage::

        signals = AppSignals()
        km = KeyboardManager(signals)
        km.handle_key_press(key_event)
    """

    def __init__(self, signals: AppSignals) -> None:
        """Initialize the keyboard manager.

        Args:
            signals: The application signal hub to emit signals on.
        """
        super().__init__()
        self._signals = signals
        self._bindings: dict[str, object] = {
            "Ctrl+=": signals.zoom_in,
            "Ctrl++": signals.zoom_in,
            "Ctrl+-": signals.zoom_out,
            "Ctrl+O": signals.open_file,
            "Ctrl+W": signals.close_document,
        }

    @property
    def bindings(self) -> dict[str, object]:
        """Return the current key-to-signal bindings."""
        return dict(self._bindings)

    def bind(self, key: str, signal: object) -> None:
        """Bind a keyboard shortcut to a signal.

        Args:
            key: Key combination string (e.g., "Ctrl+Z").
            signal: The signal to emit when the key is pressed.
        """
        self._bindings[key] = signal

    def unbind(self, key: str) -> None:
        """Remove a keyboard binding.

        Args:
            key: Key combination string to unbind.

        Raises:
            KeyError: If the key is not bound.
        """
        if key not in self._bindings:
            msg = f"Key not bound: {key}"
            raise KeyError(msg)
        del self._bindings[key]

    def handle_key_press(self, event: QKeyEvent) -> bool:
        """Process a key press event and emit the corresponding signal.

        Args:
            event: The Qt key event to process.

        Returns:
            True if the key was handled, False otherwise.
        """
        key_str = self._key_event_to_string(event)
        if key_str in self._bindings:
            self._bindings[key_str].emit()
            return True
        return False

    def _key_event_to_string(self, event: QKeyEvent) -> str:
        """Convert a QKeyEvent to a human-readable string.

        Args:
            event: The Qt key event.

        Returns:
            A string like "Ctrl+=" or "Ctrl+Shift+Z".
        """
        parts: list[str] = []
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")

        key = event.key()
        text = event.text()
        if text and text.isprintable():
            parts.append(text)
        else:
            parts.append(chr(key))

        return "+".join(parts)
