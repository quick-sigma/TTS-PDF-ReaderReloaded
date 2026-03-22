import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog

from pdfreader_reborn.ui.toolbar import NavigationToolbar
from pdfreader_reborn.ui.viewer import PDFViewer

ICONS_DIR = Path(__file__).parent / "icons"


class MainWindow(QMainWindow):
    """Application main window with PDF viewport."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Reader Reborn")
        self.resize(1200, 800)

        self.viewer = PDFViewer(self)
        self.setCentralWidget(self.viewer)

        self._create_toolbar()

    def _create_toolbar(self) -> None:
        """Create and add the navigation toolbar."""
        toolbar = NavigationToolbar(
            icons_dir=ICONS_DIR,
            on_open=self._open_file,
            on_zoom_in=self._zoom_in,
            on_zoom_out=self._zoom_out,
        )
        self.addToolBar(toolbar.to_qtoolbar())

    def _open_file(self) -> None:
        """Open a PDF file via dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self.viewer.load_document(Path(path))

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
