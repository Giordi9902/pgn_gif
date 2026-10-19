"""
Turn a chess game in PGN notation into an animated GIF with Manim.

Requirements:
    pip install manim chess

Command line:
    python pgn_gif.py game.pgn -o game.gif --theme green

With Manim:
    manim -qm --format=gif pgn_gif.py ChessGame

With Manim the file named by $PGN_GIF_FILE is used, otherwise "game.pgn" if
it exists, otherwise the sample game below. The theme is read from
$PGN_GIF_THEME.
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

from pgn_core import (SQ, DEFAULT_THEME, THEMES, describe_result, load_game,
                      piece_svg, plan_moves, players, pos, square_color, subtitle)

PGN_FILE = "game.pgn"
SAMPLE_PGN = """
[Event "Opera Game"]
[Site "Paris"]
[Date "1858.??.??"]
[White "Paul Morphy"]
[Black "Duke Karl / Count Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7
8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7
14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0
"""

MOVE_TIME = 0.5               # seconds per move
FONT = "DejaVu Sans"
BACKGROUND = "#262421"
MUTED_TEXT = "#9E9B98"
GOLD = "#E8C547"
PANEL = RIGHT * 4.05          # centre of the panel to the right of the board
PANEL_WIDTH = 4.6
QUALITIES = {"l": "low_quality", "m": "medium_quality",
             "h": "high_quality", "k": "fourk_quality"}
# Single palette without dithering, and frames updated only in the rectangle
# that changes: far smaller GIFs than the ones Manim writes directly
GIF_FILTER = ("split[a][b];[a]palettegen=max_colors=96:stats_mode=full[p];"
              "[b][p]paletteuse=dither=none:diff_mode=rectangle")

_SVG_DIR = tempfile.TemporaryDirectory(prefix="pgn_gif_")


def read_default_pgn():
    path = os.environ.get("PGN_GIF_FILE", PGN_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return SAMPLE_PGN


@functools.lru_cache(maxsize=None)
def svg_file(symbol):
    """Write the piece SVG (only once) and return its path."""
    color = "w" if symbol.isupper() else "b"
    path = os.path.join(_SVG_DIR.name, f"{symbol.lower()}{color}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(piece_svg(chess.Piece.from_symbol(symbol)))
    return path


def make_piece(piece):
    return SVGMobject(svg_file(piece.symbol()), height=SQ)


def label(content, size, color=WHITE, **kwargs):
    t = Text(content, font=FONT, font_size=size, color=color, **kwargs)
    if t.width > PANEL_WIDTH:
        t.scale_to_fit_width(PANEL_WIDTH)
    return t


def player_rows(white, black):
    """Coloured dot followed by the name, with both names at the same scale."""
    names = [Text(n, font=FONT, font_size=26, weight=BOLD) for n in (white, black)]
    widest = PANEL_WIDTH - 0.5
    scale = min(1, *(widest / t.width for t in names if t.width))
    rows = []
    for t, color in zip(names, (WHITE, BLACK)):
        dot = Circle(0.13, fill_color=color, fill_opacity=1,
                     stroke_color=MUTED_TEXT, stroke_width=1.5)
        rows.append(VGroup(dot, t.scale(scale)).arrange(RIGHT, buff=0.22))
    return rows


def check_glow(square):
    """Red radial glow under the king in check."""
    return VGroup(*[
        Circle(SQ * r, fill_color="#FF2A2A", fill_opacity=0.28, stroke_width=0)
        for r in (0.5, 0.38, 0.26)
    ]).move_to(np.array(pos(square)))


class ChessGame(Scene):
    def __init__(self, pgn=None, move_time=MOVE_TIME, theme=None, **kwargs):
        super().__init__(**kwargs)
        self.pgn = pgn
        self.move_time = move_time
        self.theme = THEMES[theme or os.environ.get("PGN_GIF_THEME", DEFAULT_THEME)]

    def construct(self):
        game = load_game(self.pgn or read_default_pgn())
        moves = list(plan_moves(game))
        theme = self.theme
        p = lambda sq: np.array(pos(sq))
        self.camera.background_color = BACKGROUND

        # Frame with drop shadow
        side = 8 * SQ + 0.28
        centre = (p(chess.A1) + p(chess.H8)) / 2
        shadow = RoundedRectangle(corner_radius=0.12, width=side, height=side,
                                  fill_color=BLACK, fill_opacity=0.45, stroke_width=0)
        frame = RoundedRectangle(corner_radius=0.12, width=side, height=side,
                                 fill_color=theme.border, fill_opacity=1, stroke_width=0)
        shadow.move_to(centre + RIGHT * 0.09 + DOWN * 0.09)
        frame.move_to(centre)

        # Squares and inner coordinates, in the colour of the opposite square
        squares = VGroup(*[
            Square(SQ, fill_color=square_color(sq, theme), fill_opacity=1,
                   stroke_width=0).move_to(p(sq))
            for sq in chess.SQUARES
        ])
        def coordinate(text, sq, corner):
            color = theme.light if square_color(sq, theme) == theme.dark else theme.dark
            t = Text(text, font=FONT, font_size=13, weight=BOLD, color=color)
            return t.move_to(p(sq) + corner * (SQ / 2 - 0.1))
        coordinates = VGroup(
            *[coordinate(chr(97 + f), chess.square(f, 0), DR) for f in range(8)],
            *[coordinate(str(r + 1), chess.square(0, r), UL) for r in range(8)],
        )

        # Last-move highlight, invisible until something moves
        highlight = VGroup(*[
            Square(SQ, fill_color=theme.highlight, fill_opacity=0, stroke_width=0)
            for _ in range(2)
        ])
        self.add(shadow, frame, squares, coordinates, highlight)

        # Starting pieces
        pieces = {}
        for sq, piece in game.board().piece_map().items():
            pieces[sq] = make_piece(piece).move_to(p(sq))
            self.add(pieces[sq])

        # Panel: Black at the top and White at the bottom, as on the board
        white, black = players(game)
        white_row, black_row = player_rows(white, black)
        black_row.move_to(PANEL + UP * 3.05)
        white_row.move_to(PANEL + DOWN * 3.05)
        black_row.set_opacity(0.45)
        info = label(subtitle(game), 20, MUTED_TEXT).move_to(PANEL + UP * 1.5)
        current = label("", 48).move_to(PANEL + UP * 0.5)
        bar_width = 3.6
        bar_left = PANEL + LEFT * bar_width / 2 + DOWN * 0.35
        track = RoundedRectangle(corner_radius=0.03, width=bar_width, height=0.06,
                                 fill_color=WHITE, fill_opacity=0.15, stroke_width=0)
        track.move_to(bar_left + RIGHT * bar_width / 2)
        def bar(fraction):
            r = Rectangle(width=max(bar_width * fraction, 0.001), height=0.06,
                          fill_color=GOLD, fill_opacity=1, stroke_width=0)
            return r.move_to(bar_left, aligned_edge=LEFT)
        progress = bar(0)
        self.add(black_row, white_row, info, current, track, progress)
        self.wait(0.5)

        # Move animation
        glow = None
        for i, move in enumerate(moves):
            anims = []
            piece = pieces.pop(move.from_sq)
            self.bring_to_front(piece)    # slides over the other pieces

            for square, sq in zip(highlight, (move.from_sq, move.to_sq)):
                square.move_to(p(sq)).set_fill(opacity=0.5)

            if glow:
                anims.append(FadeOut(glow))
                glow = None

            if move.captured is not None:
                anims.append(FadeOut(pieces.pop(move.captured), scale=0.6))

            anims.append(piece.animate.move_to(p(move.to_sq)))

            if move.rook:
                rook_from, rook_to = move.rook
                rook = pieces.pop(rook_from)
                anims.append(rook.animate.move_to(p(rook_to)))
                pieces[rook_to] = rook

            if move.check is not None:
                glow = check_glow(move.check)
                # above squares and highlight, below the pieces
                self.bring_to_back(shadow, frame, squares, coordinates, highlight, glow)
                anims.append(FadeIn(glow))

            # The side to move is highlighted
            white_to_move = i % 2 == 1
            anims += [white_row.animate.set_opacity(1 if white_to_move else 0.45),
                      black_row.animate.set_opacity(0.45 if white_to_move else 1)]

            new_label = label(move.label, 48).move_to(PANEL + UP * 0.5)
            anims += [FadeOut(current, shift=UP * 0.2), FadeIn(new_label, shift=UP * 0.2)]
            current = new_label
            anims.append(Transform(progress, bar((i + 1) / len(moves))))
            self.play(*anims, run_time=self.move_time)

            # Promotion: replace the pawn
            if move.promotion:
                promoted = make_piece(move.promotion).move_to(p(move.to_sq))
                self.play(ReplacementTransform(piece, promoted), run_time=0.3)
                piece = promoted

            pieces[move.to_sq] = piece

        result = game.headers.get("Result", "*")
        ending = VGroup(label(result.replace("1/2", "½"), 52, GOLD, weight=BOLD))
        description = describe_result(result)
        if description:
            ending.add(label(description, 22, MUTED_TEXT))
        ending.arrange(DOWN, buff=0.15).next_to(track, DOWN, buff=0.5)
        self.play(FadeIn(ending, shift=UP * 0.2), white_row.animate.set_opacity(1),
                  black_row.animate.set_opacity(1), run_time=0.6)
        self.wait(2)


def render_gif(pgn, output, quality="m", move_time=MOVE_TIME, theme=DEFAULT_THEME):
    """Render `pgn` (PGN text) to the GIF `output` and return its path."""
    load_game(pgn)            # fail clearly before starting Manim
    ffmpeg = shutil.which("ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        with tempconfig({"format": "mp4" if ffmpeg else "gif",
                         "quality": QUALITIES[quality], "media_dir": tmp,
                         "output_file": "game", "verbosity": "WARNING",
                         "progress_bar": "none"}):
            scene = ChessGame(pgn, move_time=move_time, theme=theme)
            scene.render()
            video = str(scene.renderer.file_writer.movie_file_path)
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        if ffmpeg:
            subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", video,
                            "-filter_complex", GIF_FILTER, output], check=True)
        else:
            shutil.move(video, output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pgn-gif", description="Turn a PGN chess game into an animated GIF.")
    parser.add_argument("pgn", help="PGN file to animate ('-' for standard input)")
    parser.add_argument("-o", "--output",
                        help="destination GIF (default: the PGN name with .gif)")
    parser.add_argument("-q", "--quality", choices=QUALITIES, default="m",
                        help="l=480p15, m=720p30, h=1080p60, k=2160p60 (default: m)")
    parser.add_argument("-t", "--move-time", type=float, default=MOVE_TIME,
                        help=f"seconds per move (default: {MOVE_TIME})")
    parser.add_argument("--theme", choices=THEMES, default=DEFAULT_THEME,
                        help=f"board colours (default: {DEFAULT_THEME})")
    args = parser.parse_args(argv)

    if args.pgn == "-":
        pgn, output = sys.stdin.read(), args.output or "game.gif"
    else:
        with open(args.pgn, encoding="utf-8") as f:
            pgn = f.read()
        output = args.output or os.path.splitext(args.pgn)[0] + ".gif"

    try:
        render_gif(pgn, output, args.quality, args.move_time, args.theme)
    except ValueError as e:
        parser.exit(1, f"error: {e}\n")
    print(output)


if __name__ == "__main__":
    main()
