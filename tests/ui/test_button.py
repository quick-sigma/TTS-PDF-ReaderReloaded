import pytest
from pathlib import Path
from unittest.mock import Mock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QAction

from pdfreader_reborn.ui.icon import SVGIcon
from pdfreader_reborn.ui.button import ToolbarElement, Button


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for button tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestToolbarElement:
    """Tests for the ToolbarElement abstract base class."""

    def test_toolbar_element_is_abstract(self) -> None:
        """ToolbarElement cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ToolbarElement()  # type: ignore[abstract]


class TestButton:
    """Tests for the Button concrete implementation."""

    def test_button_implements_toolbar_element(self, icons_dir: Path) -> None:
        """Button should be a subclass of ToolbarElement."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Test")
        assert isinstance(button, ToolbarElement)

    def test_button_creates_qaction(self, icons_dir: Path, qapp: QApplication) -> None:
        """to_qaction() should return a QAction."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open")
        action = button.to_qaction()
        assert isinstance(action, QAction)

    def test_button_has_icon(self, icons_dir: Path) -> None:
        """Button should store the provided icon."""
        icon = SVGIcon(icons_dir / "zoomIn.svg")
        button = Button(icon=icon, label="Zoom In")
        assert button.icon is icon

    def test_button_has_label(self, icons_dir: Path) -> None:
        """Button should store the provided label."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open PDF")
        assert button.label == "Open PDF"

    def test_button_has_tooltip(self, icons_dir: Path) -> None:
        """Button should store the provided tooltip."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open", tooltip="Open a PDF file")
        assert button.tooltip == "Open a PDF file"

    def test_button_tooltip_default_empty(self, icons_dir: Path) -> None:
        """Tooltip should default to empty string."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open")
        assert button.tooltip == ""

    def test_button_has_shortcut(self, icons_dir: Path) -> None:
        """Button should store the provided shortcut."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open", shortcut="Ctrl+O")
        assert button.shortcut == "Ctrl+O"

    def test_button_next_is_none_by_default(self, icons_dir: Path) -> None:
        """Next element should be None by default (end of list)."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open")
        assert button.next is None

    def test_button_linking(self, icons_dir: Path) -> None:
        """Buttons can be linked via the next property."""
        icon1 = SVGIcon(icons_dir / "openFile.svg")
        icon2 = SVGIcon(icons_dir / "zoomIn.svg")
        btn1 = Button(icon=icon1, label="Open")
        btn2 = Button(icon=icon2, label="Zoom In")
        btn1.next = btn2
        assert btn1.next is btn2
        assert btn2.next is None

    def test_button_on_click_callback(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """Clicking the action should invoke the callback."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        callback = Mock()
        button = Button(icon=icon, label="Open", on_click=callback)
        action = button.to_qaction()
        action.trigger()
        callback.assert_called_once()

    def test_button_no_callback_does_not_raise(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """Clicking without a callback should not raise."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open")
        action = button.to_qaction()
        action.trigger()  # Should not raise

    def test_button_qaction_has_correct_text(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """The QAction text should match the button label."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open PDF")
        action = button.to_qaction()
        assert action.text() == "Open PDF"

    def test_button_qaction_has_tooltip(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """The QAction tooltip should match the button tooltip."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open", tooltip="Open file")
        action = button.to_qaction()
        assert action.toolTip() == "Open file"

    def test_button_qaction_has_shortcut(
        self, icons_dir: Path, qapp: QApplication
    ) -> None:
        """The QAction shortcut should match the button shortcut."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        button = Button(icon=icon, label="Open", shortcut="Ctrl+O")
        action = button.to_qaction()
        assert action.shortcut().toString() == "Ctrl+O"
