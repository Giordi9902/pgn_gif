"""
Converte una partita in notazione PGN in una GIF animata con Manim.

Requisiti:
    pip install manim chess

Uso da riga di comando:
    python pgn_gif.py partita.pgn -o partita.gif --tema verde

Uso con Manim:
    manim -qm --format=gif pgn_gif.py PartitaPGN

Con Manim viene letto il file indicato da $PGN_GIF_FILE, altrimenti
"partita.pgn" se esiste, altrimenti la partita d'esempio qui sotto.
Il tema si sceglie con $PGN_GIF_TEMA.
"""
import argparse
import functools
import os
import shutil
import subprocess
import sys
import tempfile

import chess
from manim import *

from pgn_core import (SQ, TEMA_PREDEFINITO, TEMI, carica_partita, colore_casa,
                      descrivi_risultato, giocatori, pezzo_svg, pianifica, pos,
                      sottotitolo)

PGN_FILE = "partita.pgn"
PGN_ESEMPIO = """
[Event "Partita dell'Opera"]
[Site "Parigi"]
[Date "1858.??.??"]
[White "Paul Morphy"]
[Black "Duca di Brunswick e Conte Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7
8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7
14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0
"""

TEMPO_MOSSA = 0.5             # secondi per mossa
FONT = "DejaVu Sans"
SFONDO = "#262421"
TESTO_TENUE = "#9E9B98"
ORO = "#E8C547"
PANNELLO = RIGHT * 4.05       # centro del riquadro a destra della scacchiera
LARGHEZZA_PANNELLO = 4.6
QUALITA = {"l": "low_quality", "m": "medium_quality",
           "h": "high_quality", "k": "fourk_quality"}
# Palette unica senza dithering e frame aggiornati solo nel rettangolo che cambia:
# le GIF risultano molto più leggere di quelle scritte direttamente da Manim
FILTRO_GIF = ("split[a][b];[a]palettegen=max_colors=96:stats_mode=full[p];"
              "[b][p]paletteuse=dither=none:diff_mode=rectangle")

_CARTELLA_SVG = tempfile.TemporaryDirectory(prefix="pgn_gif_")


def leggi_pgn_predefinito():
    percorso = os.environ.get("PGN_GIF_FILE", PGN_FILE)
    if os.path.exists(percorso):
        with open(percorso, encoding="utf-8") as f:
            return f.read()
    return PGN_ESEMPIO


@functools.lru_cache(maxsize=None)
def file_svg(simbolo):
    """Scrive (una volta sola) l'SVG del pezzo e ne restituisce il percorso."""
    colore = "b" if simbolo.isupper() else "n"
    percorso = os.path.join(_CARTELLA_SVG.name, f"{simbolo.lower()}{colore}.svg")
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(pezzo_svg(chess.Piece.from_symbol(simbolo)))
    return percorso


def crea_pezzo(piece):
    return SVGMobject(file_svg(piece.symbol()), height=SQ)


def scritta(contenuto, dimensione, colore=WHITE, **kwargs):
    t = Text(contenuto, font=FONT, font_size=dimensione, color=colore, **kwargs)
    if t.width > LARGHEZZA_PANNELLO:
        t.scale_to_fit_width(LARGHEZZA_PANNELLO)
    return t


def righe_giocatori(bianco, nero):
    """Pallino del colore seguito dal nome, con i due nomi alla stessa scala."""
    nomi = [Text(n, font=FONT, font_size=26, weight=BOLD) for n in (bianco, nero)]
    massimo = LARGHEZZA_PANNELLO - 0.5
    scala = min(1, *(massimo / t.width for t in nomi if t.width))
    righe = []
    for t, colore in zip(nomi, (WHITE, BLACK)):
        disco = Circle(0.13, fill_color=colore, fill_opacity=1,
                       stroke_color=TESTO_TENUE, stroke_width=1.5)
        righe.append(VGroup(disco, t.scale(scala)).arrange(RIGHT, buff=0.22))
    return righe


def alone_scacco(square):
    """Sfumatura radiale rossa sotto il re sotto scacco."""
    return VGroup(*[
        Circle(SQ * r, fill_color="#FF2A2A", fill_opacity=0.28, stroke_width=0)
        for r in (0.5, 0.38, 0.26)
    ]).move_to(np.array(pos(square)))


