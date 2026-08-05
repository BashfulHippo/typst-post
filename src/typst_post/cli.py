from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .booklet import SHEET_SIZES, booklet
from .pack import PackError, pack
from .reorder import reorder
from .rotate import rotate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="typst-post",
        description="Post-compilation utilities for Typst documents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("booklet", help="impose pages as a 2-up saddle-stitch booklet")
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path, help="output PDF (default: INPUT.booklet.pdf)")
    p.add_argument(
        "--sheet",
        choices=sorted(SHEET_SIZES),
        help="scale spreads onto a named sheet size (default: twice the input page width)",
    )
    p.add_argument(
        "--signature",
        type=int,
        default=0,
        metavar="N",
        help="pages per folded signature, a multiple of 4 for --layout 2up or 8 for "
        "4up (default: whole document)",
    )
    p.add_argument(
        "--layout",
        choices=("2up", "4up"),
        default="2up",
        help="2 or 4 logical pages per side (default: 2up)",
    )

    p = sub.add_parser("rotate", help="rotate pages, e.g. 2:180 or 5-8:90 or all:180")
    p.add_argument("input", type=Path)
    p.add_argument("specs", nargs="+", metavar="PAGES:ANGLE")
    p.add_argument("-o", "--output", type=Path, help="output PDF (default: INPUT.rotate.pdf)")

    p = sub.add_parser("reorder", help="reorder, duplicate or drop pages, e.g. 4,1,2,3 or 1-3,8-5")
    p.add_argument("input", type=Path)
    p.add_argument("order", metavar="ORDER")
    p.add_argument("-o", "--output", type=Path, help="output PDF (default: INPUT.reorder.pdf)")

    p = sub.add_parser("pack", help="zip a Typst project with every file it depends on")
    p.add_argument("input", type=Path, metavar="SOURCE.typ")
    p.add_argument("-o", "--output", type=Path, help="output archive (default: SOURCE.zip)")
    p.add_argument(
        "--root",
        type=Path,
        help="project root for the archive layout (default: the source file's directory)",
    )
    p.add_argument("--with-pdf", action="store_true", help="include the compiled PDF in the archive")
    return parser


def _default_output(input_path: Path, command: str) -> Path:
    return input_path.with_name(f"{input_path.stem}.{command}.pdf")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.input.is_file():
        print(f"error: {args.input} is not a file", file=sys.stderr)
        return 2
    if args.command == "pack":
        output = args.output or args.input.with_suffix(".zip")
    else:
        output = args.output or _default_output(args.input, args.command)
    if output.resolve() == args.input.resolve():
        print("error: output would overwrite the input file", file=sys.stderr)
        return 2

    try:
        if args.command == "booklet":
            pages = booklet(
                args.input, output, sheet=args.sheet, signature=args.signature, layout=args.layout
            )
            print(f"wrote {output} ({pages} pages)")
        elif args.command == "rotate":
            rotate(args.input, args.specs, output)
            print(f"wrote {output}")
        elif args.command == "reorder":
            reorder(args.input, args.order, output)
            print(f"wrote {output}")
        else:
            archived, skipped = pack(args.input, output, root=args.root, with_pdf=args.with_pdf)
            note = f" ({skipped} outside the project root skipped)" if skipped else ""
            print(f"packed {archived} files into {output}{note}")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except PackError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
