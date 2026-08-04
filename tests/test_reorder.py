import pytest
from pypdf import PdfReader

from typst_post.reorder import reorder


def widths_of(path):
    return [float(page.mediabox.width) for page in PdfReader(str(path)).pages]


def test_reorder(make_pdf, tmp_path):
    source = make_pdf([100.0, 110.0, 120.0, 130.0])
    output = tmp_path / "out.pdf"
    reorder(source, "4,1,2,3", output)
    assert widths_of(output) == [130.0, 100.0, 110.0, 120.0]


def test_drop_and_duplicate(make_pdf, tmp_path):
    source = make_pdf([100.0, 110.0, 120.0])
    output = tmp_path / "out.pdf"
    reorder(source, "2,2", output)
    assert widths_of(output) == [110.0, 110.0]


def test_invalid_order(make_pdf, tmp_path):
    source = make_pdf([100.0])
    with pytest.raises(ValueError):
        reorder(source, "2", tmp_path / "out.pdf")
