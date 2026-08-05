"""2-up saddle-stitch booklet imposition.

Pages are paired onto landscape spreads so that a duplex-printed, folded
stack reads in order. All placement is done with vector transformations;
nothing is rasterized.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter, Transformation

# Landscape sheet sizes in PostScript points.
SHEET_SIZES = {
    "a3": (1191.0, 842.0),
    "a4": (842.0, 595.0),
    "a5": (595.0, 420.0),
    "letter": (792.0, 612.0),
    "legal": (1008.0, 612.0),
}


def spread_order(
    page_count: int, signature: int = 0, multiple: int = 4
) -> list[tuple[Optional[int], Optional[int]]]:
    """Return (left, right) 0-indexed page pairs for each output spread.

    None marks a blank added to pad a signature to a multiple of `multiple`
    pages. A signature of 0 treats the whole document as one signature.
    `multiple` is 4 for 2-up imposition and 8 for 4-up, since each physical
    sheet consumes one spread per side (2-up) or four spreads per sheet (4-up).
    """
    if signature < 0 or signature % multiple:
        raise ValueError(f"signature size must be a positive multiple of {multiple}")
    if page_count < 1:
        raise ValueError("document has no pages")
    chunk = signature or page_count + (-page_count) % multiple
    spreads: list[tuple[Optional[int], Optional[int]]] = []
    for start in range(0, page_count, chunk):
        size = min(chunk, page_count - start)
        padded = size + (-size) % multiple
        for k in range(padded // 2):
            left, right = (padded - k, k + 1) if k % 2 == 0 else (k + 1, padded - k)
            spreads.append(
                (
                    start + left - 1 if left <= size else None,
                    start + right - 1 if right <= size else None,
                )
            )
    return spreads


def _place(
    sheet_page,
    reader: PdfReader,
    index: Optional[int],
    shift_x: float,
    shift_y: float,
    slot_w: float,
    slot_h: float,
    rotate180: bool = False,
) -> None:
    """Merge page *index* into *sheet_page*, fit to its own (shift, slot).

    Each page is scaled independently from its own mediabox, so a document
    with mixed page sizes (a landscape page in a portrait document, or a
    page previously rotated 90/270 degrees) still imposes correctly instead
    of being placed using another page's geometry.
    """
    if index is None:
        return
    source_page = reader.pages[index]
    page_w = float(source_page.mediabox.width)
    page_h = float(source_page.mediabox.height)
    scale = min(slot_w / page_w, slot_h / page_h)
    x_offset = shift_x + (slot_w - page_w * scale) / 2
    y_offset = shift_y + (slot_h - page_h * scale) / 2
    transform = Transformation().scale(scale)
    if rotate180:
        # Rotating about the origin flips the page into negative coordinate
        # space, so the translation must add back the full scaled page size
        # to land it in the same (shift, slot) box a non-rotated page would.
        transform = transform.rotate(180).translate(x_offset + page_w * scale, y_offset + page_h * scale)
    else:
        transform = transform.translate(x_offset, y_offset)
    sheet_page.merge_transformed_page(source_page, transform)


def _booklet_2up(reader: PdfReader, sheet: Optional[str], signature: int) -> tuple[PdfWriter, int]:
    spreads = spread_order(len(reader.pages), signature, multiple=4)
    if sheet is None:
        max_width = max(float(p.mediabox.width) for p in reader.pages)
        max_height = max(float(p.mediabox.height) for p in reader.pages)
        sheet_w, sheet_h = 2 * max_width, max_height
    else:
        sheet_w, sheet_h = SHEET_SIZES[sheet]
    slot_w, slot_h = sheet_w / 2, sheet_h

    writer = PdfWriter()
    for left, right in spreads:
        page = writer.add_blank_page(width=sheet_w, height=sheet_h)
        _place(page, reader, left, 0.0, 0.0, slot_w, slot_h)
        _place(page, reader, right, slot_w, 0.0, slot_w, slot_h)
    return writer, len(spreads)


def quadrants_4up(
    spreads: list[tuple[Optional[int], Optional[int]]],
) -> list[tuple[Optional[int], Optional[int], Optional[int], Optional[int]]]:
    """Group 2-up spreads into 4-up sheet sides: (bottom_left, bottom_right, top_left, top_right).

    Each physical sheet consumes four consecutive spreads: the first two
    form the unrotated bottom row (one per side), the last two form the top
    row, reversed and rotated 180 degrees, on the same two sides. This
    layout, including which quadrants rotate, was verified against a real,
    independently produced imposition rather than derived from a written
    description alone (see the project's issue tracker).
    """
    sides = []
    for i in range(0, len(spreads), 4):
        a, b, c, d = spreads[i : i + 4]
        sides.append((a[0], a[1], d[1], d[0]))
        sides.append((b[0], b[1], c[1], c[0]))
    return sides


def _booklet_4up(reader: PdfReader, sheet: Optional[str], signature: int) -> tuple[PdfWriter, int]:
    spreads = spread_order(len(reader.pages), signature, multiple=8)
    sides = quadrants_4up(spreads)
    if sheet is None:
        max_width = max(float(p.mediabox.width) for p in reader.pages)
        max_height = max(float(p.mediabox.height) for p in reader.pages)
        sheet_w, sheet_h = 2 * max_width, 2 * max_height
    else:
        # Sheet sizes are tabulated landscape (for 2-up); 4-up sheets use
        # the same paper in its natural portrait orientation.
        landscape_w, landscape_h = SHEET_SIZES[sheet]
        sheet_w, sheet_h = landscape_h, landscape_w
    slot_w, slot_h = sheet_w / 2, sheet_h / 2

    writer = PdfWriter()
    for bl, br, tl, tr in sides:
        page = writer.add_blank_page(width=sheet_w, height=sheet_h)
        _place(page, reader, bl, 0.0, 0.0, slot_w, slot_h)
        _place(page, reader, br, slot_w, 0.0, slot_w, slot_h)
        _place(page, reader, tl, 0.0, slot_h, slot_w, slot_h, rotate180=True)
        _place(page, reader, tr, slot_w, slot_h, slot_w, slot_h, rotate180=True)
    return writer, len(sides)


def booklet(
    source: Path,
    output: Path,
    sheet: Optional[str] = None,
    signature: int = 0,
    layout: str = "2up",
) -> int:
    """Impose *source* as a booklet, returning the number of sheet sides written."""
    if layout not in ("2up", "4up"):
        raise ValueError(f"unknown layout {layout!r}, expected '2up' or '4up'")
    reader = PdfReader(str(source))
    for page in reader.pages:
        if page.rotation:
            page.transfer_rotation_to_content()

    if layout == "2up":
        writer, count = _booklet_2up(reader, sheet, signature)
    else:
        writer, count = _booklet_4up(reader, sheet, signature)
    with open(output, "wb") as handle:
        writer.write(handle)
    return count
