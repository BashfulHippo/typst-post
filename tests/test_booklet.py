import pytest
from pypdf import PdfReader

from typst_post.booklet import booklet, quadrants_4up, spread_order


def test_spread_order_eight_pages():
    assert spread_order(8) == [(7, 0), (1, 6), (5, 2), (3, 4)]


def test_spread_order_pads_to_multiple_of_four():
    assert spread_order(6) == [(None, 0), (1, None), (5, 2), (3, 4)]


def test_spread_order_signatures():
    # Two signatures of 4: pages 1-4, then 5-8.
    assert spread_order(8, signature=4) == [(3, 0), (1, 2), (7, 4), (5, 6)]


def test_spread_order_validation():
    with pytest.raises(ValueError, match="multiple of 4"):
        spread_order(8, signature=6)
    with pytest.raises(ValueError, match="no pages"):
        spread_order(0)


def test_booklet_output_dimensions(make_pdf, tmp_path):
    source = make_pdf([420.0] * 8, height=595.0)
    output = tmp_path / "out.pdf"
    spreads = booklet(source, output)
    pages = PdfReader(str(output)).pages
    assert spreads == 4
    assert len(pages) == 4
    assert float(pages[0].mediabox.width) == 840.0
    assert float(pages[0].mediabox.height) == 595.0


def test_booklet_scaled_to_sheet(make_pdf, tmp_path):
    source = make_pdf([595.0] * 4, height=842.0)
    output = tmp_path / "out.pdf"
    booklet(source, output, sheet="a4")
    page = PdfReader(str(output)).pages[0]
    assert float(page.mediabox.width) == 842.0
    assert float(page.mediabox.height) == 595.0


def test_booklet_mixed_page_sizes_auto_sheet_fits_largest_page(make_sized_pdf, tmp_path):
    # Three portrait A5 pages plus one landscape page (a wide table, or a page
    # a previous `rotate` call turned 90 degrees) mixed into the same document.
    source = make_sized_pdf([(420.0, 595.0), (595.0, 420.0), (420.0, 595.0), (420.0, 595.0)])
    output = tmp_path / "out.pdf"
    spreads = booklet(source, output)
    pages = PdfReader(str(output)).pages
    assert spreads == 2
    # The sheet must accommodate the widest and tallest page in the document,
    # not assume every page matches the first page's dimensions.
    assert float(pages[0].mediabox.width) == 2 * 595.0
    assert float(pages[0].mediabox.height) == 595.0


def test_booklet_mixed_page_sizes_scaled_to_sheet(make_sized_pdf, tmp_path):
    source = make_sized_pdf([(420.0, 595.0), (595.0, 420.0), (420.0, 595.0), (420.0, 595.0)])
    output = tmp_path / "out.pdf"
    spreads = booklet(source, output, sheet="a4")
    assert spreads == 2
    page = PdfReader(str(output)).pages[0]
    assert float(page.mediabox.width) == 842.0
    assert float(page.mediabox.height) == 595.0


def test_spread_order_multiple_8_pads_to_eight():
    # 5 real pages padded to 8: three blanks, single signature.
    spreads = spread_order(5, multiple=8)
    assert len(spreads) == 4
    assert spreads == [(None, 0), (1, None), (None, 2), (3, 4)]


def test_spread_order_multiple_8_rejects_non_multiple_signature():
    with pytest.raises(ValueError, match="multiple of 8"):
        spread_order(16, signature=4, multiple=8)


def test_quadrants_4up_single_sheet():
    # One 8-page sheet: bottom row unrotated, top row reversed.
    spreads = spread_order(8, multiple=8)
    assert quadrants_4up(spreads) == [(7, 0, 4, 3), (1, 6, 2, 5)]


def test_quadrants_4up_two_sheet_signature():
    # Ground truth: independently produced imposition of a 16-page, 2-sheet
    # signature (github.com/johnblommers/Imposition-Example), page numbers
    # converted from that file's 1-indexed labels to 0-indexed here. Every
    # quadrant on every sheet matched exactly when checked against the
    # rendered PDF; this is not a value derived from the algorithm itself.
    spreads = spread_order(16, multiple=8)
    assert quadrants_4up(spreads) == [
        (15, 0, 12, 3),  # sheet 1, front: BL=16 BR=1 TL=13 TR=4
        (1, 14, 2, 13),  # sheet 1, back:  BL=2  BR=15 TL=3  TR=14
        (11, 4, 8, 7),  # sheet 2, front: BL=12 BR=5  TL=9  TR=8
        (5, 10, 6, 9),  # sheet 2, back:  BL=6  BR=11 TL=7  TR=10
    ]


def test_booklet_4up_output_dimensions(make_pdf, tmp_path):
    source = make_pdf([306.0] * 16, height=396.0)
    output = tmp_path / "out.pdf"
    pages = booklet(source, output, layout="4up")
    written = PdfReader(str(output)).pages
    assert pages == 4
    assert len(written) == 4
    assert float(written[0].mediabox.width) == 612.0
    assert float(written[0].mediabox.height) == 792.0


def test_booklet_4up_scaled_to_sheet_uses_portrait(make_pdf, tmp_path):
    source = make_pdf([306.0] * 8, height=396.0)
    output = tmp_path / "out.pdf"
    booklet(source, output, layout="4up", sheet="a4")
    page = PdfReader(str(output)).pages[0]
    # a4 is tabulated landscape (842x595) for --layout 2up; 4up uses the
    # same sheet in its natural portrait orientation.
    assert float(page.mediabox.width) == 595.0
    assert float(page.mediabox.height) == 842.0


def test_booklet_invalid_layout(make_pdf, tmp_path):
    source = make_pdf([306.0] * 8, height=396.0)
    with pytest.raises(ValueError, match="unknown layout"):
        booklet(source, tmp_path / "out.pdf", layout="8up")
