from pathlib import Path

import chess
import pytest

from pgn_core import (SQ, DEFAULT_THEME, THEMES, describe_result, load_game,
                      move_label, piece_svg, plan_moves, players, pos,
                      square_color, subtitle)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def game(moves, **headers):
    header = "".join(f'[{k} "{v}"]\n' for k, v in headers.items())
    return load_game(f"{header}\n{moves}")


def plan(moves):
    return list(plan_moves(game(moves)))


# --- geometry --------------------------------------------------------------

def test_pos_corners_are_symmetric():
    xa1, ya1, _ = pos(chess.A1)
    xh8, yh8, _ = pos(chess.H8)
    assert xh8 - xa1 == pytest.approx(7 * SQ)
    assert yh8 - ya1 == pytest.approx(7 * SQ)
    assert ya1 == pytest.approx(-yh8)


def test_pos_adjacent_squares_one_side_apart():
    assert pos(chess.E2)[1] + SQ == pytest.approx(pos(chess.E3)[1])
    assert pos(chess.E2)[0] + SQ == pytest.approx(pos(chess.F2)[0])


@pytest.mark.parametrize("square, dark", [
    (chess.A1, True), (chess.H1, False), (chess.A8, False), (chess.H8, True),
    (chess.D1, False), (chess.E1, True),
])
@pytest.mark.parametrize("name", THEMES)
def test_square_color(name, square, dark):
    theme = THEMES[name]
    assert square_color(square, theme) == (theme.dark if dark else theme.light)


def test_default_theme_exists():
    assert DEFAULT_THEME in THEMES
    assert square_color(chess.A1) == THEMES[DEFAULT_THEME].dark


@pytest.mark.parametrize("name", THEMES)
def test_themes_use_hex_colors(name):
    for color in vars(THEMES[name]).values():
        assert color.startswith("#") and len(color) == 7
        int(color[1:], 16)


# --- pieces ----------------------------------------------------------------

@pytest.mark.parametrize("symbol", "KQRBNPkqrbnp")
def test_piece_svg_fills_the_whole_box(symbol):
    svg = piece_svg(chess.Piece.from_symbol(symbol))
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    # the transparent rectangle must be the first element, right after <svg ...>
    opening = svg.index(">") + 1
    assert svg[opening:].startswith('<rect x="0" y="0" width="45" height="45"')
    assert "fill-opacity:0" in svg


def test_white_and_black_pieces_differ():
    white = piece_svg(chess.Piece(chess.KNIGHT, chess.WHITE))
    black = piece_svg(chess.Piece(chess.KNIGHT, chess.BLACK))
    assert "white-knight" in white and "black-knight" in black


# --- PGN parsing -----------------------------------------------------------

def test_empty_pgn():
    with pytest.raises(ValueError, match="no game"):
        load_game("")


def test_pgn_with_illegal_move():
    with pytest.raises(ValueError, match="invalid PGN"):
        load_game("1. e4 e5 2. Ke3")


def test_players_from_headers():
    assert players(game("1. e4", White="Tal", Black="Botvinnik")) == ("Tal", "Botvinnik")


def test_players_without_headers():
    assert players(load_game("1. e4")) == ("?", "?")


@pytest.mark.parametrize("headers, expected", [
    ({"Event": "World Championship", "Date": "1960.05.07"}, "World Championship · 1960"),
    ({"Event": "World Championship", "Date": "????.??.??"}, "World Championship"),
    ({"Date": "1851.06.21"}, "1851"),
    ({}, ""),
])
def test_subtitle(headers, expected):
    assert subtitle(game("1. e4", **headers)) == expected


@pytest.mark.parametrize("result, expected", [
    ("1-0", "White wins"), ("0-1", "Black wins"), ("1/2-1/2", "Draw"), ("*", ""),
])
def test_describe_result(result, expected):
    assert describe_result(result) == expected


# --- labels ----------------------------------------------------------------

