import pytest
from pypdf import PdfReader

from typst_post.booklet import booklet, spread_order


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
