"""Reorder, duplicate or drop pages."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .pages import parse_page_list


def reorder(source: Path, order: str, output: Path) -> None:
    reader = PdfReader(str(source))
    indices = parse_page_list(order, len(reader.pages))
    writer = PdfWriter()
    for index in indices:
        writer.add_page(reader.pages[index])
    with open(output, "wb") as handle:
        writer.write(handle)
