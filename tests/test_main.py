import sys
from unittest.mock import patch

from pdfreader_reborn.data.pdf_loader import PdfDocument


def test_pdf_document_exists() -> None:
    """Verify PdfDocument class is importable."""
    assert PdfDocument is not None


def test_main_module_importable() -> None:
    """Verify main module can be imported without starting GUI."""
    with patch("main.QApplication"):
        import main as main_module

        assert hasattr(main_module, "main")
