"""
Converte una partita in notazione PGN in una GIF animata con Manim.

Requisiti:
    pip install manim chess

Uso da riga di comando:
    python pgn_gif.py partita.pgn -o partita.gif

Uso con Manim:
    manim -qm --format=gif pgn_gif.py PartitaPGN

Con Manim viene letto il file indicato da $PGN_GIF_FILE, altrimenti
"partita.pgn" se esiste, altrimenti la partita d'esempio qui sotto.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import chess
from manim import *

from pgn_core import SQ, colore_casa, carica_partita, glifo, pianifica, pos, titolo

PGN_FILE = "partita.pgn"
PGN_ESEMPIO = """
[Event "Partita dell'Opera"]
[White "Morphy"]
[Black "Duca di Brunswick e Conte Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7
8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7
14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0
"""

TEMPO_MOSSA = 0.5             # secondi per mossa
PANNELLO = RIGHT * 4.4        # centro del riquadro a destra della scacchiera
QUALITA = {"l": "low_quality", "m": "medium_quality",
           "h": "high_quality", "k": "fourk_quality"}
# Palette ricavata dai soli pixel che cambiano e frame aggiornati per rettangoli:
# le GIF risultano molto più leggere di quelle scritte direttamente da Manim
FILTRO_GIF = ("split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];"
              "[b][p]paletteuse=dither=none:diff_mode=rectangle")


def leggi_pgn_predefinito():
    percorso = os.environ.get("PGN_GIF_FILE", PGN_FILE)
    if os.path.exists(percorso):
        with open(percorso, encoding="utf-8") as f:
            return f.read()
    return PGN_ESEMPIO


def crea_pezzo(piece):
    colore = WHITE if piece.color == chess.WHITE else BLACK
    t = Text(glifo(piece), font="DejaVu Sans", font_size=44, color=colore)
    t.set_stroke(BLACK if piece.color == chess.WHITE else WHITE, 1.2,
                 background=True)
    return t


class PartitaPGN(Scene):
    def __init__(self, testo=None, tempo_mossa=TEMPO_MOSSA, **kwargs):
        super().__init__(**kwargs)
        self.testo = testo
        self.tempo_mossa = tempo_mossa

    def construct(self):
        game = carica_partita(self.testo or leggi_pgn_predefinito())
        p = lambda sq: np.array(pos(sq))

        # Scacchiera
        caselle = VGroup(*[
            Square(SQ, fill_color=colore_casa(sq), fill_opacity=1,
                   stroke_width=0).move_to(p(sq))
            for sq in chess.SQUARES
        ])
        coordinate = VGroup(
            *[Text(chr(97 + f), font_size=18).move_to(p(chess.square(f, 0)) + DOWN * 0.6)
              for f in range(8)],
            *[Text(str(r + 1), font_size=18).move_to(p(chess.square(0, r)) + LEFT * 0.6)
              for r in range(8)],
        )
        self.add(caselle, coordinate)

        # Pezzi iniziali
        pezzi = {}
        for sq, piece in game.board().piece_map().items():
            pezzi[sq] = crea_pezzo(piece).move_to(p(sq))
            self.add(pezzi[sq])

        # Intestazione e riquadro della mossa
        intestazione = Text(titolo(game), font_size=24)
        if intestazione.width > 5.0:
            intestazione.scale_to_fit_width(5.0)
        intestazione.move_to(PANNELLO + UP * 3.2)
        etichetta = Text("", font_size=36).move_to(PANNELLO)
        self.add(intestazione, etichetta)
        self.wait(0.5)

        # Animazione delle mosse
        for mossa in pianifica(game):
            anims = []
            pezzo = pezzi.pop(mossa.da)

            if mossa.catturata is not None:
                anims.append(FadeOut(pezzi.pop(mossa.catturata)))

            anims.append(pezzo.animate.move_to(p(mossa.a)))

            if mossa.torre:
                da, a = mossa.torre
                torre = pezzi.pop(da)
                anims.append(torre.animate.move_to(p(a)))
                pezzi[a] = torre

            nuova_etichetta = Text(mossa.etichetta, font_size=36).move_to(PANNELLO)
            anims.append(Transform(etichetta, nuova_etichetta))
            self.play(*anims, run_time=self.tempo_mossa)

            # Promozione: sostituisce il pedone
            if mossa.promozione:
                nuovo = crea_pezzo(mossa.promozione).move_to(p(mossa.a))
                self.play(ReplacementTransform(pezzo, nuovo), run_time=0.3)
                pezzo = nuovo

            pezzi[mossa.a] = pezzo

        risultato = Text(game.headers.get("Result", ""), font_size=40, color=YELLOW)
        risultato.next_to(etichetta, DOWN)
        self.play(FadeIn(risultato))
        self.wait(2)



def renderizza(testo, uscita, qualita="m", tempo_mossa=TEMPO_MOSSA):
    """Renderizza `testo` (PGN) nella GIF `uscita` e restituisce il percorso."""
    carica_partita(testo)     # errore chiaro prima di avviare Manim
    ffmpeg = shutil.which("ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        with tempconfig({"format": "mp4" if ffmpeg else "gif",
                         "quality": QUALITA[qualita], "media_dir": tmp,
                         "output_file": "partita", "verbosity": "WARNING",
                         "progress_bar": "none"}):
            scena = PartitaPGN(testo, tempo_mossa=tempo_mossa)
            scena.render()
            video = str(scena.renderer.file_writer.movie_file_path)
        os.makedirs(os.path.dirname(os.path.abspath(uscita)), exist_ok=True)
        if ffmpeg:
            subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", video,
                            "-filter_complex", FILTRO_GIF, uscita], check=True)
        else:
            shutil.move(video, uscita)
    return uscita


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pgn-gif", description="Trasforma una partita PGN in una GIF animata.")
    parser.add_argument("pgn", help="file PGN da animare ('-' per lo standard input)")
    parser.add_argument("-o", "--output",
                        help="GIF di destinazione (predefinito: nome del PGN con .gif)")
    parser.add_argument("-q", "--qualita", choices=QUALITA, default="m",
                        help="l=480p15, m=720p30, h=1080p60, k=2160p60 (predefinito: m)")
    parser.add_argument("-t", "--tempo", type=float, default=TEMPO_MOSSA,
                        help=f"secondi per mossa (predefinito: {TEMPO_MOSSA})")
    args = parser.parse_args(argv)

    if args.pgn == "-":
        testo, uscita = sys.stdin.read(), args.output or "partita.gif"
    else:
        with open(args.pgn, encoding="utf-8") as f:
            testo = f.read()
        uscita = args.output or os.path.splitext(args.pgn)[0] + ".gif"

    try:
        renderizza(testo, uscita, args.qualita, args.tempo)
    except ValueError as e:
        parser.exit(1, f"errore: {e}\n")
    print(uscita)


if __name__ == "__main__":
    main()
