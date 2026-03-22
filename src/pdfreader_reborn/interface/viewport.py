from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel

from pdfreader_reborn.data.pdf_loader import PdfDocument


@dataclass
class PageRenderTask:
    """Metadata for a page that needs to be (or has been) rendered."""

    page_number: int
    zoom: float
    pixmap: QPixmap | None = field(default=None, repr=False)

    @property
    def is_rendered(self) -> bool:
        return self.pixmap is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PageRenderTask):
            return NotImplemented
        return self.page_number == other.page_number and self.zoom == other.zoom


class RenderWorker(QThread):
    """Background thread that renders PDF pages off the UI thread."""

    page_ready = pyqtSignal(int, QPixmap)

    def __init__(self, doc: PdfDocument, zoom: float = 1.5) -> None:
        super().__init__()
        self._doc = doc
        self._zoom = zoom
        self._queue: list[int] = []
        self._running = True

    def request_page(self, page_number: int) -> None:
        if page_number not in self._queue:
            self._queue.append(page_number)

    def run(self) -> None:
        while self._running:
            if not self._queue:
                self.msleep(16)
                continue

            page_num = self._queue.pop(0)
            try:
                img_bytes = self._doc.render_page(page_num, zoom=self._zoom)
                image = QImage.fromData(img_bytes, "PNG")
                pixmap = QPixmap.fromImage(image)
                self.page_ready.emit(page_num, pixmap)
            except Exception:
                pass

    def stop(self) -> None:
        self._running = False
        self.wait()


class PdfViewport(QScrollArea):
    """Continuous-scroll PDF viewer with lazy page rendering.

    Only pages visible in the viewport (plus a small buffer) are rendered.
    As the user scrolls, new pages are requested from the background worker
    and already-rendered pages that leave the viewport can be evicted from
    the pixmap cache to save memory.
    """

    CACHE_AHEAD = 3
    CACHE_BEHIND = 1

    def __init__(self, parent: QWidget | None = None) -> None:
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
        """Open a PDF and prepare page placeholders."""
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
        if self._doc is None:
            return
        self._worker = RenderWorker(self._doc, self._zoom)
        self._worker.page_ready.connect(self._on_page_ready)
        self._worker.start()
        self._request_visible_pages()

    def _on_page_ready(self, page_number: int, pixmap: QPixmap) -> None:
        if page_number < 0 or page_number >= len(self._labels):
            return
        self._cache[page_number] = pixmap
        label = self._labels[page_number]
        label.setPixmap(pixmap)
        label.setMinimumHeight(pixmap.height())
        label.setText("")

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._request_visible_pages()

    def _request_visible_pages(self) -> None:
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
            len(self._labels), (max(visible) + self.CACHE_AHEAD + 1) if visible else 0
        )

        for i in range(start, end):
            if i not in self._cache:
                self._worker.request_page(i)

        evict = [k for k in self._cache if k < start or k >= end]
        for k in evict:
            del self._cache[k]

    def set_zoom(self, zoom: float) -> None:
        self._zoom = zoom
        self._cache.clear()
        if self._doc is not None:
            self._cleanup_worker()
            self._start_worker()

    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def closeEvent(self, event) -> None:  # noqa: ANN001
        self._cleanup_worker()
        if self._doc is not None:
            self._doc.close()
            self._doc = None
        super().closeEvent(event)
