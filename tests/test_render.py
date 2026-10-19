"""Test end-to-end: renderizzano davvero una GIF (lenti, richiedono Manim e ffmpeg)."""
import shutil

import pytest

manim = pytest.importorskip("manim")
if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg non disponibile", allow_module_level=True)

import pgn_gif  # noqa: E402

pytestmark = pytest.mark.slow

BREVE = '[White "A"]\n[Black "B"]\n[Result "1-0"]\n\n1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0'


def test_cli_produce_gif(tmp_path):
    pgn = tmp_path / "matto_del_barbiere.pgn"
    pgn.write_text(BREVE, encoding="utf-8")
    pgn_gif.main([str(pgn), "-q", "l", "-t", "0.1"])
    gif = tmp_path / "matto_del_barbiere.gif"
    assert gif.read_bytes()[:6] in (b"GIF87a", b"GIF89a")


def test_cli_pgn_non_valido(tmp_path, capsys):
    pgn = tmp_path / "rotto.pgn"
    pgn.write_text("1. e4 e5 2. Ke3", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        pgn_gif.main([str(pgn)])
    assert e.value.code == 1
    assert "non valido" in capsys.readouterr().err
    assert not (tmp_path / "rotto.gif").exists()


@pytest.mark.parametrize("tema", ["verde", "blu"])
def test_cli_temi(tmp_path, tema):
    pgn = tmp_path / "breve.pgn"
    pgn.write_text("1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0", encoding="utf-8")
    pgn_gif.main([str(pgn), "-q", "l", "-t", "0.1", "--tema", tema, "-o", str(tmp_path / "out.gif")])
    assert (tmp_path / "out.gif").stat().st_size > 0


def test_cli_tema_sconosciuto(tmp_path):
    with pytest.raises(SystemExit) as e:
        pgn_gif.main([str(tmp_path / "x.pgn"), "--tema", "rosa"])
    assert e.value.code == 2
