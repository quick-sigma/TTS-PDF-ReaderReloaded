import pytest
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from pdfreader_reborn.ui.viewer import Viewer, PDFViewer


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication for viewer tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestViewer:
    """Tests for the Viewer base class."""

    def test_viewer_methods_raise_not_implemented(self) -> None:
        """Viewer methods should raise NotImplementedError."""
        viewer = Viewer()
        with pytest.raises(NotImplementedError):
            viewer.load_document("test.pdf")
        with pytest.raises(NotImplementedError):
            viewer.set_zoom(1.0)
        with pytest.raises(NotImplementedError):
            _ = viewer.zoom
        with pytest.raises(NotImplementedError):
            viewer.close()


class TestPDFViewer:
    """Tests for the PDFViewer concrete implementation."""

    def test_pdf_viewer_implements_viewer(self, qapp: QApplication) -> None:
        """PDFViewer should be a subclass of Viewer."""
        viewer = PDFViewer()
        assert isinstance(viewer, Viewer)

    def test_pdf_viewer_initial_zoom(self, qapp: QApplication) -> None:
        """Default zoom should be 1.5."""
        viewer = PDFViewer()
        assert viewer.zoom == 1.5

    def test_pdf_viewer_set_zoom(self, qapp: QApplication) -> None:
        """set_zoom should update the zoom factor."""
        viewer = PDFViewer()
        viewer.set_zoom(2.0)
        assert viewer.zoom == 2.0

    def test_pdf_viewer_has_no_document_initially(self, qapp: QApplication) -> None:
        """Viewer should have no document before loading."""
        viewer = PDFViewer()
        assert viewer._doc is None

    def test_pdf_viewer_close_without_document(self, qapp: QApplication) -> None:
        """close() should not raise when no document is loaded."""
        viewer = PDFViewer()
        viewer.close()  # Should not raise
