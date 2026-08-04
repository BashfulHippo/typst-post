"""Parsing of 1-indexed page selections like "4,1-3,8-5"."""

from __future__ import annotations


def parse_page_list(text: str, page_count: int) -> list[int]:
    """Parse a comma-separated page selection into 0-indexed page numbers.

    Ranges may run backwards ("8-5") and pages may repeat.
    """
    pages: list[int] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            raise ValueError(f"empty page token in {text!r}")
        if "-" in token:
            start_text, _, end_text = token.partition("-")
            start = _page_number(start_text, page_count)
            end = _page_number(end_text, page_count)
            step = 1 if end >= start else -1
            pages.extend(range(start, end + step, step))
        else:
            pages.append(_page_number(token, page_count))
    return pages


def _page_number(text: str, page_count: int) -> int:
    try:
        number = int(text)
    except ValueError:
        raise ValueError(f"invalid page number {text!r}") from None
    if not 1 <= number <= page_count:
        raise ValueError(f"page {number} out of range 1-{page_count}")
    return number - 1