class PartitaPGN(Scene):
    def __init__(self, testo=None, tempo_mossa=TEMPO_MOSSA, tema=None, **kwargs):
        super().__init__(**kwargs)
        self.testo = testo
        self.tempo_mossa = tempo_mossa
        self.tema = TEMI[tema or os.environ.get("PGN_GIF_TEMA", TEMA_PREDEFINITO)]

    def construct(self):
        game = carica_partita(self.testo or leggi_pgn_predefinito())
        mosse = list(pianifica(game))
        tema = self.tema
        p = lambda sq: np.array(pos(sq))
        self.camera.background_color = SFONDO

        # Cornice con ombra
        lato = 8 * SQ + 0.28
        centro = (p(chess.A1) + p(chess.H8)) / 2
        ombra = RoundedRectangle(corner_radius=0.12, width=lato, height=lato,
                                 fill_color=BLACK, fill_opacity=0.45, stroke_width=0)
        cornice = RoundedRectangle(corner_radius=0.12, width=lato, height=lato,
                                   fill_color=tema.cornice, fill_opacity=1, stroke_width=0)
        ombra.move_to(centro + RIGHT * 0.09 + DOWN * 0.09)
        cornice.move_to(centro)

        # Case e coordinate interne, nel colore della casa opposta
        caselle = VGroup(*[
            Square(SQ, fill_color=colore_casa(sq, tema), fill_opacity=1,
                   stroke_width=0).move_to(p(sq))
            for sq in chess.SQUARES
        ])
        def coordinata(etichetta, sq, angolo):
            colore = tema.chiara if colore_casa(sq, tema) == tema.scura else tema.scura
            t = Text(etichetta, font=FONT, font_size=13, weight=BOLD, color=colore)
            return t.move_to(p(sq) + angolo * (SQ / 2 - 0.1))
        coordinate = VGroup(
            *[coordinata(chr(97 + f), chess.square(f, 0), DR) for f in range(8)],
            *[coordinata(str(r + 1), chess.square(0, r), UL) for r in range(8)],
        )

        # Evidenziazione dell'ultima mossa, invisibile finché non si muove nulla
        evidenza = VGroup(*[
            Square(SQ, fill_color=tema.evidenza, fill_opacity=0, stroke_width=0)
            for _ in range(2)
        ])
        self.add(ombra, cornice, caselle, coordinate, evidenza)

        # Pezzi iniziali
        pezzi = {}
        for sq, piece in game.board().piece_map().items():
            pezzi[sq] = crea_pezzo(piece).move_to(p(sq))
            self.add(pezzi[sq])

        # Pannello: Nero in alto e Bianco in basso, come sulla scacchiera
        bianco, nero = giocatori(game)
        riga_bianco, riga_nero = righe_giocatori(bianco, nero)
        riga_nero.move_to(PANNELLO + UP * 3.05)
        riga_bianco.move_to(PANNELLO + DOWN * 3.05)
        riga_nero.set_opacity(0.45)
        info = scritta(sottotitolo(game), 20, TESTO_TENUE).move_to(PANNELLO + UP * 1.5)
        etichetta = scritta("", 48).move_to(PANNELLO + UP * 0.5)
        larghezza_barra = 3.6
        sinistra_barra = PANNELLO + LEFT * larghezza_barra / 2 + DOWN * 0.35
        binario = RoundedRectangle(corner_radius=0.03, width=larghezza_barra, height=0.06,
                                   fill_color=WHITE, fill_opacity=0.15, stroke_width=0)
        binario.move_to(sinistra_barra + RIGHT * larghezza_barra / 2)
        def barra(frazione):
            r = Rectangle(width=max(larghezza_barra * frazione, 0.001), height=0.06,
                          fill_color=ORO, fill_opacity=1, stroke_width=0)
            return r.move_to(sinistra_barra, aligned_edge=LEFT)
        avanzamento = barra(0)
        self.add(riga_nero, riga_bianco, info, etichetta, binario, avanzamento)
        self.wait(0.5)

        # Animazione delle mosse
        alone = None
        for i, mossa in enumerate(mosse):
            anims = []
            pezzo = pezzi.pop(mossa.da)
            self.bring_to_front(pezzo)    # passa sopra agli altri pezzi

            for quadrato, sq in zip(evidenza, (mossa.da, mossa.a)):
                quadrato.move_to(p(sq)).set_fill(opacity=0.5)

            if alone:
                anims.append(FadeOut(alone))
                alone = None

            if mossa.catturata is not None:
                anims.append(FadeOut(pezzi.pop(mossa.catturata), scale=0.6))

            anims.append(pezzo.animate.move_to(p(mossa.a)))

            if mossa.torre:
                da, a = mossa.torre
                torre = pezzi.pop(da)
                anims.append(torre.animate.move_to(p(a)))
                pezzi[a] = torre

            if mossa.scacco is not None:
                alone = alone_scacco(mossa.scacco)
                # sopra case ed evidenza, sotto i pezzi
                self.bring_to_back(ombra, cornice, caselle, coordinate, evidenza, alone)
                anims.append(FadeIn(alone))

            # Il giocatore che deve muovere è in evidenza
            muove_bianco = i % 2 == 1
            anims += [riga_bianco.animate.set_opacity(1 if muove_bianco else 0.45),
                      riga_nero.animate.set_opacity(0.45 if muove_bianco else 1)]

            nuova_etichetta = scritta(mossa.etichetta, 48).move_to(PANNELLO + UP * 0.5)
            anims += [FadeOut(etichetta, shift=UP * 0.2), FadeIn(nuova_etichetta, shift=UP * 0.2)]
            etichetta = nuova_etichetta
            anims.append(Transform(avanzamento, barra((i + 1) / len(mosse))))
            self.play(*anims, run_time=self.tempo_mossa)

            # Promozione: sostituisce il pedone
            if mossa.promozione:
                nuovo = crea_pezzo(mossa.promozione).move_to(p(mossa.a))
                self.play(ReplacementTransform(pezzo, nuovo), run_time=0.3)
                pezzo = nuovo

            pezzi[mossa.a] = pezzo

        risultato = game.headers.get("Result", "*")
        finale = VGroup(scritta(risultato.replace("1/2", "½"), 52, ORO, weight=BOLD))
        descrizione = descrivi_risultato(risultato)
        if descrizione:
            finale.add(scritta(descrizione, 22, TESTO_TENUE))
        finale.arrange(DOWN, buff=0.15).next_to(binario, DOWN, buff=0.5)
        self.play(FadeIn(finale, shift=UP * 0.2), riga_bianco.animate.set_opacity(1),
                  riga_nero.animate.set_opacity(1), run_time=0.6)
        self.wait(2)


