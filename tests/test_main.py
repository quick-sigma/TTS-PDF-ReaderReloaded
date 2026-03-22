from unittest.mock import patch

from pdfreader_reborn.data.document import PdfDocument


def test_pdf_document_exists() -> None:
    """Verify PdfDocument class is importable."""
    assert PdfDocument is not None


def test_main_module_importable() -> None:
    """Verify main module can be imported without starting GUI."""
    with patch("main.QApplication"):
        import main as main_module

        assert hasattr(main_module, "main")


def test_new_architecture_modules_importable() -> None:
    """Verify all new architecture modules are importable."""
    from pdfreader_reborn.ui.icon import Icon, SVGIcon, PngIcon
    from pdfreader_reborn.ui.button import ToolbarElement, Button
    from pdfreader_reborn.ui.toolbar import Toolbar, NavigationToolbar
    from pdfreader_reborn.ui.viewer import Viewer, PDFViewer
    from pdfreader_reborn.data.document import Document, PdfDocument
    from pdfreader_reborn.kernel import Kernel
    from pdfreader_reborn.kernel.hooks import ToolbarHooks
    from pdfreader_reborn.plugins import OpenFilePlugin

    assert Icon is not None
    assert SVGIcon is not None
    assert PngIcon is not None
    assert ToolbarElement is not None
    assert Button is not None
    assert Toolbar is not None
    assert NavigationToolbar is not None
    assert Viewer is not None
    assert PDFViewer is not None
    assert Document is not None
    assert PdfDocument is not None
    assert Kernel is not None
    assert ToolbarHooks is not None
    assert OpenFilePlugin is not None
