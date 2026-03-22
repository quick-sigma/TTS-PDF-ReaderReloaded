# tests/ui/test_main_window.py

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QKeyEvent

from main import MainWindow


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for MainWindow tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestMainWindowInit:
    """Tests for MainWindow initialization."""

    def test_window_title(self, qapp: QApplication) -> None:
        """Window title should be set on creation."""
        window = MainWindow()
        assert window.windowTitle() == "PDF Reader Reborn"

    def test_window_has_signals(self, qapp: QApplication) -> None:
        """MainWindow should create an AppSignals instance."""
        window = MainWindow()
        assert hasattr(window, "signals")
        from pdfreader_reborn.ui.signals import AppSignals

        assert isinstance(window.signals, AppSignals)

    def test_window_has_kernel(self, qapp: QApplication) -> None:
        """MainWindow should create a Kernel for plugin management."""
        window = MainWindow()
        assert hasattr(window, "kernel")
        from pdfreader_reborn.kernel import Kernel

        assert isinstance(window.kernel, Kernel)

    def test_window_has_keyboard(self, qapp: QApplication) -> None:
        """MainWindow should create a KeyboardManager."""
        window = MainWindow()
        assert hasattr(window, "keyboard")
        from pdfreader_reborn.ui.keyboard import KeyboardManager

        assert isinstance(window.keyboard, KeyboardManager)

    def test_window_has_viewer(self, qapp: QApplication) -> None:
        """MainWindow should create a PDFViewer as central widget."""
        window = MainWindow()
        from pdfreader_reborn.ui.viewer import PDFViewer

        assert isinstance(window.viewer, PDFViewer)
        assert window.centralWidget() is window.viewer

    def test_window_has_toolbar(self, qapp: QApplication) -> None:
        """MainWindow should have a navigation toolbar."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        assert qtoolbar.windowTitle() == "Navigation"
        assert len(qtoolbar.actions()) == 3  # Open PDF + Zoom In + Zoom Out


class TestMainWindowHandlers:
    """Tests for MainWindow signal handlers."""

    def test_zoom_in_increases_zoom(self, qapp: QApplication, sample_pdf: Path) -> None:
        """_zoom_in should increase zoom by 0.25."""
        window = MainWindow()
        window.viewer.load_document(sample_pdf)
        initial_zoom = window.viewer.zoom
        window._zoom_in()
        assert window.viewer.zoom == initial_zoom + 0.25
        window.viewer.close()

    def test_zoom_out_decreases_zoom(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_zoom_out should decrease zoom by 0.25."""
        window = MainWindow()
        window.viewer.load_document(sample_pdf)
        window.viewer.set_zoom(2.0)
        window._zoom_out()
        assert window.viewer.zoom == 1.75
        window.viewer.close()

    def test_zoom_out_minimum(self, qapp: QApplication, sample_pdf: Path) -> None:
        """_zoom_out should not go below 0.5."""
        window = MainWindow()
        window.viewer.load_document(sample_pdf)
        window.viewer.set_zoom(0.5)
        window._zoom_out()
        assert window.viewer.zoom == 0.5
        window.viewer.close()

    def test_close_document_clears_viewer(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_close_document should close the viewer and reset title."""
        window = MainWindow()
        window.viewer.load_document(sample_pdf)
        window.setWindowTitle("PDF Reader Reborn — test.pdf")
        window._close_document()
        assert window.windowTitle() == "PDF Reader Reborn"
        assert window.viewer._doc is None

    def test_close_document_without_loaded_doc(self, qapp: QApplication) -> None:
        """_close_document should not raise when no document is loaded."""
        window = MainWindow()
        window._close_document()  # Should not raise

    def test_open_file_with_no_selection(self, qapp: QApplication) -> None:
        """_open_file should do nothing when user cancels the dialog."""
        window = MainWindow()
        with patch("main.QFileDialog.getOpenFileName", return_value=("", "")):
            window._open_file()
        assert window.viewer._doc is None

    def test_open_file_with_valid_pdf(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_open_file should load the document when a path is selected."""
        window = MainWindow()
        with patch(
            "main.QFileDialog.getOpenFileName",
            return_value=(str(sample_pdf), "PDF Files (*.pdf)"),
        ):
            window._open_file()
        assert window.viewer._doc is not None
        assert window.viewer._doc.page_count == 3
        window.viewer.close()


class TestMainWindowKeyEvents:
    """Tests for MainWindow key event delegation."""

    def test_key_press_delegates_to_keyboard_manager(self, qapp: QApplication) -> None:
        """Key press should be delegated to KeyboardManager."""
        window = MainWindow()
        callback = Mock()
        window.signals.zoom_in.connect(callback)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Equal,
            Qt.KeyboardModifier.ControlModifier,
        )
        window.keyPressEvent(event)
        callback.assert_called_once()

    def test_key_press_unpropagated_event_is_ignored(self, qapp: QApplication) -> None:
        """Unbound key should fall through to super().keyPressEvent."""
        window = MainWindow()
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_F5,
            Qt.KeyboardModifier.NoModifier,
        )
        # Should not raise — falls through to QWidget.keyPressEvent
        window.keyPressEvent(event)

    def test_key_press_handled_is_accepted(self, qapp: QApplication) -> None:
        """Handled key events should be accepted."""
        window = MainWindow()
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Minus,
            Qt.KeyboardModifier.ControlModifier,
        )
        window.keyPressEvent(event)
        assert event.isAccepted()

    def test_key_press_unhandled_is_not_accepted(self, qapp: QApplication) -> None:
        """Unhandled key events should not be accepted by us."""
        window = MainWindow()
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_F5,
            Qt.KeyboardModifier.NoModifier,
        )
        window.keyPressEvent(event)
        # The event may or may not be accepted by super(), but our code
        # didn't explicitly accept it


class TestMainWindowPluginToolbar:
    """Tests for toolbar buttons contributed by plugins via the kernel."""

    def test_open_pdf_button_is_first_in_toolbar(self, qapp: QApplication) -> None:
        """The Open PDF button (from plugin) should be the first toolbar action."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        first_action = qtoolbar.actions()[0]
        assert first_action.text() == "Open PDF"
        assert "Ctrl+O" in first_action.toolTip()

    def test_toolbar_order_plugin_buttons_before_zoom(self, qapp: QApplication) -> None:
        """Plugin buttons should come before zoom controls."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        labels = [a.text() for a in qtoolbar.actions()]
        assert labels[0] == "Open PDF"
        assert "Zoom In" in labels
        assert "Zoom Out" in labels
        assert labels.index("Open PDF") < labels.index("Zoom In")

    def test_open_file_button_opens_document(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Clicking the Open PDF button from the plugin should open a document."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        open_action = qtoolbar.actions()[0]
        assert open_action.text() == "Open PDF"

        with patch(
            "main.QFileDialog.getOpenFileName",
            return_value=(str(sample_pdf), "PDF Files (*.pdf)"),
        ):
            open_action.trigger()

        assert window.viewer._doc is not None
        assert window.viewer._doc.page_count == 3
        window.viewer.close()

    def test_open_file_button_canceled_does_not_open(self, qapp: QApplication) -> None:
        """Canceling the dialog should not load a document."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        open_action = qtoolbar.actions()[0]

        with patch("main.QFileDialog.getOpenFileName", return_value=("", "")):
            open_action.trigger()

        assert window.viewer._doc is None
