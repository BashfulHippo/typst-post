"""Bundle a Typst project with every file it depends on.

The dependency list comes from the compiler itself (``typst compile --deps``,
with a fallback to the older ``--make-deps``), so imports of imports, package
assets referenced through variables, and anything else the compiler touches
are all covered without guessing at the source.
"""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path
from typing import Optional

_TMP_PDF = ".typst-post.tmp.pdf"
_TMP_DEPS = ".typst-post.tmp.deps"


class PackError(RuntimeError):
    """Raised when the project cannot be compiled or bundled."""


def parse_depfile(text: str, target: str) -> list[str]:
    """Extract the dependency paths from a make-style depfile.

    Handles the escapes typst emits: ``\\ `` for spaces and ``\\:`` for
    colons (seen in absolute Windows paths).
    """
    joined = text.replace("\\\n", " ")
    prefix = f"{target}:"
    line = next((ln for ln in joined.splitlines() if ln.startswith(prefix)), None)
    if line is None:
        raise PackError("could not locate the dependency list in the depfile")
    deps: list[str] = []
    current: list[str] = []
    rest = line[len(prefix):]
    i = 0
    while i < len(rest):
        char = rest[i]
        if char == "\\" and i + 1 < len(rest) and rest[i + 1] in (" ", ":"):
            current.append(rest[i + 1])
            i += 2
        elif char == " ":
            if current:
                deps.append("".join(current))
                current = []
            i += 1
        else:
            current.append(char)
            i += 1
    if current:
        deps.append("".join(current))
    return deps


def normalize_path(raw: str) -> Path:
    """Drop the Windows extended-length prefix typst puts on absolute paths."""
    if raw.startswith("\\\\?\\UNC\\"):
        raw = "\\\\" + raw[8:]
    elif raw.startswith("\\\\?\\"):
        raw = raw[4:]
    return Path(raw)


def _compile_deps(source: Path, workdir: Path) -> list[str]:
    base = ["typst", "compile", source.name, _TMP_PDF]
    try:
        result = subprocess.run(
            base + ["--deps", _TMP_DEPS, "--deps-format", "json"],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "--deps" in result.stderr:
            # Older typst without --deps; fall back to the make-style depfile.
            result = subprocess.run(
                base + ["--make-deps", _TMP_DEPS],
                cwd=workdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise PackError(f"typst compile failed:\n{result.stderr.strip()}")
            depfile = (workdir / _TMP_DEPS).read_text(encoding="utf-8")
            return parse_depfile(depfile, _TMP_PDF)
    except FileNotFoundError:
        raise PackError("typst executable not found on PATH") from None
    if result.returncode != 0:
        raise PackError(f"typst compile failed:\n{result.stderr.strip()}")
    depfile = (workdir / _TMP_DEPS).read_text(encoding="utf-8")
    return json.loads(depfile)["inputs"]


def pack(
    source: Path,
    output: Path,
    root: Optional[Path] = None,
    with_pdf: bool = False,
) -> tuple[int, int]:
    """Compile *source*, then zip its dependencies relative to *root*.

    Returns (files archived, files skipped as outside the root). Files
    outside the root — typically the package cache — are skipped because
    Typst restores packages on its own.
    """
    source = source.resolve()
    workdir = source.parent
    root = (root or workdir).resolve()
    tmp_pdf = workdir / _TMP_PDF
    tmp_deps = workdir / _TMP_DEPS
    try:
        deps = _compile_deps(source, workdir)
        included: dict[Path, Path] = {}
        skipped = 0
        for dep in deps:
            path = normalize_path(dep)
            path = (path if path.is_absolute() else workdir / path).resolve()
            if path == tmp_pdf:
                continue
            try:
                relative = path.relative_to(root)
            except ValueError:
                skipped += 1
                continue
            included[relative] = path

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for relative, path in sorted(included.items()):
                archive.write(path, relative.as_posix())
            if with_pdf:
                archive.write(tmp_pdf, source.with_suffix(".pdf").name)
        return len(included), skipped
    finally:
        for tmp in (tmp_pdf, tmp_deps):
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