@pytest.mark.parametrize("ply, san, expected", [
    (0, "e4", "1. e4"), (1, "e5", "1... e5"), (22, "O-O", "12. O-O"), (33, "Rd8#", "17... Rd8#"),
])
def test_move_label(ply, san, expected):
    assert move_label(ply, san) == expected


def test_labels_follow_the_game():
    assert [m.label for m in plan("1. e4 e5 2. Nf3 Nc6")] == \
        ["1. e4", "1... e5", "2. Nf3", "2... Nc6"]


# --- move planning ---------------------------------------------------------

def test_simple_move():
    (m,) = plan("1. e4")
    assert (m.from_sq, m.to_sq, m.captured, m.rook, m.promotion, m.check) == \
        (chess.E2, chess.E4, None, None, None, None)


def test_capture():
    m = plan("1. e4 d5 2. exd5")[-1]
    assert m.captured == chess.D5


def test_en_passant_captures_the_adjacent_pawn():
    m = plan("1. e4 a6 2. e5 d5 3. exd6")[-1]
    assert m.to_sq == chess.D6
    assert m.captured == chess.D5


@pytest.mark.parametrize("moves, king, rook", [
    ("1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O", (chess.E1, chess.G1), (chess.H1, chess.F1)),
    ("1. e4 e5 2. Nf3 Nf6 3. Bc4 Bc5 4. d3 O-O", (chess.E8, chess.G8), (chess.H8, chess.F8)),
    ("1. d4 d5 2. Nc3 Nc6 3. Bf4 Bf5 4. Qd2 Qd7 5. O-O-O", (chess.E1, chess.C1), (chess.A1, chess.D1)),
    ("1. d4 d5 2. Nc3 Nc6 3. Bf4 Bf5 4. Qd2 Qd7 5. e3 O-O-O", (chess.E8, chess.C8), (chess.A8, chess.D8)),
])
def test_castling_also_moves_the_rook(moves, king, rook):
    m = plan(moves)[-1]
    assert (m.from_sq, m.to_sq) == king
    assert m.rook == rook
    assert m.captured is None


def test_promotion_with_capture():
    m = plan("1. e4 d5 2. e5 f5 3. exf6 Nc6 4. fxg7 Be6 5. gxh8=N")[-1]
    assert m.promotion == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert m.captured == chess.H8
    assert m.label == "5. gxh8=N"


def test_black_promotion():
    m = plan("1. a4 h5 2. a5 h4 3. a6 h3 4. axb7 hxg2 5. bxa8=Q gxh1=Q")[-1]
    assert m.promotion == chess.Piece(chess.QUEEN, chess.BLACK)
    assert m.captured == chess.H1


def test_check_points_at_the_king():
    m = plan("1. e4 d5 2. Bb5+")[-1]
    assert m.check == chess.E8


def test_check_against_white():
    m = plan("1. f3 e5 2. g4 Qh4#")[-1]
    assert m.check == chess.E1
    assert m.label == "2... Qh4#"


# --- examples --------------------------------------------------------------

@pytest.mark.parametrize("file", sorted(EXAMPLES.glob("*.pgn")), ids=lambda p: p.name)
def test_examples_are_valid(file):
    g = load_game(file.read_text(encoding="utf-8"))
    assert len(list(plan_moves(g))) == len(list(g.mainline_moves())) > 0


def test_opera_game_ends_in_mate():
    g = load_game((EXAMPLES / "opera_game.pgn").read_text(encoding="utf-8"))
    assert list(plan_moves(g))[-1].label == "17. Rd8#"
    assert g.end().board().is_checkmate()


def test_replay_matches_python_chess():
    """Replaying the plan on a dict of pieces gives the final position."""
    for file in EXAMPLES.glob("*.pgn"):
        g = load_game(file.read_text(encoding="utf-8"))
        pieces = dict(g.board().piece_map())
        for m in plan_moves(g):
            piece = pieces.pop(m.from_sq)
            if m.captured is not None:
                del pieces[m.captured]
            if m.rook:
                pieces[m.rook[1]] = pieces.pop(m.rook[0])
            pieces[m.to_sq] = m.promotion or piece
        assert pieces == g.end().board().piece_map(), file.name
