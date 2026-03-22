# tests/ui/test_keyboard.py

import pytest
from unittest.mock import Mock

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QKeyEvent

from pdfreader_reborn.ui.signals import AppSignals
from pdfreader_reborn.ui.keyboard import KeyboardManager


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for keyboard tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def signals(qapp: QApplication) -> AppSignals:
    """Create an AppSignals instance for testing."""
    return AppSignals()


@pytest.fixture
def km(signals: AppSignals) -> KeyboardManager:
    """Create a KeyboardManager instance for testing."""
    return KeyboardManager(signals)


class TestKeyboardManager:
    """Tests for the KeyboardManager class."""

    def test_has_default_bindings(self, km: KeyboardManager) -> None:
        """KeyboardManager should have default bindings."""
        bindings = km.bindings
        assert "Ctrl+=" in bindings
        assert "Ctrl++" in bindings
        assert "Ctrl+-" in bindings
        assert "Ctrl+O" in bindings
        assert "Ctrl+W" in bindings

    def test_bind_custom_key(self, km: KeyboardManager) -> None:
        """bind() should add a new key binding."""
        mock_signal = Mock()
        km.bind("Ctrl+Z", mock_signal)
        assert "Ctrl+Z" in km.bindings

    def test_unbind_key(self, km: KeyboardManager) -> None:
        """unbind() should remove a key binding."""
        km.unbind("Ctrl+=")
        assert "Ctrl+=" not in km.bindings

    def test_unbind_nonexistent_raises(self, km: KeyboardManager) -> None:
        """unbind() should raise KeyError for unbound keys."""
        with pytest.raises(KeyError, match="Key not bound"):
            km.unbind("Ctrl+Z")

    def test_handle_ctrl_equals_emits_zoom_in(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Ctrl+= key press should emit zoom_in signal."""
        callback = Mock()
        signals.zoom_in.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Equal,
            Qt.KeyboardModifier.ControlModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is True
        callback.assert_called_once()

    def test_handle_ctrl_plus_emits_zoom_in(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Ctrl++ key press should emit zoom_in signal."""
        callback = Mock()
        signals.zoom_in.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Plus,
            Qt.KeyboardModifier.ControlModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is True
        callback.assert_called_once()

    def test_handle_ctrl_minus_emits_zoom_out(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Ctrl+- key press should emit zoom_out signal."""
        callback = Mock()
        signals.zoom_out.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Minus,
            Qt.KeyboardModifier.ControlModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is True
        callback.assert_called_once()

    def test_handle_ctrl_o_emits_open_file(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Ctrl+O key press should emit open_file signal."""
        callback = Mock()
        signals.open_file.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_O,
            Qt.KeyboardModifier.ControlModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is True
        callback.assert_called_once()

    def test_handle_ctrl_w_emits_close_document(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Ctrl+W key press should emit close_document signal."""
        callback = Mock()
        signals.close_document.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_W,
            Qt.KeyboardModifier.ControlModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is True
        callback.assert_called_once()

    def test_handle_unbound_key_returns_false(self, km: KeyboardManager) -> None:
        """Unbound key press should return False."""
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_X,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is False

    def test_handle_key_does_not_emit_for_unbound(
        self, km: KeyboardManager, signals: AppSignals
    ) -> None:
        """Unbound key should not emit any signal."""
        callback = Mock()
        signals.zoom_in.connect(callback)
        signals.zoom_out.connect(callback)
        signals.open_file.connect(callback)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_X,
            Qt.KeyboardModifier.NoModifier,
        )
        km.handle_key_press(event)
        callback.assert_not_called()

    def test_special_key_does_not_crash(self, km: KeyboardManager) -> None:
        """Special keys like Escape should not raise ValueError."""
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is False  # Not bound, but should not crash

    def test_function_key_does_not_crash(self, km: KeyboardManager) -> None:
        """Function keys should be handled without errors."""
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_F5,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = km.handle_key_press(event)
        assert handled is False