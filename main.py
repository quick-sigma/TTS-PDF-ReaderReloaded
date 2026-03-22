# main.py

import sys
from pathlib import Path

from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog

from pdfreader_reborn.kernel import Kernel
from pdfreader_reborn.plugins import OpenFilePlugin
from pdfreader_reborn.ui.signals import AppSignals
from pdfreader_reborn.ui.keyboard import KeyboardManager
from pdfreader_reborn.ui.toolbar import NavigationToolbar
from pdfreader_reborn.ui.viewer import PDFViewer

ICONS_DIR = Path(__file__).parent / "icons"


class MainWindow(QMainWindow):
    """Application main window with PDF viewport.

    Uses AppSignals as the single event bus. Both toolbar clicks and
    keyboard shortcuts emit the same signals, ensuring one handler
    per action with no double-dispatch. The kernel manages plugins
    that contribute toolbar buttons and other UI elements.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Reader Reborn")
        self.resize(1200, 800)

        self.signals = AppSignals()
        self.keyboard = KeyboardManager(self.signals)
        self.kernel = Kernel()

        self.viewer = PDFViewer(self)
        self.setCentralWidget(self.viewer)

        self._connect_signals()
        self._register_plugins()
        self._create_toolbar()

    def _connect_signals(self) -> None:
        """Connect all application signals to their handlers."""
        self.signals.zoom_in.connect(self._zoom_in)
        self.signals.zoom_out.connect(self._zoom_out)
        self.signals.open_file.connect(self._open_file)
        self.signals.close_document.connect(self._close_document)

    def _register_plugins(self) -> None:
        """Register built-in plugins with the kernel."""
        open_plugin = OpenFilePlugin(
            on_open=lambda: self.signals.open_file.emit(),
        )
        self.kernel.register_plugin(open_plugin)

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
            self, "Open PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self.viewer.load_document(Path(path))

    def _close_document(self) -> None:
        """Close the current document."""
        self.viewer.close()
        self.setWindowTitle("PDF Reader Reborn")

    def _zoom_in(self) -> None:
        """Zoom in by 0.25."""
        self.viewer.set_zoom(self.viewer.zoom + 0.25)

    def _zoom_out(self) -> None:
        """Zoom out by 0.25, minimum 0.5."""
        self.viewer.set_zoom(max(0.5, self.viewer.zoom - 0.25))


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
