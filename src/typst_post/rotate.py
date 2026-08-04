"""Rotate individual pages without touching their content streams."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from .pages import parse_page_list


def parse_spec(spec: str, page_count: int) -> tuple[list[int], int]:
    """Parse a "PAGES:ANGLE" spec such as "2:180", "5-8:90" or "all:180"."""
    pages_part, sep, angle_part = spec.rpartition(":")
    if not sep:
        raise ValueError(f"expected PAGES:ANGLE, got {spec!r}")
    try:
        angle = int(angle_part)
    except ValueError:
        raise ValueError(f"invalid angle {angle_part!r}") from None
    if angle % 90 != 0:
        raise ValueError(f"angle must be a multiple of 90, got {angle}")
    if pages_part == "all":
        pages = list(range(page_count))
    else:
        pages = parse_page_list(pages_part, page_count)
    return pages, angle % 360


def rotate(source: Path, specs: list[str], output: Path) -> None:
    writer = PdfWriter(clone_from=str(source))
    for spec in specs:
        pages, angle = parse_spec(spec, len(writer.pages))
        if angle == 0:
            continue
        for index in pages:
            writer.pages[index].rotate(angle)
    with open(output, "wb") as handle:
        writer.write(handle)
