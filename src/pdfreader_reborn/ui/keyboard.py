# src/pdfreader_reborn/ui/keyboard.py

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtGui import QKeyEvent, QKeySequence

from pdfreader_reborn.ui.signals import AppSignals

# Explicit key name table — avoids chr() on arbitrary Qt.Key values
_KEY_NAMES: dict[int, str] = {
    Qt.Key.Key_Equal: "=",
    Qt.Key.Key_Plus: "+",
    Qt.Key.Key_Minus: "-",
    Qt.Key.Key_A: "A",
    Qt.Key.Key_B: "B",
    Qt.Key.Key_C: "C",
    Qt.Key.Key_D: "D",
    Qt.Key.Key_E: "E",
    Qt.Key.Key_F: "F",
    Qt.Key.Key_G: "G",
    Qt.Key.Key_H: "H",
    Qt.Key.Key_I: "I",
    Qt.Key.Key_J: "J",
    Qt.Key.Key_K: "K",
    Qt.Key.Key_L: "L",
    Qt.Key.Key_M: "M",
    Qt.Key.Key_N: "N",
    Qt.Key.Key_O: "O",
    Qt.Key.Key_P: "P",
    Qt.Key.Key_Q: "Q",
    Qt.Key.Key_R: "R",
    Qt.Key.Key_S: "S",
    Qt.Key.Key_T: "T",
    Qt.Key.Key_U: "U",
    Qt.Key.Key_V: "V",
    Qt.Key.Key_W: "W",
    Qt.Key.Key_X: "X",
    Qt.Key.Key_Y: "Y",
    Qt.Key.Key_Z: "Z",
    Qt.Key.Key_0: "0",
    Qt.Key.Key_1: "1",
    Qt.Key.Key_2: "2",
    Qt.Key.Key_3: "3",
    Qt.Key.Key_4: "4",
    Qt.Key.Key_5: "5",
    Qt.Key.Key_6: "6",
    Qt.Key.Key_7: "7",
    Qt.Key.Key_8: "8",
    Qt.Key.Key_9: "9",
    Qt.Key.Key_Space: "Space",
    Qt.Key.Key_Return: "Return",
    Qt.Key.Key_Enter: "Enter",
    Qt.Key.Key_Escape: "Escape",
    Qt.Key.Key_Tab: "Tab",
    Qt.Key.Key_Backspace: "Backspace",
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_F1: "F1",
    Qt.Key.Key_F2: "F2",
    Qt.Key.Key_F3: "F3",
    Qt.Key.Key_F4: "F4",
    Qt.Key.Key_F5: "F5",
    Qt.Key.Key_F6: "F6",
    Qt.Key.Key_F7: "F7",
    Qt.Key.Key_F8: "F8",
    Qt.Key.Key_F9: "F9",
    Qt.Key.Key_F10: "F10",
    Qt.Key.Key_F11: "F11",
    Qt.Key.Key_F12: "F12",
}


class _Signal:
    """Protocol-like wrapper for pyqt signals used in bindings.

    Provides type-safe emit() without depending on pyqtBoundSignal
    internals, which vary across PyQt6 versions.
    """

    __slots__ = ("_signal",)

    def __init__(self, signal: object) -> None:
        self._signal = signal

    def emit(self) -> None:
        """Emit the wrapped signal."""
        self._signal.emit()  # type: ignore[union-attr]


class KeyboardManager(QObject):
    """Maps keyboard shortcuts to application signals.

    Uses an explicit key name table for cross-platform consistency.
    All key-to-string conversion avoids chr() on raw Qt.Key values,
    which can produce ValueError for special keys.

    Usage::

        signals = AppSignals()
        km = KeyboardManager(signals)
        km.handle_key_press(key_event)
    """

    def __init__(self, signals: AppSignals) -> None:
        """Initialize the keyboard manager with default bindings.

        Args:
            signals: The application signal hub to emit signals on.
        """
        super().__init__()
        self._signals = signals
        self._bindings: dict[str, _Signal] = {
            "Ctrl+=": _Signal(signals.zoom_in),
            "Ctrl++": _Signal(signals.zoom_in),
            "Ctrl+-": _Signal(signals.zoom_out),
            "Ctrl+O": _Signal(signals.open_file),
            "Ctrl+W": _Signal(signals.close_document),
        }

    @property
    def bindings(self) -> dict[str, _Signal]:
        """Return a copy of the current key-to-signal bindings."""
        return dict(self._bindings)

    def bind(self, key: str, signal: object) -> None:
        """Bind a keyboard shortcut to a signal.

        Args:
            key: Key combination string (e.g., "Ctrl+Z").
            signal: The signal to emit when the key is pressed.
        """
        self._bindings[key] = _Signal(signal)

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
        """Convert a QKeyEvent to a canonical string representation.

        Uses an explicit key name table instead of chr() to avoid
        ValueError on non-Unicode Qt.Key values and ensure consistent
        behavior across platforms.

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
        key_name = _KEY_NAMES.get(key)

        if key_name is None:
            seq = QKeySequence(key)
            key_name = seq.toString()

        if key_name:
            parts.append(key_name)

        return "+".join(parts)