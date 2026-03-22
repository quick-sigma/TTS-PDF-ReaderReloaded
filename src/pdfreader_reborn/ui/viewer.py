# src/pdfreader_reborn/ui/viewer.py

from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel

from pdfreader_reborn.data.document import PdfDocument


@dataclass
class PageRenderTask:
    """Metadata for a page that needs to be (or has been) rendered.

    Attributes:
        page_number: Zero-based page index.
        zoom: Zoom factor for rendering.
        pixmap: Rendered pixmap, or None if not yet rendered.
    """

    page_number: int
    zoom: float
    pixmap: QPixmap | None = field(default=None, repr=False)

    @property
    def is_rendered(self) -> bool:
        """Return True if the page has been rendered."""
        return self.pixmap is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PageRenderTask):
            return NotImplemented
        return self.page_number == other.page_number and self.zoom == other.zoom


class RenderWorker(QThread):
    """Background thread that renders PDF pages off the UI thread.

    Uses a thread-safe Queue to receive page requests. The worker sleeps
    efficiently when idle — no busy-waiting or polling loops.

    Attributes:
        page_ready: Signal emitted with (page_number, pixmap) when done.
    """

    page_ready = pyqtSignal(int, QPixmap)

    QUEUE_TIMEOUT: float = 0.1
    """Seconds to wait for a queue item before checking _running flag."""

    def __init__(self, doc: PdfDocument, zoom: float = 1.5) -> None:
        """Initialize the render worker.

        Args:
            doc: The PDF document to render pages from.
            zoom: Zoom factor for rendering.
        """
        super().__init__()
        self._doc = doc
        self._zoom = zoom
        self._queue: Queue[int] = Queue()
        self._running = True
        self._pending: set[int] = set()

    def request_page(self, page_number: int) -> None:
        """Queue a page for rendering. Thread-safe, deduplicates requests.

        Args:
            page_number: Zero-based page index to render.
        """
        if page_number not in self._pending:
            self._pending.add(page_number)
            self._queue.put(page_number)

    def run(self) -> None:
        """Main render loop. Blocks on queue, no busy-waiting."""
        while self._running:
            try:
                page_num = self._queue.get(timeout=self.QUEUE_TIMEOUT)
            except Empty:
                continue

            try:
                img_bytes = self._doc.render_page(page_num, zoom=self._zoom)
                image = QImage.fromData(img_bytes, "PNG")
                pixmap = QPixmap.fromImage(image)
                self.page_ready.emit(page_num, pixmap)
            except Exception:
                pass
            finally:
                self._pending.discard(page_num)

    def stop(self) -> None:
        """Stop the render loop and wait for the thread to finish."""
        self._running = False
        self.wait()


class Viewer:
    """Abstract base class for document viewers.

    A viewer is responsible for displaying document content with features
    like zoom and lazy loading. Subclasses must implement the abstract
    methods to provide format-specific rendering.

    Note: This class uses duck typing rather than ABC to allow multiple
    inheritance with Qt widgets.
    """

    def load_document(self, path: Path | str) -> None:
        """Open and display a document.

        Args:
            path: Path to the document file.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom factor.

        Args:
            zoom: New zoom factor (1.0 = 100%).

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    @property
    def zoom(self) -> float:
        """Return the current zoom factor.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Close the current document and release resources.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError


class PDFViewer(Viewer, QScrollArea):
    """Continuous-scroll PDF viewer with lazy page rendering.

    Only pages visible in the viewport (plus a small buffer) are rendered.
    As the user scrolls, new pages are requested from the background worker
    and already-rendered pages that leave the viewport can be evicted from
    the pixmap cache to save memory.

    Usage::

        viewer = PDFViewer()
        viewer.load_document(Path("report.pdf"))
        viewer.set_zoom(2.0)
    """

    CACHE_AHEAD: int = 3
    CACHE_BEHIND: int = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the PDF viewer.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)

        self._doc: PdfDocument | None = None
        self._zoom: float = 1.5
        self._labels: list[QLabel] = []
        self._cache: dict[int, QPixmap] = {}
        self._worker: RenderWorker | None = None

    def load_document(self, path: Path | str) -> None:
        """Open a PDF and prepare page placeholders.

        Args:
            path: Path to the PDF file.
        """
        self._cleanup_worker()

        self._doc = PdfDocument(path)
        self._cache.clear()

        for label in self._labels:
            self._layout.removeWidget(label)
            label.deleteLater()
        self._labels.clear()

        for i in range(self._doc.page_count):
            label = QLabel(f"Page {i + 1} — loading…")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumHeight(200)
            label.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
            self._layout.addWidget(label)
            self._labels.append(label)

        self._start_worker()

    def _start_worker(self) -> None:
        """Start the background render worker."""
        if self._doc is None:
            return
        self._worker = RenderWorker(self._doc, self._zoom)
        self._worker.page_ready.connect(self._on_page_ready)
        self._worker.start()
        self._request_visible_pages()

    def _on_page_ready(self, page_number: int, pixmap: QPixmap) -> None:
        """Handle a rendered page from the worker.

        Args:
            page_number: Zero-based page index.
            pixmap: The rendered page image.
        """
        if page_number < 0 or page_number >= len(self._labels):
            return
        self._cache[page_number] = pixmap
        label = self._labels[page_number]
        label.setPixmap(pixmap)
        label.setMinimumHeight(pixmap.height())
        label.setText("")

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        """Handle scroll events to trigger lazy loading.

        Args:
            dx: Horizontal scroll delta.
            dy: Vertical scroll delta.
        """
        super().scrollContentsBy(dx, dy)
        self._request_visible_pages()

    def _request_visible_pages(self) -> None:
        """Request rendering for visible pages and evict off-screen ones."""
        if self._doc is None or self._worker is None:
            return

        viewport_height = self.viewport().height()
        scroll_pos = self.verticalScrollBar().value()

        visible: set[int] = set()
        y_offset = 0
        for i, label in enumerate(self._labels):
            label_top = y_offset
            label_bottom = y_offset + label.height()
            y_offset += label.height() + self._layout.spacing()

            if label_bottom < scroll_pos - 200:
                continue
            if label_top > scroll_pos + viewport_height + 200:
                break

            visible.add(i)

        start = max(0, min(visible) - self.CACHE_BEHIND) if visible else 0
        end = min(
            len(self._labels),
            (max(visible) + self.CACHE_AHEAD + 1) if visible else 0,
        )

        for i in range(start, end):
            if i not in self._cache:
                self._worker.request_page(i)

        evict = [k for k in self._cache if k < start or k >= end]
        for k in evict:
            del self._cache[k]

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom factor and re-render all pages.

        Args:
            zoom: New zoom factor (1.0 = 100%).
        """
        self._zoom = zoom
        self._cache.clear()
        if self._doc is not None:
            self._cleanup_worker()
            self._start_worker()

    @property
    def zoom(self) -> float:
        """Return the current zoom factor."""
        return self._zoom

    def _cleanup_worker(self) -> None:
        """Stop and clean up the render worker."""
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def close(self) -> None:
        """Close the document and release resources."""
        self._cleanup_worker()
        self._cache.clear()
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def closeEvent(self, event) -> None:  # noqa: ANN001
        """Handle widget close event.

        Args:
            event: The close event.
        """
        self.close()
        super().closeEvent(event)
