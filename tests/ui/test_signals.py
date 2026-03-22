import pytest
from unittest.mock import Mock

from PyQt6.QtWidgets import QApplication

from pdfreader_reborn.ui.signals import AppSignals


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for signal tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestAppSignals:
    """Tests for the AppSignals signal hub."""

    def test_signals_has_zoom_in(self, qapp: QApplication) -> None:
        """AppSignals should have a zoom_in signal."""
        signals = AppSignals()
        assert hasattr(signals, "zoom_in")

    def test_signals_has_zoom_out(self, qapp: QApplication) -> None:
        """AppSignals should have a zoom_out signal."""
        signals = AppSignals()
        assert hasattr(signals, "zoom_out")

    def test_signals_has_open_file(self, qapp: QApplication) -> None:
        """AppSignals should have an open_file signal."""
        signals = AppSignals()
        assert hasattr(signals, "open_file")

    def test_signals_has_close_document(self, qapp: QApplication) -> None:
        """AppSignals should have a close_document signal."""
        signals = AppSignals()
        assert hasattr(signals, "close_document")

    def test_zoom_in_emits_to_connected_slot(self, qapp: QApplication) -> None:
        """zoom_in signal should call connected slots."""
        signals = AppSignals()
        callback = Mock()
        signals.zoom_in.connect(callback)
        signals.zoom_in.emit()
        callback.assert_called_once()

    def test_zoom_out_emits_to_connected_slot(self, qapp: QApplication) -> None:
        """zoom_out signal should call connected slots."""
        signals = AppSignals()
        callback = Mock()
        signals.zoom_out.connect(callback)
        signals.zoom_out.emit()
        callback.assert_called_once()

    def test_multiple_slots_receive_signal(self, qapp: QApplication) -> None:
        """Multiple slots can connect to the same signal."""
        signals = AppSignals()
        callback1 = Mock()
        callback2 = Mock()
        signals.zoom_in.connect(callback1)
        signals.zoom_in.connect(callback2)
        signals.zoom_in.emit()
        callback1.assert_called_once()
        callback2.assert_called_once()