def renderizza(testo, uscita, qualita="m", tempo_mossa=TEMPO_MOSSA, tema=TEMA_PREDEFINITO):
    """Renderizza `testo` (PGN) nella GIF `uscita` e restituisce il percorso."""
    carica_partita(testo)     # errore chiaro prima di avviare Manim
    ffmpeg = shutil.which("ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        with tempconfig({"format": "mp4" if ffmpeg else "gif",
                         "quality": QUALITA[qualita], "media_dir": tmp,
                         "output_file": "partita", "verbosity": "WARNING",
                         "progress_bar": "none"}):
            scena = PartitaPGN(testo, tempo_mossa=tempo_mossa, tema=tema)
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
    parser.add_argument("--tema", choices=TEMI, default=TEMA_PREDEFINITO,
                        help=f"colori della scacchiera (predefinito: {TEMA_PREDEFINITO})")
    args = parser.parse_args(argv)

    if args.pgn == "-":
        testo, uscita = sys.stdin.read(), args.output or "partita.gif"
    else:
        with open(args.pgn, encoding="utf-8") as f:
            testo = f.read()
        uscita = args.output or os.path.splitext(args.pgn)[0] + ".gif"

    try:
        renderizza(testo, uscita, args.qualita, args.tempo, args.tema)
    except ValueError as e:
        parser.exit(1, f"errore: {e}\n")
    print(uscita)


if __name__ == "__main__":
    main()
