from pathlib import Path

import fitz


class PdfLoadError(Exception):
    """Raised when a PDF file cannot be loaded."""


class PdfPage:
    """Lightweight reference to a single page in a document."""

    __slots__ = ("_doc", "page_number", "width", "height")

    def __init__(self, doc: fitz.Document, page_number: int) -> None:
        self._doc = doc
        self.page_number = page_number
        page = doc[page_number]
        self.width = page.rect.width
        self.height = page.rect.height

    def render(self, zoom: float = 1.0) -> bytes:
        """Render this page to PNG bytes at the given zoom factor."""
        mat = fitz.Matrix(zoom, zoom)
        pix = self._doc[self.page_number].get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def extract_text(self) -> str:
        """Extract text content from this page."""
        text = self._doc[self.page_number].get_text()
        return str(text) if text else ""


class PdfDocument:
    """Load a PDF into memory and provide page-level access.

    Usage::

        with PdfDocument(Path("report.pdf")) as doc:
            img = doc.render_page(0, zoom=2.0)
            text = doc.extract_text(0)
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._doc: fitz.Document | None = None

        if not self._path.exists():
            raise PdfLoadError(f"File not found: {self._path}")

        try:
            self._doc = fitz.open(str(self._path))
        except Exception as exc:
            raise PdfLoadError(f"Invalid PDF: {self._path}") from exc

    @property
    def page_count(self) -> int:
        if self._doc is None:
            return 0
        return len(self._doc)

    @property
    def metadata(self) -> dict:
        if self._doc is None:
            return {}
        return self._doc.metadata or {}

    def get_page(self, index: int) -> PdfPage:
        """Return a PdfPage wrapper for the given zero-based index."""
        if self._doc is None:
            raise RuntimeError("Document is closed")
        if index < 0 or index >= len(self._doc):
            raise IndexError(
                f"Page index {index} out of range (0-{len(self._doc) - 1})"
            )
        return PdfPage(self._doc, index)

    def render_page(self, index: int, zoom: float = 1.0) -> bytes:
        """Render a page and return raw PNG bytes."""
        page = self.get_page(index)
        return page.render(zoom)

    def extract_text(self, index: int) -> str:
        """Extract text from a single page."""
        page = self.get_page(index)
        return str(page.extract_text())

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def __enter__(self) -> "PdfDocument":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
