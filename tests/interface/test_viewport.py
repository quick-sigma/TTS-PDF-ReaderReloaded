import pytest
from pathlib import Path

from pdfreader_reborn.interface.viewport import PageRenderTask


class TestPageRenderTask:
    """Tests for lazy page rendering task metadata."""

    def test_task_has_page_number(self) -> None:
        task = PageRenderTask(page_number=5, zoom=1.5)
        assert task.page_number == 5

    def test_task_has_zoom(self) -> None:
        task = PageRenderTask(page_number=0, zoom=2.0)
        assert task.zoom == 2.0

    def test_task_not_rendered_initially(self) -> None:
        task = PageRenderTask(page_number=0, zoom=1.0)
        assert task.pixmap is None
        assert not task.is_rendered

    def test_task_equality(self) -> None:
        a = PageRenderTask(page_number=1, zoom=1.0)
        b = PageRenderTask(page_number=1, zoom=1.0)
        c = PageRenderTask(page_number=1, zoom=2.0)
        assert a == b
        assert a != c
