import pytest
from pypdf import PdfReader

from typst_post.rotate import parse_spec, rotate


def test_parse_spec_variants():
    assert parse_spec("2:180", 8) == ([1], 180)
    assert parse_spec("5-7:90", 8) == ([4, 5, 6], 90)
    assert parse_spec("all:180", 3) == ([0, 1, 2], 180)
    assert parse_spec("1:-90", 8) == ([0], 270)


def test_parse_spec_errors():
    with pytest.raises(ValueError, match="PAGES:ANGLE"):
        parse_spec("2", 8)
    with pytest.raises(ValueError, match="multiple of 90"):
        parse_spec("2:45", 8)
    with pytest.raises(ValueError, match="invalid angle"):
        parse_spec("2:abc", 8)


def test_rotate_applies_to_selected_pages(make_pdf, tmp_path):
    source = make_pdf([400.0] * 4)
    output = tmp_path / "out.pdf"
    rotate(source, ["2:180", "4:90"], output)
    rotations = [page.rotation for page in PdfReader(str(output)).pages]
    assert rotations == [0, 180, 0, 90]


def test_rotations_accumulate(make_pdf, tmp_path):
    source = make_pdf([400.0] * 2)
    output = tmp_path / "out.pdf"
    rotate(source, ["1:90", "1:90"], output)
    assert PdfReader(str(output)).pages[0].rotation == 180
