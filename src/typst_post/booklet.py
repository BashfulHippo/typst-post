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


def spread_order(page_count: int, signature: int = 0) -> list[tuple[Optional[int], Optional[int]]]:
    """Return (left, right) 0-indexed page pairs for each output spread.

    None marks a blank added to pad a signature to a multiple of four pages.
    A signature of 0 treats the whole document as one signature.
    """
    if signature < 0 or signature % 4:
        raise ValueError("signature size must be a positive multiple of 4")
    if page_count < 1:
        raise ValueError("document has no pages")
    chunk = signature or page_count + (-page_count) % 4
    spreads: list[tuple[Optional[int], Optional[int]]] = []
    for start in range(0, page_count, chunk):
        size = min(chunk, page_count - start)
        padded = size + (-size) % 4
        for k in range(padded // 2):
            left, right = (padded - k, k + 1) if k % 2 == 0 else (k + 1, padded - k)
            spreads.append(
                (
                    start + left - 1 if left <= size else None,
                    start + right - 1 if right <= size else None,
                )
            )
    return spreads


def booklet(
    source: Path,
    output: Path,
    sheet: Optional[str] = None,
    signature: int = 0,
) -> int:
    """Impose *source* as a booklet, returning the number of output spreads."""
    reader = PdfReader(str(source))
    spreads = spread_order(len(reader.pages), signature)
    for page in reader.pages:
        if page.rotation:
            page.transfer_rotation_to_content()

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
        for index, shift in ((left, 0.0), (right, slot_w)):
            if index is None:
                continue
            source_page = reader.pages[index]
            page_w = float(source_page.mediabox.width)
            page_h = float(source_page.mediabox.height)
            # Each page is scaled independently to fit its slot, so a document
            # with mixed page sizes (a landscape page in a portrait document,
            # or a page previously rotated 90/270 degrees) still imposes
            # correctly instead of being placed using another page's geometry.
            scale = min(slot_w / page_w, slot_h / page_h)
            x_offset = shift + (slot_w - page_w * scale) / 2
            y_offset = (slot_h - page_h * scale) / 2
            transform = Transformation().scale(scale).translate(x_offset, y_offset)
            page.merge_transformed_page(source_page, transform)
    with open(output, "wb") as handle:
        writer.write(handle)
    return len(spreads)
