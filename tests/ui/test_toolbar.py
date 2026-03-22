# tests/ui/test_toolbar.py

import pytest
from pathlib import Path
from unittest.mock import Mock

from PyQt6.QtWidgets import QApplication, QToolBar

from pdfreader_reborn.ui.icon import SVGIcon
from pdfreader_reborn.ui.button import Button
from pdfreader_reborn.ui.toolbar import Toolbar, NavigationToolbar
from pdfreader_reborn.strings import t


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for toolbar tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestToolbar:
    """Tests for the Toolbar abstract base class."""

    def test_toolbar_is_abstract(self) -> None:
        """Toolbar cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Toolbar()  # type: ignore[abstract]


class TestNavigationToolbar:
    """Tests for the NavigationToolbar concrete implementation."""

    def test_navigation_toolbar_implements_toolbar(self, icons_dir: Path) -> None:
        """NavigationToolbar should be a subclass of Toolbar."""
        toolbar = NavigationToolbar(icons_dir)
        assert isinstance(toolbar, Toolbar)

    def test_navigation_toolbar_has_zoom_buttons(self, icons_dir: Path) -> None:
        """NavigationToolbar should contain zoom in and zoom out buttons."""
        toolbar = NavigationToolbar(icons_dir)
        elements = list(toolbar)
        labels = [e.label for e in elements]
        assert t("toolbar.zoom_in.label") in labels
        assert t("toolbar.zoom_out.label") in labels

    def test_navigation_toolbar_creates_qtoolbar(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """to_qtoolbar() should return a QToolBar."""
        toolbar = NavigationToolbar(icons_dir)
        qtoolbar = toolbar.to_qtoolbar()
        assert isinstance(qtoolbar, QToolBar)

    def test_navigation_toolbar_qtoolbar_has_actions(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """The QToolBar should contain actions for each button."""
        toolbar = NavigationToolbar(icons_dir)
        qtoolbar = toolbar.to_qtoolbar()
        actions = qtoolbar.actions()
        assert len(actions) >= 2

    def test_navigation_toolbar_no_shortcuts_on_actions(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """Actions should NOT have shortcuts — KeyboardManager owns those."""
        toolbar = NavigationToolbar(icons_dir)
        qtoolbar = toolbar.to_qtoolbar()
        for action in qtoolbar.actions():
            assert action.shortcut().isEmpty(), (
                f"Action '{action.text()}' has shortcut '{action.shortcut().toString()}'"
                " but shortcuts should be managed by KeyboardManager only"
            )

    def test_navigation_toolbar_tooltips_show_shortcuts(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """Tooltips should mention the keyboard shortcut for discoverability."""
        toolbar = NavigationToolbar(icons_dir)
        qtoolbar = toolbar.to_qtoolbar()
        tooltips = [a.toolTip() for a in qtoolbar.actions()]
        assert any("Ctrl+=" in t for t in tooltips)
        assert any("Ctrl+-" in t for t in tooltips)

    def test_navigation_toolbar_head_is_first_element(self, icons_dir: Path) -> None:
        """Head should be the Zoom In button."""
        toolbar = NavigationToolbar(icons_dir)
        assert toolbar.head is not None
        assert toolbar.head.label == t("toolbar.zoom_in.label")

    def test_navigation_toolbar_linked_list_order(self, icons_dir: Path) -> None:
        """Elements should be linked in insertion order."""
        toolbar = NavigationToolbar(icons_dir)
        elements = list(toolbar)
        labels = [e.label for e in elements]
        assert labels == [t("toolbar.zoom_in.label"), t("toolbar.zoom_out.label")]

    def test_navigation_toolbar_add_element(self, icons_dir: Path) -> None:
        """Adding an element appends it to the linked list."""
        toolbar = NavigationToolbar(icons_dir)
        icon = SVGIcon(icons_dir / "zoomOut.svg")
        button = Button(icon=icon, label="Custom")
        toolbar.add(button)
        elements = list(toolbar)
        assert elements[-1].label == "Custom"

    def test_navigation_toolbar_add_first_element(self, icons_dir: Path) -> None:
        """add_first should prepend an element to the linked list."""
        toolbar = NavigationToolbar(icons_dir)
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open PDF")
        toolbar.add_first(button)
        assert toolbar.head is not None
        assert toolbar.head.label == "Open PDF"
        assert len(toolbar) == 3

    def test_navigation_toolbar_remove_element(self, icons_dir: Path) -> None:
        """Removing an element unlinks it from the list."""
        toolbar = NavigationToolbar(icons_dir)
        elements_before = list(toolbar)
        target = elements_before[0]
        toolbar.remove(target)
        elements_after = list(toolbar)
        assert target not in elements_after
        assert len(elements_after) == len(elements_before) - 1

    def test_navigation_toolbar_iter(self, icons_dir: Path) -> None:
        """Iteration should yield all elements in order."""
        toolbar = NavigationToolbar(icons_dir)
        elements = list(toolbar)
        assert len(elements) == 2

    def test_navigation_toolbar_len(self, icons_dir: Path) -> None:
        """len() should return the number of elements."""
        toolbar = NavigationToolbar(icons_dir)
        assert len(toolbar) == 2

    def test_navigation_toolbar_on_zoom_in_callback(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """on_zoom_in callback should be wired to the Zoom In button."""
        callback = Mock()
        toolbar = NavigationToolbar(icons_dir, on_zoom_in=callback)
        qtoolbar = toolbar.to_qtoolbar()
        zoom_in_action = qtoolbar.actions()[0]
        zoom_in_action.trigger()
        callback.assert_called_once()

    def test_navigation_toolbar_on_zoom_out_callback(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """on_zoom_out callback should be wired to the Zoom Out button."""
        callback = Mock()
        toolbar = NavigationToolbar(icons_dir, on_zoom_out=callback)
        qtoolbar = toolbar.to_qtoolbar()
        zoom_out_action = qtoolbar.actions()[1]
        zoom_out_action.trigger()
        callback.assert_called_once()
