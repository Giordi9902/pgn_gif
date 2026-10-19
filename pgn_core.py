"""
Logica pura di pgn_gif: lettura del PGN e pianificazione delle animazioni.

Questo modulo dipende solo da python-chess, così può essere testato senza
Manim. La scena in pgn_gif.py si limita a tradurre ogni `Mossa` in animazioni.
"""
import io
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

import chess
import chess.pgn

SQ = 0.8                      # lato di una casa
OFFSET_X = -2.0               # spostamento della scacchiera verso sinistra
LIGHT, DARK = "#F0D9B5", "#B58863"
GLYPH = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}


@dataclass(frozen=True)
class Mossa:
    """Tutto ciò che serve per animare una semimossa."""
    da: int                                   # casa di partenza
    a: int                                    # casa di arrivo
    catturata: Optional[int] = None           # casa del pezzo catturato
    torre: Optional[Tuple[int, int]] = None   # (da, a) della torre nell'arrocco
    promozione: Optional[chess.Piece] = None  # pezzo che sostituisce il pedone
    etichetta: str = ""                       # es. "12. O-O-O" o "12... Rd8"


def pos(square):
    """Coordinate (x, y, z) del centro di una casa (a1 in basso a sinistra)."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return ((f - 3.5) * SQ + OFFSET_X, (r - 3.5) * SQ, 0.0)


def colore_casa(square):
    """Colore di sfondo della casa: a1 è scura."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return DARK if (f + r) % 2 == 0 else LIGHT


def glifo(piece):
    """Carattere Unicode usato per disegnare il pezzo."""
    return GLYPH[piece.symbol().lower()]


class _RaccogliErrori(chess.pgn.GameBuilder):
    """Come GameBuilder, ma raccoglie gli errori senza scriverli nel log."""
    def handle_error(self, error):
        self.game.errors.append(error)


def carica_partita(testo):
    """Legge la prima partita di un testo PGN, sollevando ValueError se non valida."""
    game = chess.pgn.read_game(io.StringIO(testo), Visitor=_RaccogliErrori)
    if game is None:
        raise ValueError("nessuna partita trovata nel PGN")
    if game.errors:
        raise ValueError(f"PGN non valido: {game.errors[0]}")
    return game


def etichetta(numero, san):
    """Etichetta di una semimossa (numero parte da 0): '1. e4', '1... e5'."""
    return f"{numero // 2 + 1}.{'' if numero % 2 == 0 else '..'} {san}"


def titolo(game):
    """Intestazione 'Bianco – Nero' presa dagli header del PGN."""
    h = game.headers
    return f"{h.get('White', '?')} – {h.get('Black', '?')}"


def pianifica(game) -> Iterator[Mossa]:
    """Percorre la linea principale producendo una `Mossa` per ogni semimossa."""
    board = game.board()
    for numero, move in enumerate(game.mainline_moves()):
        da, a = move.from_square, move.to_square

        # Cattura (incluso en passant, dove il pedone non sta sulla casa d'arrivo)
        if board.is_en_passant(move):
            catturata = chess.square(chess.square_file(a), chess.square_rank(da))
        elif board.piece_at(a) is not None and not board.is_castling(move):
            catturata = a
        else:
            catturata = None

        # Arrocco: muove anche la torre
        torre = None
        if board.is_castling(move):
            rank = chess.square_rank(da)
            rf, rt = (7, 5) if board.is_kingside_castling(move) else (0, 3)
            torre = (chess.square(rf, rank), chess.square(rt, rank))

        promozione = chess.Piece(move.promotion, board.turn) if move.promotion else None

        # SAN va calcolato prima di push
        yield Mossa(da, a, catturata, torre, promozione, etichetta(numero, board.san(move)))
        board.push(move)
