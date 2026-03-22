import pytest
from pathlib import Path

from pdfreader_reborn.data.pdf_loader import PdfDocument, PdfLoadError


class TestPdfDocument:
    """Tests for PDF document loading and page access."""

    def test_load_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        """Loading a nonexistent file should raise PdfLoadError."""
        fake_path = tmp_path / "nonexistent.pdf"
        with pytest.raises(PdfLoadError, match="File not found"):
            PdfDocument(fake_path)

    def test_load_invalid_pdf_raises_error(self, tmp_path: Path) -> None:
        """Loading a corrupt file should raise PdfLoadError."""
        bad_file = tmp_path / "bad.pdf"
        bad_file.write_text("not a pdf")
        with pytest.raises(PdfLoadError, match="Invalid PDF"):
            PdfDocument(bad_file)

    def test_page_count(self, sample_pdf: Path) -> None:
        """Document should report correct number of pages."""
        doc = PdfDocument(sample_pdf)
        assert doc.page_count == 3
        doc.close()

    def test_get_page_returns_renderable_page(self, sample_pdf: Path) -> None:
        """Getting a valid page index returns a page object."""
        doc = PdfDocument(sample_pdf)
        page = doc.get_page(0)
        assert page is not None
        assert page.page_number == 0
        doc.close()

    def test_get_page_invalid_index_raises(self, sample_pdf: Path) -> None:
        """Out-of-range page index should raise IndexError."""
        doc = PdfDocument(sample_pdf)
        with pytest.raises(IndexError):
            doc.get_page(999)
        doc.close()

    def test_render_page_returns_bytes(self, sample_pdf: Path) -> None:
        """Rendering a page should return raw image bytes (PNG)."""
        doc = PdfDocument(sample_pdf)
        img_bytes = doc.render_page(0, zoom=1.0)
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0
        # PNG signature
        assert img_bytes[:4] == b"\x89PNG"
        doc.close()

    def test_context_manager_closes_document(self, sample_pdf: Path) -> None:
        """Using 'with' statement should close the document automatically."""
        with PdfDocument(sample_pdf) as doc:
            assert doc.page_count == 3
        # After exiting context, internal fitz.Document should be closed
        assert doc._doc is None

    def test_extract_text_from_page(self, sample_pdf: Path) -> None:
        """Should extract text content from a page."""
        with PdfDocument(sample_pdf) as doc:
            text = doc.extract_text(0)
            assert isinstance(text, str)
            assert len(text) > 0

    def test_metadata(self, sample_pdf: Path) -> None:
        """Document should expose metadata dict."""
        with PdfDocument(sample_pdf) as doc:
            meta = doc.metadata
            assert isinstance(meta, dict)
