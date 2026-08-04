import pytest
from pypdf import PdfWriter


@pytest.fixture
def make_pdf(tmp_path):
    """Build a PDF whose pages have the given widths, so order is observable."""

    def _make(widths, height=595.0):
        writer = PdfWriter()
        for width in widths:
            writer.add_blank_page(width=width, height=height)
        path = tmp_path / f"sample-{len(widths)}.pdf"
        with open(path, "wb") as handle:
            writer.write(handle)
        return path

    return _make


@pytest.fixture
def make_sized_pdf(tmp_path):
    """Build a PDF whose pages have independent (width, height) pairs."""

    def _make(sizes):
        writer = PdfWriter()
        for width, height in sizes:
            writer.add_blank_page(width=width, height=height)
        path = tmp_path / f"sized-{len(sizes)}.pdf"
        with open(path, "wb") as handle:
            writer.write(handle)
        return path

    return _make
