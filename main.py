# main.py

import sys
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMenu, QMenuBar

from pdfreader_reborn.kernel import Kernel
from pdfreader_reborn.plugins import OpenFilePlugin
from pdfreader_reborn.strings import t, set_locale, on_locale_changed
from pdfreader_reborn.ui.signals import AppSignals
from pdfreader_reborn.ui.keyboard import KeyboardManager
from pdfreader_reborn.ui.toolbar import NavigationToolbar
from pdfreader_reborn.ui.viewer import PDFViewer

ICONS_DIR = Path(__file__).parent / "icons"

# Shortcut constants
OPEN_SHORTCUT = "Ctrl+O"
ZOOM_IN_SHORTCUT = "Ctrl+="
ZOOM_OUT_SHORTCUT = "Ctrl+-"
CLOSE_SHORTCUT = "Ctrl+W"
EXIT_SHORTCUT = "Ctrl+Q"


class MainWindow(QMainWindow):
    """Application main window with PDF viewport and menu bar.

    Uses AppSignals as the single event bus. Both toolbar clicks and
    keyboard shortcuts emit the same signals, ensuring one handler
    per action with no double-dispatch. The kernel manages plugins
    that contribute toolbar buttons and other UI elements.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(t("app.title"))
        self.resize(1200, 800)

        self.signals = AppSignals()
        self.keyboard = KeyboardManager(self.signals)
        self.kernel = Kernel()

        self.viewer = PDFViewer(self)
        self.setCentralWidget(self.viewer)

        self._menu_actions: dict[str, QAction] = {}

        self._connect_signals()
        self._register_plugins()
        self._create_menu_bar()
        self._create_toolbar()

        on_locale_changed(self._retranslate)

    def _connect_signals(self) -> None:
        """Connect all application signals to their handlers."""
        self.signals.zoom_in.connect(lambda: self._zoom_in())
        self.signals.zoom_out.connect(lambda: self._zoom_out())
        self.signals.open_file.connect(self._open_file)
        self.signals.close_document.connect(self._close_document)
        self.viewer.zoom_in.connect(self._zoom_in)
        self.viewer.zoom_out.connect(self._zoom_out)

    def _register_plugins(self) -> None:
        """Register built-in plugins with the kernel."""
        open_plugin = OpenFilePlugin(
            on_open=lambda: self.signals.open_file.emit(),
        )
        self.kernel.register_plugin(open_plugin)

    def _make_action(
        self,
        key: str,
        callback: Callable[[], None],
        shortcut: str = "",
    ) -> QAction:
        """Create a QAction backed by a translatable string key.

        Args:
            key: The i18n string key for the action text.
            callback: Slot invoked when triggered.
            shortcut: Optional keyboard shortcut.

        Returns:
            The configured QAction.
        """
        action = QAction(t(key), self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self._menu_actions[key] = action
        return action

    def _create_menu_bar(self) -> None:
        """Build the menu bar with File, View, and Settings menus."""
        menubar = self.menuBar()

        # ── File menu ────────────────────────────────────────
        file_menu = menubar.addMenu(t("menu.file"))
        file_menu.addAction(
            self._make_action(
                "menu.file.open",
                lambda: self.signals.open_file.emit(),
                OPEN_SHORTCUT,
            )
        )
        file_menu.addSeparator()
        file_menu.addAction(
            self._make_action(
                "menu.file.close",
                lambda: self.signals.close_document.emit(),
                CLOSE_SHORTCUT,
            )
        )
        file_menu.addAction(
            self._make_action("menu.file.exit", self._exit_app, EXIT_SHORTCUT)
        )

        # ── View menu ────────────────────────────────────────
        view_menu = menubar.addMenu(t("menu.view"))
        view_menu.addAction(
            self._make_action(
                "menu.view.zoom_in",
                lambda: self.signals.zoom_in.emit(),
                ZOOM_IN_SHORTCUT,
            )
        )
        view_menu.addAction(
            self._make_action(
                "menu.view.zoom_out",
                lambda: self.signals.zoom_out.emit(),
                ZOOM_OUT_SHORTCUT,
            )
        )

        # ── Settings menu ────────────────────────────────────
        settings_menu = menubar.addMenu(t("menu.settings"))
        lang_menu = settings_menu.addMenu(t("menu.settings.language"))
        self._lang_menu = lang_menu

        for code in ("es", "en"):
            label_key = f"lang.{code}"
            lang_action = QAction(t(label_key), self)
            lang_action.setCheckable(True)
            lang_action.setData(code)
            lang_action.triggered.connect(lambda checked, c=code: set_locale(c))
            lang_menu.addAction(lang_action)

        # Mark the current locale as checked.
        self._update_language_checks()

    def _update_language_checks(self) -> None:
        """Ensure only the active language radio is checked."""
        from pdfreader_reborn.strings import get_locale

        current = get_locale()
        for action in self._lang_menu.actions():
            action.setChecked(action.data() == current)

    def _create_toolbar(self) -> None:
        """Create toolbar with plugin-contributed buttons and zoom controls."""
        toolbar = NavigationToolbar(
            icons_dir=ICONS_DIR,
            on_zoom_in=lambda: self.signals.zoom_in.emit(),
            on_zoom_out=lambda: self.signals.zoom_out.emit(),
        )

        plugin_buttons = self.kernel.get_toolbar_buttons(ICONS_DIR)
        for btn in reversed(plugin_buttons):
            toolbar.add_first(btn)

        self._nav_toolbar = toolbar
        self.addToolBar(toolbar.to_qtoolbar())

    def _retranslate(self) -> None:
        """Update every translatable string in the UI."""
        self.setWindowTitle(t("app.title"))

        # Menu bar
        menubar = self.menuBar()
        menus = menubar.findChildren(QMenu)
        # Top-level menus: File, View, Settings
        for menu in menus:
            if menu.parent() is not menubar:
                continue

        # Rebuild is simpler than patching — wipe and recreate.
        menubar.clear()
        self._menu_actions.clear()
        self._create_menu_bar()
        self._update_language_checks()

        # Toolbar (tear down old and rebuild)
        old_toolbar = self._nav_toolbar
        old_qtoolbar = old_toolbar.to_qtoolbar()
        self.removeToolBar(old_qtoolbar)
        old_qtoolbar.deleteLater()
        self._create_toolbar()

        # Viewer placeholder text
        self.viewer.retranslate()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Delegate key events to KeyboardManager.

        Args:
            event: The key press event.
        """
        if self.keyboard.handle_key_press(event):
            event.accept()
        else:
            super().keyPressEvent(event)

    def _open_file(self) -> None:
        """Open a PDF file via dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self, t("dialog.open.title"), "", t("dialog.open.filter")
        )
        if path:
            self.viewer.load_document(Path(path))

    def _close_document(self) -> None:
        """Close the current document."""
        self.viewer.close()
        self.setWindowTitle(t("app.title"))

    def _exit_app(self) -> None:
        """Exit the application."""
        self.close()

    def _zoom_in(self, anchor: QPoint | None = None) -> None:
        """Zoom in by 0.25, optionally toward *anchor*."""
        self.viewer.set_zoom(self.viewer.zoom + 0.25, anchor=anchor)

    def _zoom_out(self, anchor: QPoint | None = None) -> None:
        """Zoom out by 0.25 (minimum 0.5), optionally toward *anchor*."""
        self.viewer.set_zoom(max(0.5, self.viewer.zoom - 0.25), anchor=anchor)


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if pdf_path.exists():
            window.viewer.load_document(pdf_path)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
