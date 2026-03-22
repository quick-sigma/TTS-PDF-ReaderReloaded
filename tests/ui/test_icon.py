import pytest
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from pdfreader_reborn.ui.icon import Icon, SVGIcon, PngIcon, STANDARD_ICON_SIZE


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for icon tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestIconConstants:
    """Tests for icon module constants."""

    def test_standard_icon_size_is_24(self) -> None:
        """Industry standard toolbar icon size is 24x24 pixels."""
        assert STANDARD_ICON_SIZE == 24


class TestSVGIcon:
    """Tests for SVG icon loading and rendering."""

    def test_svg_icon_loads(self, icons_dir: Path) -> None:
        """SVGIcon should load from a valid SVG file path."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        assert icon is not None

    def test_svg_icon_returns_qicon(self, icons_dir: Path, qapp: QApplication) -> None:
        """to_qicon() should return a QIcon instance."""
        icon = SVGIcon(icons_dir / "zoomIn.svg")
        qicon = icon.to_qicon()
        assert isinstance(qicon, QIcon)
        assert not qicon.isNull()

    def test_svg_icon_default_size(self, icons_dir: Path) -> None:
        """Default icon size should be STANDARD_ICON_SIZE."""
        icon = SVGIcon(icons_dir / "openFile.svg")
        assert icon.size == STANDARD_ICON_SIZE

    def test_svg_icon_custom_size(self, icons_dir: Path) -> None:
        """Custom size should override default."""
        icon = SVGIcon(icons_dir / "openFile.svg", size=32)
        assert icon.size == 32

    def test_nonexistent_svg_raises(self, tmp_path: Path) -> None:
        """Loading a nonexistent SVG should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Icon not found"):
            SVGIcon(tmp_path / "missing.svg")


class TestPngIcon:
    """Tests for PNG icon loading and rendering."""

    def test_png_icon_loads(self, png_icon_path: Path) -> None:
        """PngIcon should load from a valid PNG file path."""
        icon = PngIcon(png_icon_path)
        assert icon is not None

    def test_png_icon_returns_qicon(
        self, png_icon_path: Path, qapp: QApplication
    ) -> None:
        """to_qicon() should return a QIcon instance."""
        icon = PngIcon(png_icon_path)
        qicon = icon.to_qicon()
        assert isinstance(qicon, QIcon)

    def test_png_icon_default_size(self, png_icon_path: Path) -> None:
        """Default icon size should be STANDARD_ICON_SIZE."""
        icon = PngIcon(png_icon_path)
        assert icon.size == STANDARD_ICON_SIZE

    def test_png_icon_custom_size(self, png_icon_path: Path) -> None:
        """Custom size should override default."""
        icon = PngIcon(png_icon_path, size=48)
        assert icon.size == 48

    def test_nonexistent_png_raises(self, tmp_path: Path) -> None:
        """Loading a nonexistent PNG should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Icon not found"):
            PngIcon(tmp_path / "missing.png")
