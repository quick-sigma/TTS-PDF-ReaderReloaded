import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QToolBar

from pdfreader_reborn.interface.viewport import PdfViewport

ICONS_DIR = Path(__file__).parent / "icons"


def _icon(name: str) -> QIcon:
    """Load an SVG icon from the icons/ directory."""
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()


class MainWindow(QMainWindow):
    """Application main window with PDF viewport."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Reader Reborn")
        self.resize(1200, 800)

        self.viewport = PdfViewport(self)
        self.setCentralWidget(self.viewport)

        self._create_toolbar()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(True)
        toolbar.setIconSize(toolbar.iconSize() * 1.5)
        self.addToolBar(toolbar)

        open_action = QAction(_icon("openFile"), "Open PDF", self)
        open_action.setToolTip("Open PDF file")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        zoom_in = QAction(_icon("zoomIn"), "Zoom In", self)
        zoom_in.setToolTip("Zoom in (Ctrl+=)")
        zoom_in.setShortcut("Ctrl+=")
        zoom_in.triggered.connect(
            lambda: self.viewport.set_zoom(self.viewport._zoom + 0.25)
        )
        toolbar.addAction(zoom_in)

        zoom_out = QAction(_icon("zoomOut"), "Zoom Out", self)
        zoom_out.setToolTip("Zoom out (Ctrl+-)")
        zoom_out.setShortcut("Ctrl+-")
        zoom_out.triggered.connect(
            lambda: self.viewport.set_zoom(max(0.5, self.viewport._zoom - 0.25))
        )
        toolbar.addAction(zoom_out)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self.viewport.load_document(Path(path))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if pdf_path.exists():
            window.viewport.load_document(pdf_path)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
