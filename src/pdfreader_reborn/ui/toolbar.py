# src/pdfreader_reborn/ui/toolbar.py

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from pathlib import Path

from PyQt6.QtWidgets import QToolBar

from pdfreader_reborn.ui.icon import SVGIcon
from pdfreader_reborn.ui.button import Button, ToolbarElement
from pdfreader_reborn.strings import t


class Toolbar(ABC):
    """Abstract base class for toolbars with linked list structure.

    A toolbar is an ordered collection of ToolbarElements linked together.
    This design allows plugins to insert and remove elements dynamically
    without rebuilding the entire toolbar.

    Subclasses must implement ``to_qtoolbar()`` to produce the Qt widget.

    Usage::

        toolbar = NavigationToolbar(icons_dir, on_open=open_file)
        main_window.addToolBar(toolbar.to_qtoolbar())
    """

    def __init__(self) -> None:
        """Initialize an empty toolbar."""
        self._head: ToolbarElement | None = None
        self._tail: ToolbarElement | None = None
        self._size: int = 0

    @property
    def head(self) -> ToolbarElement | None:
        """Return the first element in the linked list."""
        return self._head

    def add(self, element: ToolbarElement) -> None:
        """Append an element to the end of the linked list.

        Args:
            element: The ToolbarElement to append.
        """
        if self._head is None:
            self._head = element
            self._tail = element
        else:
            assert self._tail is not None
            self._tail.next = element
            self._tail = element
        self._size += 1

    def add_first(self, element: ToolbarElement) -> None:
        """Prepend an element to the beginning of the linked list.

        Args:
            element: The ToolbarElement to prepend.
        """
        element.next = self._head
        self._head = element
        if self._tail is None:
            self._tail = element
        self._size += 1

    def remove(self, element: ToolbarElement) -> None:
        """Remove an element from the linked list.

        Args:
            element: The ToolbarElement to remove.

        Raises:
            ValueError: If the element is not in the list.
        """
        if self._head is None:
            msg = "Element not found in toolbar"
            raise ValueError(msg)

        if self._head is element:
            self._head = self._head.next
            if self._head is None:
                self._tail = None
            self._size -= 1
            return

        current = self._head
        while current.next is not None:
            if current.next is element:
                current.next = element.next
                if element is self._tail:
                    self._tail = current
                self._size -= 1
                return
            current = current.next

        msg = "Element not found in toolbar"
        raise ValueError(msg)

    def __iter__(self) -> Iterator[ToolbarElement]:
        """Iterate over all elements in order."""
        current = self._head
        while current is not None:
            yield current
            current = current.next

    def __len__(self) -> int:
        """Return the number of elements in the toolbar."""
        return self._size

    @abstractmethod
    def to_qtoolbar(self) -> QToolBar:
        """Convert to a QToolBar for Qt integration.

        Returns:
            A fully configured QToolBar widget.
        """


class NavigationToolbar(Toolbar):
    """Navigation toolbar with Zoom In and Zoom Out buttons.

    Open File is provided by the plugin system (see ``OpenFilePlugin``).
    Buttons emit signals via callbacks. Keyboard shortcuts are NOT set
    on QActions — they are managed exclusively by KeyboardManager to
    prevent double-dispatch.

    Usage::

        toolbar = NavigationToolbar(
            icons_dir,
            on_zoom_in=lambda: signals.zoom_in.emit(),
            on_zoom_out=lambda: signals.zoom_out.emit(),
        )
        kernel = Kernel()
        open_buttons = kernel.get_toolbar_buttons(icons_dir)
        for btn in reversed(open_buttons):
            toolbar.add_first(btn)
        main_window.addToolBar(toolbar.to_qtoolbar())
    """

    def __init__(
        self,
        icons_dir: Path,
        on_zoom_in: Callable[[], None] | None = None,
        on_zoom_out: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the navigation toolbar.

        Args:
            icons_dir: Path to the directory containing SVG icons.
            on_zoom_in: Callback for the Zoom In button.
            on_zoom_out: Callback for the Zoom Out button.
        """
        super().__init__()
        self._icons_dir = icons_dir
        self._on_zoom_in = on_zoom_in
        self._on_zoom_out = on_zoom_out
        self._build()

    def _build(self) -> None:
        """Construct toolbar elements. No shortcuts — KeyboardManager owns those."""
        zoom_in_btn = Button(
            icon=SVGIcon(self._icons_dir / "zoomIn.svg"),
            label=t("toolbar.zoom_in.label"),
            tooltip=t("toolbar.zoom_in.tooltip"),
            on_click=self._on_zoom_in,
        )
        zoom_out_btn = Button(
            icon=SVGIcon(self._icons_dir / "zoomOut.svg"),
            label=t("toolbar.zoom_out.label"),
            tooltip=t("toolbar.zoom_out.tooltip"),
            on_click=self._on_zoom_out,
        )
        self.add(zoom_in_btn)
        self.add(zoom_out_btn)

    def to_qtoolbar(self) -> QToolBar:
        """Convert to a QToolBar with all navigation actions.

        Returns:
            A movable QToolBar with Open, Zoom In, and Zoom Out actions.
        """
        toolbar = QToolBar(t("toolbar.navigation.name"))
        toolbar.setMovable(True)
        self._actions: list = []
        for element in self:
            action = element.to_qaction()
            self._actions.append(action)
            toolbar.addAction(action)
        return toolbar
