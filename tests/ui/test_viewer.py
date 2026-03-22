# tests/ui/test_viewer.py

import pytest
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from pdfreader_reborn.ui.viewer import Viewer, PDFViewer
from pdfreader_reborn.cache import PageCacheLRU


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


class TestPDFViewerLoadDocument:
    """Tests for PDFViewer.load_document and close behavior."""

    def test_load_document_sets_doc(self, qapp: QApplication, sample_pdf: Path) -> None:
        """load_document should set the internal document."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._doc is not None
        assert viewer._doc.page_count == 3
        viewer.close()

    def test_load_document_creates_lru_cache(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """load_document should create a PageCacheLRU."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._cache is not None
        assert isinstance(viewer._cache, PageCacheLRU)
        viewer.close()

    def test_load_document_creates_labels(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """load_document should create one label per page."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert len(viewer._labels) == 3
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

    def test_close_clears_doc(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should set _doc to None."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.close()
        assert viewer._doc is None

    def test_close_clears_cache(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should set _cache to None."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.close()
        assert viewer._cache is None

    def test_close_clears_labels(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should remove all labels."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert len(viewer._labels) == 3
        viewer.close()
        assert len(viewer._labels) == 0


class TestPDFViewerZoom:
    """Tests for zoom behavior with LRU cache."""

    def test_set_zoom_updates_label_sizes_immediately(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """set_zoom should set label dimensions to expected values."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)

        viewer.set_zoom(2.0)
        qapp.processEvents()

        for i, label in enumerate(viewer._labels):
            page = viewer._doc.get_page(i)
            assert label.height() == int(page.height * 2.0)
            assert label.width() == int(page.width * 2.0)

        viewer.close()

    def test_set_zoom_renders_visible_pages_sync(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """set_zoom should render visible pages synchronously."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        old_zoom = viewer.zoom
        viewer.set_zoom(old_zoom + 0.5)

        assert viewer._cache is not None
        assert 0 in viewer._cache

        pixmap = viewer._cache.get(0)
        assert pixmap is not None
        page = viewer._doc.get_page(0)
        expected_height = int(page.height * viewer.zoom)
        assert pixmap.height() == expected_height

        viewer.close()


# ── Smooth zoom tests ────────────────────────────────────────


class TestZoomAnimator:
    """Tests for the _ZoomAnimator helper class."""

    def test_animator_not_active_by_default(self, qapp: QApplication) -> None:
        """Animator should not be active on creation."""
        viewer = PDFViewer()
        assert not viewer._animator.active

    def test_animator_starts_active(self, qapp: QApplication, sample_pdf: Path) -> None:
        """start() should make the animator active."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._animator.start(1.5, 2.0, QPoint(0, 100))
        assert viewer._animator.active
        viewer.close()

    def test_animator_stop_deactivates(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """stop() should deactivate the animator."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._animator.start(1.5, 2.0, QPoint(0, 100))
        viewer._animator.stop()
        assert not viewer._animator.active
        viewer.close()

    def test_animator_reaches_target(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """After enough time the zoom should reach the target."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        viewer._animator.start(1.5, 2.5, QPoint(0, 100))

        # Wait long enough for all animation frames (~150ms + margin).
        QTest.qWait(300)

        assert not viewer._animator.active
        assert viewer.zoom == pytest.approx(2.5, abs=0.01)
        viewer.close()

    def test_animator_update_target_restarts(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """update_target mid-animation should retarget."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        viewer._animator.start(1.5, 2.0, QPoint(0, 100))

        # Let a couple of frames run, then retarget.
        QTest.qWait(50)
        viewer._animator.update_target(3.0, QPoint(0, 200))

        QTest.qWait(300)

        assert viewer.zoom == pytest.approx(3.0, abs=0.01)
        viewer.close()

    def test_close_stops_animator(self, qapp: QApplication, sample_pdf: Path) -> None:
        """close() should stop a running animator."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._animator.start(1.5, 2.0, QPoint(0, 100))
        assert viewer._animator.active
        viewer.close()
        assert not viewer._animator.active


class TestApplyZoomUI:
    """Tests for _apply_zoom_ui — the fast label + scroll update."""

    def test_apply_zoom_ui_updates_zoom(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_apply_zoom_ui should set _zoom immediately."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._apply_zoom_ui(2.0, QPoint(0, 0))
        assert viewer.zoom == 2.0
        viewer.close()

    def test_apply_zoom_ui_updates_label_heights(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Label dimensions should reflect the new zoom."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer._apply_zoom_ui(3.0, QPoint(0, 0))
        qapp.processEvents()
        for i, label in enumerate(viewer._labels):
            page = viewer._doc.get_page(i)
            assert label.height() == int(page.height * 3.0)
            assert label.width() == int(page.width * 3.0)
        viewer.close()

    def test_apply_zoom_ui_no_doc_does_not_raise(self, qapp: QApplication) -> None:
        """_apply_zoom_ui without a document should just set _zoom."""
        viewer = PDFViewer()
        viewer._apply_zoom_ui(2.0, QPoint(0, 0))
        assert viewer.zoom == 2.0


class TestComputeAnchor:
    """Tests for _compute_anchor geometry helper."""

    def test_compute_anchor_top(self, qapp: QApplication, sample_pdf: Path) -> None:
        """A doc_y of 0 should return page 0, fraction 0."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        page, fraction = viewer._compute_anchor(0)
        assert page == 0
        assert fraction == pytest.approx(0.0)
        viewer.close()

    def test_compute_anchor_mid_page(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """A doc_y at half the first page should return fraction ~0.5."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        h = viewer._labels[0].height()
        page, fraction = viewer._compute_anchor(h / 2)
        assert page == 0
        assert fraction == pytest.approx(0.5, abs=0.01)
        viewer.close()

    def test_scroll_to_anchor_roundtrip(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_scroll_to_anchor should reverse _compute_anchor."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)

        target_doc_y = 300
        page, frac = viewer._compute_anchor(target_doc_y)
        scroll = viewer._scroll_to_anchor(page, frac, viewport_y=0)
        assert scroll == pytest.approx(target_doc_y, abs=1)
        viewer.close()


class TestDefaultAnchor:
    """Tests for _default_anchor (viewport center)."""

    def test_default_anchor_is_viewport_center(self, qapp: QApplication) -> None:
        """Default anchor should be at the vertical center of the viewport."""
        viewer = PDFViewer()
        viewer.resize(800, 600)
        qapp.processEvents()
        anchor = viewer._default_anchor()
        assert anchor.x() == 0
        viewport_h = viewer.viewport().height()
        assert anchor.y() == viewport_h // 2


class TestSetZoomAnimate:
    """Tests for set_zoom with animate=True vs animate=False."""

    def test_set_zoom_immediate(self, qapp: QApplication, sample_pdf: Path) -> None:
        """set_zoom with animate=False should apply immediately."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.set_zoom(2.5, animate=False)
        assert viewer.zoom == 2.5
        assert not viewer._animator.active
        viewer.close()

    def test_set_zoom_animated(self, qapp: QApplication, sample_pdf: Path) -> None:
        """set_zoom with animate=True should start the animator."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        viewer.set_zoom(2.5, animate=True)
        assert viewer._animator.active

        # Wait for animation to complete (~150ms + margin).
        QTest.qWait(300)

        assert viewer.zoom == pytest.approx(2.5, abs=0.01)
        assert not viewer._animator.active
        viewer.close()

    def test_set_zoom_no_animation_preserves_anchor(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Immediate set_zoom with explicit anchor should keep position."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        # Scroll to a known position.
        viewer.verticalScrollBar().setValue(100)
        anchor = QPoint(0, 200)

        viewer.set_zoom(2.0, anchor=anchor, animate=False)
        qapp.processEvents()

        # Something should have changed (zoom doubled, scroll adjusted).
        assert viewer.zoom == 2.0
        viewer.close()

    def test_set_zoom_with_keyboard_anchor_none(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """set_zoom(anchor=None) should use default viewport-center anchor."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        viewer.set_zoom(2.0, anchor=None, animate=False)
        assert viewer.zoom == 2.0
        viewer.close()


class TestSmoothZoomRendering:
    """Tests that verify correct rendering behavior during animated zoom."""

    def test_labels_have_scaled_contents(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Labels should have scaledContents enabled for smooth zoom."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        for label in viewer._labels:
            assert label.hasScaledContents()
        viewer.close()

    def test_labels_use_fixed_size_not_minimum(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """After set_zoom, labels should use fixed size (not just minimum)."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.set_zoom(2.0)
        qapp.processEvents()

        for i, label in enumerate(viewer._labels):
            page = viewer._doc.get_page(i)
            expected_h = int(page.height * 2.0)
            expected_w = int(page.width * 2.0)
            # With setFixedSize, height() and width() match the expected values.
            assert label.height() == expected_h
            assert label.width() == expected_w
        viewer.close()

    def test_animation_scales_pixmaps_during_zoom(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_apply_zoom_pixmaps should scale cached pixmaps to new size."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        # Render page 0 at the current zoom so the cache has it.
        viewer.set_zoom(1.5, animate=False)
        assert viewer._cache is not None
        original = viewer._cache.get(0)
        assert original is not None

        # Now simulate what the animator does at 2.5x:
        viewer._zoom = 2.5
        viewer._apply_zoom_pixmaps(2.5)
        qapp.processEvents()

        page0 = viewer._doc.get_page(0)
        expected_h = int(page0.height * 2.5)
        expected_w = int(page0.width * 2.5)
        assert viewer._labels[0].pixmap().height() == expected_h
        assert viewer._labels[0].pixmap().width() == expected_w

        # The original cached pixmap must remain unchanged.
        assert original.height() == int(page0.height * 1.5)
        viewer.close()

    def test_finish_zoom_replaces_scaled_with_hires(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """_finish_zoom should re-render at the current zoom."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        viewer.resize(800, 600)
        qapp.processEvents()

        # Simulate the end of an animation: zoom is 2.0, labels still at 1.5.
        viewer._zoom = 2.0
        if viewer._adapter is not None:
            viewer._adapter.zoom = 2.0
        viewer._update_label_sizes()
        qapp.processEvents()

        viewer._finish_zoom()
        qapp.processEvents()

        assert viewer._cache is not None
        pixmap = viewer._cache.get(0)
        assert pixmap is not None

        page0 = viewer._doc.get_page(0)
        assert pixmap.height() == int(page0.height * 2.0)
        assert pixmap.width() == int(page0.width * 2.0)
        viewer.close()

    def test_layout_is_horizontally_centered(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """Container layout should include horizontal centering."""
        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        alignment = viewer._layout.alignment()
        assert alignment & Qt.AlignmentFlag.AlignHCenter
        viewer.close()


class TestPDFViewerCloseEvent:
    """Tests for PDFViewer.closeEvent."""

    def test_close_event_calls_close(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """closeEvent should call close()."""
        from PyQt6.QtGui import QCloseEvent

        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        assert viewer._doc is not None

        event = QCloseEvent()
        viewer.closeEvent(event)
        assert viewer._doc is None
        assert viewer._cache is None

    def test_close_event_accepts_event(
        self, qapp: QApplication, sample_pdf: Path
    ) -> None:
        """closeEvent should accept the event (propagate to super)."""
        from PyQt6.QtGui import QCloseEvent

        viewer = PDFViewer()
        viewer.load_document(sample_pdf)
        event = QCloseEvent()
        viewer.closeEvent(event)
        viewer.close()
