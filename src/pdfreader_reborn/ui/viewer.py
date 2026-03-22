# src/pdfreader_reborn/ui/viewer.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty

from PyQt6.QtCore import QPoint, Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel

from pdfreader_reborn.cache import PageAdapter, PageCacheLRU
from pdfreader_reborn.data.document import PdfDocument
from pdfreader_reborn.strings import t

DEFAULT_CACHE_CAPACITY = 5
DEFAULT_CACHE_WORKERS = 2

# ── Smooth zoom constants ─────────────────────────────────────
_ZOOM_STEP_MS = 16  # ~60 fps
_ZOOM_DURATION_MS = 150
_ZOOM_STEPS = max(1, _ZOOM_DURATION_MS // _ZOOM_STEP_MS)
_ZOOM_MIN_DELTA = 0.001  # stop early when close enough


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


class PdfDocumentAdapter:
    """Adapter that wraps a PdfDocument to satisfy the PageAdapter protocol.

    Each ``load_page`` call renders the page at the configured zoom
    and returns raw PNG bytes.  The LRU cache is then responsible for
    converting these bytes into QPixmaps and managing eviction.

    Args:
        doc: A loaded ``PdfDocument``.
        zoom: The zoom factor for rendering.
    """

    def __init__(self, doc: PdfDocument, zoom: float) -> None:
        self._doc = doc
        self._zoom = zoom

    @property
    def page_count(self) -> int:
        """Return the number of pages in the document."""
        return self._doc.page_count

    @property
    def zoom(self) -> float:
        """Return the current zoom factor."""
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        """Update the zoom factor for future loads."""
        self._zoom = value

    def load_page(self, index: int) -> bytes:
        """Render a page and return raw PNG bytes.

        Args:
            index: Zero-based page index.

        Returns:
            Raw PNG image bytes.
        """
        return self._doc.render_page(index, zoom=self._zoom)


class PixmapPageAdapter:
    """Wraps a bytes-based PageAdapter and converts results to QPixmap.

    This is the adapter that the ``PageCacheLRU`` uses directly.

    Args:
        inner: A ``PageAdapter`` that returns raw bytes.
    """

    def __init__(self, inner: PageAdapter[bytes]) -> None:
        self._inner = inner

    @property
    def page_count(self) -> int:
        return self._inner.page_count

    def load_page(self, index: int) -> QPixmap:
        """Load a page and convert to QPixmap.

        Args:
            index: Zero-based page index.

        Returns:
            A QPixmap of the rendered page.
        """
        raw = self._inner.load_page(index)
        image = QImage.fromData(raw, "PNG")
        return QPixmap.fromImage(image)


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


class _ZoomAnimator:
    """Smoothly interpolate zoom between current and target values.

    Uses a QTimer at ~60 fps to step through intermediate zoom values.
    On each step the viewer's label heights and scroll position are
    updated for a fluid visual effect.  When the animation settles the
    expensive page re-rendering is triggered once.

    Rapid wheel events update the *target* so the animation adapts
    in-flight without restarting from scratch (coalescence).

    Args:
        viewer: The ``PDFViewer`` that owns this animator.
    """

    def __init__(self, viewer: PDFViewer) -> None:
        self._viewer = viewer
        self._timer = QTimer()
        self._timer.setInterval(_ZOOM_STEP_MS)
        self._timer.timeout.connect(self._step)

        self._start_zoom: float = 0.0
        self._target_zoom: float = 0.0
        self._anchor: QPoint | None = None
        self._frame: int = 0

    # ── public API ──────────────────────────────────────────

    def start(self, current: float, target: float, anchor: QPoint | None) -> None:
        """Begin (or re-target) an animation.

        Args:
            current: Zoom level when the animation starts.
            target: Desired final zoom level.
            anchor: Viewport position to zoom toward.
        """
        self._start_zoom = current
        self._target_zoom = target
        self._anchor = anchor
        self._frame = 0
        if not self._timer.isActive():
            self._timer.start()

    def update_target(self, target: float, anchor: QPoint | None) -> None:
        """Retarget the running animation from the *current* zoom.

        If no animation is running this is equivalent to ``start``.
        """
        current = self._viewer.zoom
        if self._timer.isActive():
            self._start_zoom = current
            self._target_zoom = target
            self._anchor = anchor
            self._frame = 0
        else:
            self.start(current, target, anchor)

    def stop(self) -> None:
        """Immediately stop the animation."""
        self._timer.stop()

    @property
    def active(self) -> bool:
        """Return True while the animation timer is running."""
        return self._timer.isActive()

    # ── internals ───────────────────────────────────────────

    def _step(self) -> None:
        """Advance one animation frame."""
        self._frame += 1
        progress = min(1.0, self._frame / _ZOOM_STEPS)

        # ease-out cubic: fast start, gentle landing
        eased = 1.0 - (1.0 - progress) ** 3
        zoom = self._start_zoom + (self._target_zoom - self._start_zoom) * eased

        if progress >= 1.0 or abs(zoom - self._target_zoom) < _ZOOM_MIN_DELTA:
            self._timer.stop()
            self._viewer._apply_zoom_ui(self._target_zoom, self._anchor)
            self._viewer._finish_zoom()
            return

        self._viewer._apply_zoom_ui(zoom, self._anchor)


class PDFViewer(Viewer, QScrollArea):
    """Continuous-scroll PDF viewer with LRU page caching.

    Uses a ``PageCacheLRU`` backed by a thread pool to load and evict
    pages around the current scroll position.  As the user scrolls,
    the focus updates and the cache preloads neighboring pages
    asynchronously.

    Zoom transitions are animated smoothly via :class:`_ZoomAnimator`.

    Usage::

        viewer = PDFViewer()
        viewer.load_document(Path("report.pdf"))
        viewer.set_zoom(2.0)
    """

    zoom_in = pyqtSignal(QPoint)
    """Emitted on Ctrl+scroll-up with the mouse position as anchor."""

    zoom_out = pyqtSignal(QPoint)
    """Emitted on Ctrl+scroll-down with the mouse position as anchor."""

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

        self._adapter: PdfDocumentAdapter | None = None
        self._cache: PageCacheLRU[QPixmap] | None = None
        self._animator = _ZoomAnimator(self)

    # ── Document lifecycle ────────────────────────────────────

    def load_document(self, path: Path | str) -> None:
        """Open a PDF and prepare page placeholders with LRU cache.

        Args:
            path: Path to the PDF file.
        """
        self.close()

        self._doc = PdfDocument(path)
        self._adapter = PdfDocumentAdapter(self._doc, self._zoom)
        pixmap_adapter = PixmapPageAdapter(self._adapter)
        self._cache = PageCacheLRU(
            adapter=pixmap_adapter,
            capacity=DEFAULT_CACHE_CAPACITY,
            max_workers=DEFAULT_CACHE_WORKERS,
        )
        self._cache.on_loaded(self._on_cache_page_loaded)

        for i in range(self._doc.page_count):
            label = QLabel(t("viewer.page_loading", page=i + 1))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumHeight(200)
            label.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
            self._layout.addWidget(label)
            self._labels.append(label)

        # Seed the cache around page 0.
        self._cache.focus = 0

    def retranslate(self) -> None:
        """Update all translatable text on existing labels."""
        for i, label in enumerate(self._labels):
            if not label.pixmap():
                label.setText(t("viewer.page_loading", page=i + 1))

    def _on_cache_page_loaded(self, page_number: int) -> None:
        """Handle a page arriving in the LRU cache.

        Connected to ``PageCacheLRU.on_loaded``.
        """
        if self._cache is None:
            return
        pixmap = self._cache.get(page_number)
        if pixmap is None:
            return
        self._apply_pixmap(page_number, pixmap)

    # ── Scrolling / lazy loading ─────────────────────────────

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        """Handle scroll events to update cache focus.

        Args:
            dx: Horizontal scroll delta.
            dy: Vertical scroll delta.
        """
        super().scrollContentsBy(dx, dy)
        self._update_focus_from_scroll()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Intercept Ctrl+wheel to zoom toward the mouse cursor.

        Non-Ctrl wheel events pass through to the default scroll handler.

        Args:
            event: The wheel event.
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            anchor = event.position().toPoint()
            delta = event.angleDelta().y()
            if delta > 0:
                new_target = self.zoom + 0.25
            elif delta < 0:
                new_target = max(0.5, self.zoom - 0.25)
            else:
                return
            self.set_zoom(new_target, anchor=anchor, animate=True)
            event.accept()
        else:
            super().wheelEvent(event)

    def _update_focus_from_scroll(self) -> None:
        """Detect which page is most visible and update cache focus."""
        if self._cache is None or not self._labels:
            return

        viewport_height = self.viewport().height()
        scroll_pos = self.verticalScrollBar().value()
        viewport_center = scroll_pos + viewport_height // 2

        y_offset = 0
        best_index = 0
        best_distance = float("inf")

        for i, label in enumerate(self._labels):
            label_top = y_offset
            label_bottom = y_offset + label.height()
            y_offset += label.height() + self._layout.spacing()

            label_center = (label_top + label_bottom) // 2
            distance = abs(label_center - viewport_center)
            if distance < best_distance:
                best_distance = distance
                best_index = i

        if self._cache.focus != best_index:
            self._cache.focus = best_index

    # ── Render helpers ───────────────────────────────────────

    def _get_visible_range(self) -> tuple[int, int]:
        """Return (start, end) indices of pages near the viewport."""
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

        if not visible:
            return (0, 0)

        start = max(0, min(visible) - 1)
        end = min(len(self._labels), max(visible) + 3 + 1)
        return (start, end)

    def _render_page_sync(self, page_number: int) -> QPixmap | None:
        """Render a single page synchronously at the current zoom.

        Args:
            page_number: Zero-based page index.

        Returns:
            A QPixmap if successful, or None on error.
        """
        if self._cache is None:
            return None
        try:
            return self._cache.get_or_load(page_number)
        except Exception:
            return None

    def _apply_pixmap(self, page_number: int, pixmap: QPixmap) -> None:
        """Apply a rendered pixmap to the corresponding label.

        Args:
            page_number: Zero-based page index.
            pixmap: The rendered page image.
        """
        if page_number < 0 or page_number >= len(self._labels):
            return
        label = self._labels[page_number]
        label.setPixmap(pixmap)
        label.setMinimumHeight(pixmap.height())
        label.setText("")

    # ── Zoom ─────────────────────────────────────────────────

    def _default_anchor(self) -> QPoint:
        """Return the viewport center as default zoom anchor."""
        return QPoint(0, self.viewport().height() // 2)

    def set_zoom(
        self, zoom: float, anchor: QPoint | None = None, animate: bool = False
    ) -> None:
        """Set the zoom factor.

        When *anchor* is ``None`` the viewport centre is used so that
        keyboard / toolbar zooms feel natural.

        When *animate* is ``True`` the label heights and scroll
        position transition smoothly via :class:`_ZoomAnimator` and
        the expensive page re-rendering is deferred until the
        animation settles.  When *animate* is ``False`` the zoom
        is applied immediately (labels, scroll, and re-render in
        one shot).

        Args:
            zoom: New zoom factor (1.0 = 100%).
            anchor: Optional viewport position to zoom toward.
            animate: Whether to use a smooth transition.
        """
        if anchor is None:
            anchor = self._default_anchor()

        if self._doc is None or not self._labels:
            self._zoom = zoom
            return

        if abs(zoom - self._zoom) < _ZOOM_MIN_DELTA:
            return

        if animate:
            self._animator.update_target(zoom, anchor)
        else:
            self._animator.stop()
            self._apply_zoom_ui(zoom, anchor)
            self._finish_zoom()

    def _apply_zoom_ui(self, zoom: float, anchor: QPoint | None) -> None:
        """Fast label-height + scroll update (no rendering).

        Called on every animation frame.  Keeps the document point
        under *anchor* visually stationary.
        """
        if self._doc is None or not self._labels:
            self._zoom = zoom
            return

        # --- snapshot the anchor point in document space ----------
        scroll_pos = self.verticalScrollBar().value()
        anchor_y = anchor.y() if anchor is not None else 0
        doc_y = scroll_pos + anchor_y

        anchor_page, anchor_fraction = self._compute_anchor(doc_y)

        # --- apply new zoom to labels -----------------------------
        self._zoom = zoom
        if self._adapter is not None:
            self._adapter.zoom = zoom
        self._update_label_sizes()

        # --- restore scroll so the anchor stays put ---------------
        new_scroll = self._scroll_to_anchor(anchor_page, anchor_fraction, anchor_y)
        self.verticalScrollBar().setValue(max(0, new_scroll))

    def _finish_zoom(self) -> None:
        """Re-render visible pages at the final zoom level.

        Called once when the zoom animation settles.
        """
        if self._cache is None or self._doc is None:
            return

        vis_start, vis_end = self._get_visible_range()
        self._cache.clear()

        for i in range(vis_start, min(vis_end, len(self._labels))):
            pixmap = self._render_page_sync(i)
            if pixmap is not None:
                self._apply_pixmap(i, pixmap)

        # Update cache focus so neighbours begin preloading.
        self._update_focus_from_scroll()

    # ── Zoom geometry helpers ────────────────────────────────

    def _compute_anchor(self, doc_y: float) -> tuple[int, float]:
        """Find the page index and fractional offset for a document y.

        Args:
            doc_y: Absolute y coordinate in the document (px).

        Returns:
            ``(page_index, fraction)`` where *fraction* is in [0, 1).
        """
        y_offset = 0.0
        for i, label in enumerate(self._labels):
            lh = label.height()
            if y_offset + lh >= doc_y:
                fraction = (doc_y - y_offset) / lh if lh > 0 else 0.0
                return (i, fraction)
            y_offset += lh + self._layout.spacing()
        return (max(0, len(self._labels) - 1), 0.0)

    def _scroll_to_anchor(
        self,
        page: int,
        fraction: float,
        viewport_y: int,
    ) -> int:
        """Compute the scroll value that places *page*/*fraction* at *viewport_y*.

        Args:
            page: Target page index.
            fraction: Fractional position within the page [0, 1).
            viewport_y: Desired viewport y for that document point.

        Returns:
            The vertical scroll-bar value.
        """
        y = 0
        for i in range(page):
            y += self._labels[i].height() + self._layout.spacing()
        if page < len(self._labels):
            y += int(self._labels[page].height() * fraction)
        return y - viewport_y

    def _update_label_sizes(self) -> None:
        """Pre-compute and set expected label heights at current zoom."""
        if self._doc is None:
            return
        for i, label in enumerate(self._labels):
            if i < self._doc.page_count:
                page = self._doc.get_page(i)
                label.setMinimumHeight(int(page.height * self._zoom))

    @property
    def zoom(self) -> float:
        """Return the current zoom factor."""
        return self._zoom

    # ── Cleanup ──────────────────────────────────────────────

    def close(self) -> None:
        """Close the document and release resources."""
        self._animator.stop()

        if self._cache is not None:
            self._cache.shutdown()
            self._cache = None
        self._adapter = None

        for label in self._labels:
            self._layout.removeWidget(label)
            label.deleteLater()
        self._labels.clear()

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
