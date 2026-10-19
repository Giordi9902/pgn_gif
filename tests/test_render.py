"""End-to-end tests: they really render a GIF (slow, need Manim and ffmpeg)."""
import shutil

import pytest

manim = pytest.importorskip("manim")
if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg not available", allow_module_level=True)

import pgn_gif  # noqa: E402

pytestmark = pytest.mark.slow

SCHOLARS_MATE = ('[White "A"]\n[Black "B"]\n[Result "1-0"]\n\n'
                 '1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0')


def test_cli_writes_gif(tmp_path):
    pgn = tmp_path / "scholars_mate.pgn"
    pgn.write_text(SCHOLARS_MATE, encoding="utf-8")
    pgn_gif.main([str(pgn), "-q", "l", "-t", "0.1"])
    gif = tmp_path / "scholars_mate.gif"
    assert gif.read_bytes()[:6] in (b"GIF87a", b"GIF89a")


def test_cli_invalid_pgn(tmp_path, capsys):
    pgn = tmp_path / "broken.pgn"
    pgn.write_text("1. e4 e5 2. Ke3", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        pgn_gif.main([str(pgn)])
    assert e.value.code == 1
    assert "invalid PGN" in capsys.readouterr().err
    assert not (tmp_path / "broken.gif").exists()


@pytest.mark.parametrize("theme", ["green", "blue"])
def test_cli_themes(tmp_path, theme):
    pgn = tmp_path / "short.pgn"
    pgn.write_text("1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0", encoding="utf-8")
    pgn_gif.main([str(pgn), "-q", "l", "-t", "0.1", "--theme", theme,
                  "-o", str(tmp_path / "out.gif")])
    assert (tmp_path / "out.gif").stat().st_size > 0


def test_cli_unknown_theme(tmp_path):
    with pytest.raises(SystemExit) as e:
        pgn_gif.main([str(tmp_path / "x.pgn"), "--theme", "pink"])
    assert e.value.code == 2
