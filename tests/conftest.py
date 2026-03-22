import pytest
from pathlib import Path

import fitz

ICONS_DIR = Path(__file__).parent.parent / "icons"


@pytest.fixture
def icons_dir() -> Path:
    """Return path to the project's icons directory."""
    assert ICONS_DIR.exists(), f"Icons directory not found: {ICONS_DIR}"
    return ICONS_DIR


@pytest.fixture
def png_icon_path(tmp_path: Path) -> Path:
    """Create a minimal valid PNG file for testing."""
    png_path = tmp_path / "test_icon.png"
    # Minimal 1x1 red PNG
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
        b"\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    png_path.write_bytes(png_bytes)
    return png_path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a 3-page sample PDF for testing."""
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()

    for i in range(3):
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text(
            (72, 100),
            f"Page {i + 1} - Hello from pdfreader-reborn!",
            fontsize=14,
        )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path
