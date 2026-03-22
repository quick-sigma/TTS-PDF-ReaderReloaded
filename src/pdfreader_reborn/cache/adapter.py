"""Page adapter protocol for the LRU cache.

Any document type that can provide pages by index implements this
protocol.  The adapter is generic over the page value type ``V``
(e.g. bytes, QPixmap, custom data).
"""

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class PageAdapter(Protocol[T]):
    """Protocol for accessing pages by index from any document source.

    The LRU cache delegates page loading to an adapter so it stays
    decoupled from the concrete document format (PDF, EPUB, images …).

    Implementations must provide:
        - ``page_count``: total number of pages.
        - ``load_page(index)``: return the page content at ``index``.
    """

    @property
    def page_count(self) -> int:
        """Return the total number of pages."""
        ...

    def load_page(self, index: int) -> T:
        """Load and return the page at the given index.

        Args:
            index: Zero-based page index.

        Returns:
            The page content (type depends on the adapter).

        Raises:
            IndexError: If ``index`` is out of range.
        """
        ...
