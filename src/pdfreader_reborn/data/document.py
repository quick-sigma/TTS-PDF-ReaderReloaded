# src/pdfreader_reborn/data/document.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

import fitz


class PdfLoadError(Exception):
    """Raised when a PDF file cannot be loaded."""


@runtime_checkable
class PageRenderer(Protocol):
    """Protocol for page rendering backends.

    Any object that implements render() and extract_text() for a given
    page number can serve as a renderer. This decouples Page from
    the specific PDF library used.
    """

    def render(self, page_number: int, zoom: float) -> bytes:
        """Render a page to PNG bytes."""
        ...

    def extract_text(self, page_number: int) -> str:
        """Extract text from a page."""
        ...


class FitzRenderer:
    """PyMuPDF-based page renderer.

    Wraps fitz.Document to implement the PageRenderer protocol.
    All fitz-specific logic is contained here.
    """

    __slots__ = ("_doc",)

    def __init__(self, doc: fitz.Document) -> None:
        """Initialize with a fitz document.

        Args:
            doc: An open fitz.Document instance.
        """
        self._doc = doc

    def render(self, page_number: int, zoom: float) -> bytes:
        """Render a page to PNG bytes using PyMuPDF.

        Args:
            page_number: Zero-based page index.
            zoom: Zoom factor for rendering.

        Returns:
            Raw PNG image bytes.
        """
        mat = fitz.Matrix(zoom, zoom)
        pix = self._doc[page_number].get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def extract_text(self, page_number: int) -> str:
        """Extract text from a page using PyMuPDF.

        Args:
            page_number: Zero-based page index.

        Returns:
            The extracted text as a string.
        """
        text = self._doc[page_number].get_text()
        return str(text) if text else ""


class Page:
    """Lightweight reference to a single page in a document.

    Delegates rendering and text extraction to a PageRenderer,
    making it backend-agnostic.

    Attributes:
        page_number: Zero-based page index.
        width: Page width in points.
        height: Page height in points.
    """

    __slots__ = ("_renderer", "page_number", "width", "height")

    def __init__(
        self,
        renderer: PageRenderer,
        page_number: int,
        width: float,
        height: float,
    ) -> None:
        """Initialize the page reference.

        Args:
            renderer: The rendering backend.
            page_number: Zero-based page index.
            width: Page width in points.
            height: Page height in points.
        """
        self._renderer = renderer
        self.page_number = page_number
        self.width = width
        self.height = height

    def render(self, zoom: float = 1.0) -> bytes:
        """Render this page to PNG bytes at the given zoom factor.

        Args:
            zoom: Zoom factor for rendering.

        Returns:
            Raw PNG image bytes.
        """
        return self._renderer.render(self.page_number, zoom)

    def extract_text(self) -> str:
        """Extract text content from this page.

        Returns:
            The extracted text as a string.
        """
        return self._renderer.extract_text(self.page_number)


class Document(ABC):
    """Abstract base class for document adapters.

    A document provides page-level access to file content, including
    rendering pages to images and extracting text. Subclasses must
    implement all abstract methods for their specific format.

    Usage::

        with PdfDocument(Path("report.pdf")) as doc:
            img = doc.render_page(0, zoom=2.0)
            text = doc.extract_text(0)
    """

    @property
    @abstractmethod
    def page_count(self) -> int:
        """Return the total number of pages."""

    @property
    @abstractmethod
    def metadata(self) -> dict:
        """Return document metadata as a dictionary."""

    @abstractmethod
    def get_page(self, index: int) -> Page:
        """Return a page wrapper for the given index.

        Args:
            index: Zero-based page index.

        Returns:
            A Page object for the requested page.

        Raises:
            IndexError: If the index is out of range.
        """

    @abstractmethod
    def render_page(self, index: int, zoom: float = 1.0) -> bytes:
        """Render a page and return raw image bytes.

        Args:
            index: Zero-based page index.
            zoom: Zoom factor for rendering.

        Returns:
            Raw PNG image bytes.
        """

    @abstractmethod
    def extract_text(self, index: int) -> str:
        """Extract text content from a page.

        Args:
            index: Zero-based page index.

        Returns:
            The extracted text as a string.
        """

    @abstractmethod
    def close(self) -> None:
        """Close the document and release resources."""

    def __enter__(self) -> "Document":
        """Enter context manager."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Exit context manager and close the document."""
        self.close()


class PdfDocument(Document):
    """PDF document adapter using PyMuPDF.

    All fitz-specific logic is delegated to FitzRenderer. The document
    itself only manages lifecycle and page indexing.

    Usage::

        with PdfDocument(Path("report.pdf")) as doc:
            print(f"Pages: {doc.page_count}")
            img = doc.render_page(0, zoom=2.0)
            text = doc.extract_text(0)
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize the PDF document.

        Args:
            path: Path to the PDF file.

        Raises:
            PdfLoadError: If the file does not exist or is invalid.
        """
        self._path = Path(path)
        self._doc: fitz.Document | None = None
        self._renderer: FitzRenderer | None = None

        if not self._path.exists():
            msg = f"File not found: {self._path}"
            raise PdfLoadError(msg)

        try:
            self._doc = fitz.open(str(self._path))
            self._renderer = FitzRenderer(self._doc)
        except Exception as exc:
            msg = f"Invalid PDF: {self._path}"
            raise PdfLoadError(msg) from exc

    @property
    def page_count(self) -> int:
        """Return the total number of pages."""
        if self._doc is None:
            return 0
        return len(self._doc)

    @property
    def metadata(self) -> dict:
        """Return PDF metadata as a dictionary."""
        if self._doc is None:
            return {}
        return self._doc.metadata or {}

    def get_page(self, index: int) -> Page:
        """Return a Page wrapper for the given zero-based index.

        Args:
            index: Zero-based page index.

        Returns:
            A Page object backed by FitzRenderer.

        Raises:
            RuntimeError: If the document is closed.
            IndexError: If the index is out of range.
        """
        if self._doc is None or self._renderer is None:
            msg = "Document is closed"
            raise RuntimeError(msg)
        if index < 0 or index >= len(self._doc):
            msg = f"Page index {index} out of range (0-{len(self._doc) - 1})"
            raise IndexError(msg)

        fitz_page = self._doc[index]
        return Page(
            renderer=self._renderer,
            page_number=index,
            width=fitz_page.rect.width,
            height=fitz_page.rect.height,
        )

    def render_page(self, index: int, zoom: float = 1.0) -> bytes:
        """Render a page and return raw PNG bytes.

        Args:
            index: Zero-based page index.
            zoom: Zoom factor for rendering.

        Returns:
            Raw PNG image bytes.
        """
        page = self.get_page(index)
        return page.render(zoom)

    def extract_text(self, index: int) -> str:
        """Extract text from a single page.

        Args:
            index: Zero-based page index.

        Returns:
            The extracted text as a string.
        """
        page = self.get_page(index)
        return page.extract_text()

    def close(self) -> None:
        """Close the document and release resources."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None
            self._renderer = None
