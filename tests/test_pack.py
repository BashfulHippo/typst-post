import shutil
import zipfile
from pathlib import Path

import pytest

from typst_post.pack import PackError, normalize_path, pack, parse_depfile


def test_parse_depfile_basic():
    text = "out.pdf: main.typ chapters/intro.typ assets/logo.png\n"
    assert parse_depfile(text, "out.pdf") == [
        "main.typ",
        "chapters/intro.typ",
        "assets/logo.png",
    ]


def test_parse_depfile_escaped_spaces():
    text = "out.pdf: main.typ assets/logo\\ v2.png\n"
    assert parse_depfile(text, "out.pdf") == ["main.typ", "assets/logo v2.png"]


def test_parse_depfile_line_continuations():
    text = "out.pdf: main.typ \\\n  extra.typ\n"
    assert parse_depfile(text, "out.pdf") == ["main.typ", "extra.typ"]


def test_parse_depfile_escaped_windows_path():
    text = "out.pdf: \\\\?\\C\\:\\project\\main.typ\n"
    assert parse_depfile(text, "out.pdf") == ["\\\\?\\C:\\project\\main.typ"]


def test_normalize_path_strips_extended_prefix():
    assert str(normalize_path("\\\\?\\C:\\project\\main.typ")) == "C:\\project\\main.typ"
    assert normalize_path("assets/note.typ") == Path("assets/note.typ")


def test_parse_depfile_missing_target():
    with pytest.raises(PackError):
        parse_depfile("other: a b\n", "out.pdf")


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst not installed")
def test_pack_end_to_end(tmp_path):
    project = tmp_path / "project"
    (project / "assets").mkdir(parents=True)
    (project / "assets" / "note.typ").write_text('#let extra = "included"\n')
    (project / "main.typ").write_text('#import "assets/note.typ": extra\nHello #extra\n')
    output = tmp_path / "bundle.zip"
    archived, skipped = pack(project / "main.typ", output)
    names = set(zipfile.ZipFile(output).namelist())
    assert archived == 2
    assert names == {"main.typ", "assets/note.typ"}
