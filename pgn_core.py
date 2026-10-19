"""
Pure logic for pgn_gif: PGN parsing and animation planning.

This module depends only on python-chess, so it can be tested without Manim.
The scene in pgn_gif.py simply turns every `MovePlan` into animations.
"""
import io
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

import chess
import chess.pgn
import chess.svg

SQ = 0.85                     # side of a square
OFFSET_X = -2.6               # shift of the board to the left


@dataclass(frozen=True)
class Theme:
    light: str                # light squares
    dark: str                 # dark squares
    highlight: str            # last-move squares (overlaid at 0.5 opacity)
    border: str               # frame around the board


THEMES = {
    "brown": Theme("#F0D9B5", "#B58863", "#CDD26A", "#6E4F36"),
    "green": Theme("#EEEED2", "#769656", "#F6F669", "#4B6B3A"),
    "blue":  Theme("#DEE3E6", "#8CA2AD", "#C3D887", "#4F6672"),
    "gray":  Theme("#E0E0E0", "#A0A0A0", "#9BC2E6", "#5A5A5A"),
}
DEFAULT_THEME = "brown"

# Transparent rectangle as large as the viewBox: without it every piece would be
# scaled to its own drawing, and a pawn would end up as tall as a king
_FILL_VIEWBOX = ('<rect x="0" y="0" width="45" height="45" '
                 'style="fill:#000000;fill-opacity:0;stroke:none"/>')


@dataclass(frozen=True)
class MovePlan:
    """Everything needed to animate a single ply."""
    from_sq: int                              # origin square
    to_sq: int                                # destination square
    captured: Optional[int] = None            # square of the captured piece
    rook: Optional[Tuple[int, int]] = None    # (from, to) of the rook when castling
    promotion: Optional[chess.Piece] = None   # piece replacing the pawn
    label: str = ""                           # e.g. "12. O-O-O" or "12... Rd8"
    check: Optional[int] = None               # square of the king in check after the move


def pos(square):
    """(x, y, z) coordinates of the centre of a square (a1 bottom left)."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return ((f - 3.5) * SQ + OFFSET_X, (r - 3.5) * SQ, 0.0)


def square_color(square, theme=THEMES[DEFAULT_THEME]):
    """Background colour of a square: a1 is dark."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return theme.dark if (f + r) % 2 == 0 else theme.light


def piece_svg(piece):
    """SVG of the piece (cburnett set, shipped with python-chess) on a 45×45 box."""
    svg = chess.svg.piece(piece)
    opening = svg.index(">", svg.index("<svg")) + 1
    return svg[:opening] + _FILL_VIEWBOX + svg[opening:]


class _CollectErrors(chess.pgn.GameBuilder):
    """Like GameBuilder, but collects errors without logging them."""
    def handle_error(self, error):
        self.game.errors.append(error)


def load_game(text):
    """Read the first game of a PGN text, raising ValueError if it is invalid."""
    game = chess.pgn.read_game(io.StringIO(text), Visitor=_CollectErrors)
    if game is None:
        raise ValueError("no game found in the PGN")
    if game.errors:
        raise ValueError(f"invalid PGN: {game.errors[0]}")
    return game


def move_label(ply, san):
    """Label of a ply (counting from 0): '1. e4', '1... e5'."""
    return f"{ply // 2 + 1}.{'' if ply % 2 == 0 else '..'} {san}"


def players(game):
    """(White, Black) names taken from the PGN headers."""
    h = game.headers
    return h.get("White", "?"), h.get("Black", "?")


def subtitle(game):
    """'Event · year', leaving out unknown parts."""
    h = game.headers
    year = h.get("Date", "?")[:4]
    parts = [h.get("Event", "?"), year]
    return " · ".join(p for p in parts if p and "?" not in p)


def describe_result(result):
    """Human-readable PGN result."""
    return {"1-0": "White wins", "0-1": "Black wins",
            "1/2-1/2": "Draw"}.get(result, "")


def plan_moves(game) -> Iterator[MovePlan]:
    """Walk the mainline, yielding a `MovePlan` for every ply."""
    board = game.board()
    for ply, move in enumerate(game.mainline_moves()):
        from_sq, to_sq = move.from_square, move.to_square

        # Capture (including en passant, where the pawn is not on the target square)
        if board.is_en_passant(move):
            captured = chess.square(chess.square_file(to_sq), chess.square_rank(from_sq))
        elif board.piece_at(to_sq) is not None and not board.is_castling(move):
            captured = to_sq
        else:
            captured = None

        # Castling: the rook moves too
        rook = None
        if board.is_castling(move):
            rank = chess.square_rank(from_sq)
            rf, rt = (7, 5) if board.is_kingside_castling(move) else (0, 3)
            rook = (chess.square(rf, rank), chess.square(rt, rank))

        promotion = chess.Piece(move.promotion, board.turn) if move.promotion else None

        # SAN must be computed before push, check after it
        san = board.san(move)
        board.push(move)
        check = board.king(board.turn) if board.is_check() else None
        yield MovePlan(from_sq, to_sq, captured, rook, promotion, move_label(ply, san), check)
