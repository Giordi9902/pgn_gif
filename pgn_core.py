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
import chess.svg

SQ = 0.85                     # lato di una casa
OFFSET_X = -2.6               # spostamento della scacchiera verso sinistra


@dataclass(frozen=True)
class Tema:
    chiara: str               # case chiare
    scura: str                # case scure
    evidenza: str             # case dell'ultima mossa (sovrapposto a opacità 0.5)
    cornice: str              # bordo attorno alla scacchiera


TEMI = {
    "marrone": Tema("#F0D9B5", "#B58863", "#CDD26A", "#6E4F36"),
    "verde":   Tema("#EEEED2", "#769656", "#F6F669", "#4B6B3A"),
    "blu":     Tema("#DEE3E6", "#8CA2AD", "#C3D887", "#4F6672"),
    "grigio":  Tema("#E0E0E0", "#A0A0A0", "#9BC2E6", "#5A5A5A"),
}
TEMA_PREDEFINITO = "marrone"

# Rettangolo trasparente grande quanto il viewBox: senza, ogni pezzo verrebbe
# ridimensionato sul proprio disegno e pedone e re risulterebbero alti uguali
_RIEMPI_VIEWBOX = ('<rect x="0" y="0" width="45" height="45" '
                   'style="fill:#000000;fill-opacity:0;stroke:none"/>')


@dataclass(frozen=True)
class Mossa:
    """Tutto ciò che serve per animare una semimossa."""
    da: int                                   # casa di partenza
    a: int                                    # casa di arrivo
    catturata: Optional[int] = None           # casa del pezzo catturato
    torre: Optional[Tuple[int, int]] = None   # (da, a) della torre nell'arrocco
    promozione: Optional[chess.Piece] = None  # pezzo che sostituisce il pedone
    etichetta: str = ""                       # es. "12. O-O-O" o "12... Rd8"
    scacco: Optional[int] = None              # casa del re sotto scacco dopo la mossa


def pos(square):
    """Coordinate (x, y, z) del centro di una casa (a1 in basso a sinistra)."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return ((f - 3.5) * SQ + OFFSET_X, (r - 3.5) * SQ, 0.0)


def colore_casa(square, tema=TEMI[TEMA_PREDEFINITO]):
    """Colore di sfondo della casa: a1 è scura."""
    f, r = chess.square_file(square), chess.square_rank(square)
    return tema.scura if (f + r) % 2 == 0 else tema.chiara


def pezzo_svg(piece):
    """SVG del pezzo (stile cburnett, fornito da python-chess) su un riquadro 45×45."""
    svg = chess.svg.piece(piece)
    apertura = svg.index(">", svg.index("<svg")) + 1
    return svg[:apertura] + _RIEMPI_VIEWBOX + svg[apertura:]


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


def giocatori(game):
    """Nomi (Bianco, Nero) presi dagli header del PGN."""
    h = game.headers
    return h.get("White", "?"), h.get("Black", "?")


def sottotitolo(game):
    """'Evento · anno', omettendo le parti sconosciute."""
    h = game.headers
    anno = h.get("Date", "?")[:4]
    parti = [h.get("Event", "?"), anno]
    return " · ".join(p for p in parti if p and "?" not in p)


def descrivi_risultato(risultato):
    """Testo leggibile del risultato PGN."""
    return {"1-0": "Vince il Bianco", "0-1": "Vince il Nero",
            "1/2-1/2": "Patta"}.get(risultato, "")


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

        # SAN va calcolato prima di push, lo scacco dopo
        san = board.san(move)
        board.push(move)
        scacco = board.king(board.turn) if board.is_check() else None
        yield Mossa(da, a, catturata, torre, promozione, etichetta(numero, san), scacco)
