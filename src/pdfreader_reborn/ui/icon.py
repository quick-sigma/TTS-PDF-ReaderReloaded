from abc import ABC, abstractmethod
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap

STANDARD_ICON_SIZE: int = 24


class Icon(ABC):
    """Abstract base class for all icon formats.

    Provides a uniform interface for loading and converting icons
    regardless of their source format (SVG, PNG, etc.).

    Attributes:
        _path: Path to the icon file.
        _size: Display size in pixels (square).
    """

    def __init__(self, path: Path, size: int = STANDARD_ICON_SIZE) -> None:
        """Initialize the icon.

        Args:
            path: Path to the icon file.
            size: Display size in pixels. Defaults to STANDARD_ICON_SIZE.

        Raises:
            FileNotFoundError: If the icon file does not exist.
        """
        if not path.exists():
            msg = f"Icon not found: {path}"
            raise FileNotFoundError(msg)
        self._path = path
        self._size = size

    @property
    def size(self) -> int:
        """Return the icon display size in pixels."""
        return self._size

    @property
    def path(self) -> Path:
        """Return the icon file path."""
        return self._path

    @abstractmethod
    def to_qicon(self) -> QIcon:
        """Convert to a QIcon for use in Qt widgets.

        Returns:
            A QIcon instance ready for use in toolbars or menus.
        """


class SVGIcon(Icon):
    """Icon loaded from an SVG file.

    SVG icons are resolution-independent and scale cleanly at any size.
    They are rendered on-demand by Qt's SVG engine.

    Usage::

        icon = SVGIcon(Path("icons/openFile.svg"))
        qaction.setIcon(icon.to_qicon())
    """

    def to_qicon(self) -> QIcon:
        """Convert SVG to QIcon.

        Returns:
            A QIcon backed by the SVG file.
        """
        return QIcon(str(self._path))


class PngIcon(Icon):
    """Icon loaded from a PNG file.

    PNG icons are raster images with fixed resolution. They are best
    used when SVG is unavailable or for bitmap-based icon sets.

    Usage::

        icon = PngIcon(Path("icons/custom.png"), size=32)
        qaction.setIcon(icon.to_qicon())
    """

    def to_qicon(self) -> QIcon:
        """Convert PNG to QIcon, scaled to the configured size.

        Returns:
            A QIcon backed by the PNG file, scaled to self.size.
        """
        pixmap = QPixmap(str(self._path))
        scaled = pixmap.scaled(
            QSize(self._size, self._size),
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation,
        )
        return QIcon(scaled)
