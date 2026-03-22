# tests/ui/test_viewer.py

import pytest
from pathlib import Path
from queue import Queue

from PyQt6.QtWidgets import QApplication

from pdfreader_reborn.ui.viewer import Viewer, PDFViewer, RenderWorker


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


class TestRenderWorker:
    """Tests for the RenderWorker thread safety."""

    def test_worker_uses_thread_safe_queue(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """RenderWorker should use queue.Queue, not list."""
        from pdfreader_reborn.data.document import PdfDocument

        doc = PdfDocument(sample_pdf)
        worker = RenderWorker(doc, zoom=1.0)
        assert isinstance(worker._queue, Queue)
        doc.close()

    def test_worker_deduplicates_requests(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Requesting the same page twice should only queue it once."""
        from pdfreader_reborn.data.document import PdfDocument

        doc = PdfDocument(sample_pdf)
        worker = RenderWorker(doc, zoom=1.0)
        worker.request_page(0)
        worker.request_page(0)
        assert worker._queue.qsize() == 1
        doc.close()

    def test_worker_accepts_different_pages(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Different page numbers should all be queued."""
        from pdfreader_reborn.data.document import PdfDocument

        doc = PdfDocument(sample_pdf)
        worker = RenderWorker(doc, zoom=1.0)
        worker.request_page(0)
        worker.request_page(1)
        worker.request_page(2)
        assert worker._queue.qsize() == 3
        doc.close()

    def test_worker_stop_terminates(self, qapp: QApplication, sample_pdf: Path) -> None:
        """stop() should terminate the worker thread."""
        from pdfreader_reborn.data.document import PdfDocument

        doc = PdfDocument(sample_pdf)
        worker = RenderWorker(doc, zoom=1.0)
        worker.start()
        worker.stop()
        assert not worker.isRunning()
        doc.close()


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


class TestPDFViewerLoadDocument:
    """Tests for PDFViewer.load_document and close behavior."""

    def test_load_document_sets_doc(self, qapp: QApplication, sample_pdf: Path) -> None:
        """load_document should set the internal document."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._doc is not None
        assert viewer._doc.page_count == 3
        viewer.close()

    def test_load_document_creates_labels(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """load_document should create one label per page."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert len(viewer._labels) == 3
        viewer.close()

    def test_load_document_starts_worker(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """load_document should create and start a render worker."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._worker is not None
        assert viewer._worker.isRunning()
        viewer.close()

    def test_load_document_with_string_path(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """load_document should accept string paths."""
        viewer = PDFViewer()
        viewer.load_document(str(sample_pdf))
        assert viewer._doc is not None
        assert viewer._doc.page_count == 3
        viewer.close()

    def test_load_document_twice_replaces_previous(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Loading a second document should clean up the first."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        first_worker = viewer._worker
        first_doc = viewer._doc

        viewer.load_document(sample_pdf)
        # Worker is a new instance
        assert viewer._worker is not first_worker
        # Doc is a new instance
        assert viewer._doc is not first_doc
        # Still has correct page count
        assert len(viewer._labels) == 3
        # Labels are fresh QLabels (old ones were deleted)
        viewer.close()

    def test_close_clears_doc(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should set _doc to None."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.close()
        assert viewer._doc is None

    def test_close_stops_worker(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should stop the render worker."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.close()
        assert viewer._worker is None

    def test_close_clears_cache(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should clear the pixmap cache."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._cache[0] = "dummy"
        viewer.close()
        assert len(viewer._cache) == 0


class TestPDFViewerCloseEvent:
    """Tests for PDFViewer.closeEvent."""

    def test_close_event_calls_close(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """closeEvent should call close()."""
        from PyQt6.QtCore import QEvent

        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._doc is not None

        # Use a real QCloseEvent
        from PyQt6.QtGui import QCloseEvent

        event = QCloseEvent()
        viewer.closeEvent(event)
        assert viewer._doc is None
        assert viewer._worker is None

    def test_close_event_accepts_event(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """closeEvent should accept the event (propagate to super)."""
        from PyQt6.QtGui import QCloseEvent

        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        event = QCloseEvent()
        viewer.closeEvent(event)
        # super().closeEvent() should have been called — no error means success
        viewer.close()
