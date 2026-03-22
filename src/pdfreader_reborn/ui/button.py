from abc import ABC, abstractmethod
from collections.abc import Callable

from PyQt6.QtGui import QAction

from pdfreader_reborn.ui.icon import Icon


class ToolbarElement(ABC):
    """Abstract base class for toolbar elements in a linked list.

    Toolbars are composed of a linked list of ToolbarElements. Each element
    knows about the next element in the chain, enabling dynamic insertion
    and removal without rebuilding the entire toolbar.

    Attributes:
        _next: Reference to the next element, or None if this is the tail.
    """

    def __init__(self) -> None:
        """Initialize the element with no successor."""
        self._next: "ToolbarElement | None" = None

    @property
    def next(self) -> "ToolbarElement | None":
        """Return the next element in the linked list."""
        return self._next

    @next.setter
    def next(self, value: "ToolbarElement | None") -> None:
        """Set the next element in the linked list.

        Args:
            value: The next ToolbarElement, or None to mark as tail.
        """
        self._next = value

    @abstractmethod
    def to_qaction(self) -> QAction:
        """Convert this element to a QAction for Qt toolbar integration.

        Returns:
            A QAction instance ready to be added to a QToolBar.
        """


class Button(ToolbarElement):
    """A clickable toolbar button with icon, label, and optional callback.

    Buttons are the primary interactive element in a toolbar. Each button
    wraps an Icon and produces a QAction that can be connected to a callback.

    Usage::

        icon = SVGIcon(Path("icons/openFile.svg"))
        button = Button(
            icon=icon,
            label="Open PDF",
            tooltip="Open a PDF file",
            shortcut="Ctrl+O",
            on_click=open_file,
        )
        toolbar.addAction(button.to_qaction())
    """

    def __init__(
        self,
        icon: Icon,
        label: str,
        tooltip: str = "",
        shortcut: str = "",
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the button.

        Args:
            icon: The icon to display on the button.
            label: Text label for the button.
            tooltip: Hover tooltip text. Defaults to empty string.
            shortcut: Keyboard shortcut (e.g., "Ctrl+O"). Defaults to empty.
            on_click: Callback invoked when the button is clicked.
        """
        super().__init__()
        self._icon = icon
        self._label = label
        self._tooltip = tooltip
        self._shortcut = shortcut
        self._on_click = on_click

    @property
    def icon(self) -> Icon:
        """Return the button's icon."""
        return self._icon

    @property
    def label(self) -> str:
        """Return the button's label text."""
        return self._label

    @property
    def tooltip(self) -> str:
        """Return the button's tooltip text."""
        return self._tooltip

    @property
    def shortcut(self) -> str:
        """Return the button's keyboard shortcut."""
        return self._shortcut

    def to_qaction(self) -> QAction:
        """Convert to a QAction with icon, text, tooltip, and shortcut.

        Returns:
            A fully configured QAction ready for toolbar insertion.
        """
        action = QAction(self._icon.to_qicon(), self._label)
        if self._tooltip:
            action.setToolTip(self._tooltip)
        if self._shortcut:
            action.setShortcut(self._shortcut)
        if self._on_click is not None:
            action.triggered.connect(self._on_click)
        return action
