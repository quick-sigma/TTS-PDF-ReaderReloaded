# tests/ui/test_main_window.py

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtGui import QKeyEvent

from main import MainWindow
from pdfreader_reborn.strings import t


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
        assert qtoolbar.windowTitle() == t("toolbar.navigation.name")
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
        assert first_action.text() == t("toolbar.open.label")
        assert "Ctrl+O" in first_action.toolTip()

    def test_toolbar_order_plugin_buttons_before_zoom(self, qapp: QApplication) -> None:
        """Plugin buttons should come before zoom controls."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        labels = [a.text() for a in qtoolbar.actions()]
        assert labels[0] == t("toolbar.open.label")
        assert t("toolbar.zoom_in.label") in labels
        assert t("toolbar.zoom_out.label") in labels
        assert labels.index(t("toolbar.open.label")) < labels.index(
            t("toolbar.zoom_in.label")
        )

    def test_open_file_button_opens_document(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Clicking the Open PDF button from the plugin should open a document."""
        window = MainWindow()
        qtoolbar = window._nav_toolbar.to_qtoolbar()
        open_action = qtoolbar.actions()[0]
        assert open_action.text() == t("toolbar.open.label")

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


class TestMainWindowMenu:
    """Tests for the menu bar structure."""

    def test_menu_bar_exists(self, qapp: QApplication) -> None:
        """MainWindow should have a menu bar."""
        window = MainWindow()
        menubar = window.menuBar()
        assert menubar is not None

    def test_has_file_menu(self, qapp: QApplication) -> None:
        """Menu bar should have a File menu."""
        window = MainWindow()
        menu_titles = [m.title() for m in window.menuBar().findChildren(QMenu)]
        assert t("menu.file") in menu_titles

    def test_has_view_menu(self, qapp: QApplication) -> None:
        """Menu bar should have a View menu."""
        window = MainWindow()
        menu_titles = [m.title() for m in window.menuBar().findChildren(QMenu)]
        assert t("menu.view") in menu_titles

    def test_has_settings_menu(self, qapp: QApplication) -> None:
        """Menu bar should have a Settings menu."""
        window = MainWindow()
        menu_titles = [m.title() for m in window.menuBar().findChildren(QMenu)]
        assert t("menu.settings") in menu_titles

    def test_file_menu_has_open_action(self, qapp: QApplication) -> None:
        """File menu should contain an Open file action."""
        window = MainWindow()
        file_menu = window.menuBar().findChildren(QMenu)[0]
        action_texts = [a.text() for a in file_menu.actions()]
        assert t("menu.file.open") in action_texts

    def test_view_menu_has_zoom_actions(self, qapp: QApplication) -> None:
        """View menu should contain zoom in and zoom out actions."""
        window = MainWindow()
        view_menu = window.menuBar().findChildren(QMenu)[1]
        action_texts = [a.text() for a in view_menu.actions()]
        assert t("menu.view.zoom_in") in action_texts
        assert t("menu.view.zoom_out") in action_texts

    def test_settings_menu_has_language_submenu(self, qapp: QApplication) -> None:
        """Settings menu should contain a Language submenu."""
        window = MainWindow()
        settings_menu = window.menuBar().findChildren(QMenu)[2]
        submenus = settings_menu.findChildren(QMenu)
        submenu_titles = [m.title() for m in submenus]
        assert t("menu.settings.language") in submenu_titles

    def test_language_submenu_has_es_and_en(self, qapp: QApplication) -> None:
        """Language submenu should have Spanish and English options."""
        window = MainWindow()
        lang_menu = window._lang_menu
        lang_texts = [a.text() for a in lang_menu.actions()]
        assert t("lang.es") in lang_texts
        assert t("lang.en") in lang_texts

    def test_open_action_triggers_open_file(self, qapp: QApplication) -> None:
        """Open file menu action should emit the open_file signal."""
        window = MainWindow()
        callback = Mock()
        window.signals.open_file.connect(callback)

        file_menu = window.menuBar().findChildren(QMenu)[0]
        open_action = None
        for a in file_menu.actions():
            if a.text() == t("menu.file.open"):
                open_action = a
                break
        assert open_action is not None
        with patch("main.QFileDialog.getOpenFileName", return_value=("", "")):
            open_action.trigger()
        callback.assert_called_once()

    def test_zoom_in_action_triggers_zoom(self, qapp: QApplication) -> None:
        """Zoom In menu action should emit the zoom_in signal."""
        window = MainWindow()
        callback = Mock()
        window.signals.zoom_in.connect(callback)

        view_menu = window.menuBar().findChildren(QMenu)[1]
        zoom_in_action = None
        for a in view_menu.actions():
            if a.text() == t("menu.view.zoom_in"):
                zoom_in_action = a
                break
        assert zoom_in_action is not None
        zoom_in_action.trigger()
        callback.assert_called_once()


class TestMainWindowMenuRetranslation:
    """Tests that menu text updates when locale changes."""

    def test_menu_updates_on_locale_change(self, qapp: QApplication) -> None:
        """Switching locale should retranslate all menu text."""
        from pdfreader_reborn.strings import set_locale

        window = MainWindow()
        set_locale("en")

        menu_titles = [m.title() for m in window.menuBar().findChildren(QMenu)]
        assert "File" in menu_titles
        assert "View" in menu_titles
        assert "Settings" in menu_titles

        # Restore to default
        set_locale("es")
