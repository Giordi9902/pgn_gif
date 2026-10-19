from pathlib import Path

import chess
import pytest

from pgn_core import (SQ, TEMA_PREDEFINITO, TEMI, carica_partita, colore_casa,
                      descrivi_risultato, etichetta, giocatori, pezzo_svg, pianifica,
                      pos, sottotitolo)

ESEMPI = Path(__file__).resolve().parent.parent / "examples"


def partita(mosse, **headers):
    intestazione = "".join(f'[{k} "{v}"]\n' for k, v in headers.items())
    return carica_partita(f"{intestazione}\n{mosse}")


def piano(mosse):
    return list(pianifica(partita(mosse)))


# --- geometria -------------------------------------------------------------

def test_pos_angoli_simmetrici():
    xa1, ya1, _ = pos(chess.A1)
    xh8, yh8, _ = pos(chess.H8)
    assert xh8 - xa1 == pytest.approx(7 * SQ)
    assert yh8 - ya1 == pytest.approx(7 * SQ)
    assert ya1 == pytest.approx(-yh8)


def test_pos_case_adiacenti_distano_un_lato():
    assert pos(chess.E2)[1] + SQ == pytest.approx(pos(chess.E3)[1])
    assert pos(chess.E2)[0] + SQ == pytest.approx(pos(chess.F2)[0])


@pytest.mark.parametrize("casa, scura", [
    (chess.A1, True), (chess.H1, False), (chess.A8, False), (chess.H8, True),
    (chess.D1, False), (chess.E1, True),
])
@pytest.mark.parametrize("nome", TEMI)
def test_colore_casa(nome, casa, scura):
    tema = TEMI[nome]
    assert colore_casa(casa, tema) == (tema.scura if scura else tema.chiara)


def test_tema_predefinito_esiste():
    assert TEMA_PREDEFINITO in TEMI
    assert colore_casa(chess.A1) == TEMI[TEMA_PREDEFINITO].scura


@pytest.mark.parametrize("nome", TEMI)
def test_temi_con_colori_esadecimali(nome):
    for colore in vars(TEMI[nome]).values():
        assert colore.startswith("#") and len(colore) == 7
        int(colore[1:], 16)


# --- pezzi -----------------------------------------------------------------

@pytest.mark.parametrize("simbolo", "KQRBNPkqrbnp")
def test_pezzo_svg_occupa_tutto_il_riquadro(simbolo):
    svg = pezzo_svg(chess.Piece.from_symbol(simbolo))
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    # il rettangolo trasparente deve essere il primo elemento, subito dopo <svg ...>
    apertura = svg.index(">") + 1
    assert svg[apertura:].startswith('<rect x="0" y="0" width="45" height="45"')
    assert "fill-opacity:0" in svg


def test_pezzi_bianchi_e_neri_diversi():
    bianco = pezzo_svg(chess.Piece(chess.KNIGHT, chess.WHITE))
    nero = pezzo_svg(chess.Piece(chess.KNIGHT, chess.BLACK))
    assert "white-knight" in bianco and "black-knight" in nero


# --- lettura del PGN -------------------------------------------------------

def test_pgn_vuoto():
    with pytest.raises(ValueError, match="nessuna partita"):
        carica_partita("")


def test_pgn_con_mossa_illegale():
    with pytest.raises(ValueError, match="non valido"):
        carica_partita("1. e4 e5 2. Ke3")


def test_giocatori_da_header():
    assert giocatori(partita("1. e4", White="Tal", Black="Botvinnik")) == ("Tal", "Botvinnik")


def test_giocatori_senza_header():
    assert giocatori(carica_partita("1. e4")) == ("?", "?")


@pytest.mark.parametrize("headers, atteso", [
    ({"Event": "Mondiale", "Date": "1960.05.07"}, "Mondiale · 1960"),
    ({"Event": "Mondiale", "Date": "????.??.??"}, "Mondiale"),
    ({"Date": "1851.06.21"}, "1851"),
    ({}, ""),
])
def test_sottotitolo(headers, atteso):
    assert sottotitolo(partita("1. e4", **headers)) == atteso


@pytest.mark.parametrize("risultato, atteso", [
    ("1-0", "Vince il Bianco"), ("0-1", "Vince il Nero"), ("1/2-1/2", "Patta"), ("*", ""),
])
def test_descrivi_risultato(risultato, atteso):
    assert descrivi_risultato(risultato) == atteso


# --- etichette -------------------------------------------------------------

@pytest.mark.parametrize("numero, san, atteso", [
    (0, "e4", "1. e4"), (1, "e5", "1... e5"), (22, "O-O", "12. O-O"), (33, "Rd8#", "17... Rd8#"),
])
def test_etichetta(numero, san, atteso):
    assert etichetta(numero, san) == atteso


def test_etichette_seguono_la_partita():
    assert [m.etichetta for m in piano("1. e4 e5 2. Nf3 Nc6")] == \
        ["1. e4", "1... e5", "2. Nf3", "2... Nc6"]


# --- pianificazione delle mosse --------------------------------------------

def test_mossa_semplice():
    (m,) = piano("1. e4")
    assert (m.da, m.a, m.catturata, m.torre, m.promozione, m.scacco) == \
        (chess.E2, chess.E4, None, None, None, None)


def test_scacco_indica_la_casa_del_re():
    m = piano("1. e4 d5 2. Bb5+")[-1]
    assert m.scacco == chess.E8


def test_scacco_al_bianco():
    m = piano("1. f3 e5 2. g4 Qh4#")[-1]
    assert m.scacco == chess.E1
    assert m.etichetta == "2... Qh4#"



def test_cattura():
    m = piano("1. e4 d5 2. exd5")[-1]
    assert m.catturata == chess.D5


def test_en_passant_cattura_il_pedone_accanto():
    m = piano("1. e4 a6 2. e5 d5 3. exd6")[-1]
    assert m.a == chess.D6
    assert m.catturata == chess.D5


@pytest.mark.parametrize("mosse, re, torre", [
    ("1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O", (chess.E1, chess.G1), (chess.H1, chess.F1)),
    ("1. e4 e5 2. Nf3 Nf6 3. Bc4 Bc5 4. d3 O-O", (chess.E8, chess.G8), (chess.H8, chess.F8)),
    ("1. d4 d5 2. Nc3 Nc6 3. Bf4 Bf5 4. Qd2 Qd7 5. O-O-O", (chess.E1, chess.C1), (chess.A1, chess.D1)),
    ("1. d4 d5 2. Nc3 Nc6 3. Bf4 Bf5 4. Qd2 Qd7 5. e3 O-O-O", (chess.E8, chess.C8), (chess.A8, chess.D8)),
])
def test_arrocco_muove_anche_la_torre(mosse, re, torre):
    m = piano(mosse)[-1]
    assert (m.da, m.a) == re
    assert m.torre == torre
    assert m.catturata is None


def test_promozione_con_cattura():
    m = piano("1. e4 d5 2. e5 f5 3. exf6 Nc6 4. fxg7 Be6 5. gxh8=N")[-1]
    assert m.promozione == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert m.catturata == chess.H8
    assert m.etichetta == "5. gxh8=N"


def test_promozione_del_nero():
    m = piano("1. a4 h5 2. a5 h4 3. a6 h3 4. axb7 hxg2 5. bxa8=Q gxh1=Q")[-1]
    assert m.promozione == chess.Piece(chess.QUEEN, chess.BLACK)
    assert m.catturata == chess.H1


# --- esempi ----------------------------------------------------------------

@pytest.mark.parametrize("file", sorted(ESEMPI.glob("*.pgn")), ids=lambda p: p.name)
def test_esempi_validi(file):
    game = carica_partita(file.read_text(encoding="utf-8"))
    assert len(list(pianifica(game))) == len(list(game.mainline_moves())) > 0


def test_opera_finisce_con_matto():
    game = carica_partita((ESEMPI / "opera.pgn").read_text(encoding="utf-8"))
    assert list(pianifica(game))[-1].etichetta == "17. Rd8#"
    assert game.end().board().is_checkmate()


def test_simulazione_coerente_con_python_chess():
    """Riapplicando il piano a un dizionario di pezzi si ottiene la posizione finale."""
    for file in ESEMPI.glob("*.pgn"):
        game = carica_partita(file.read_text(encoding="utf-8"))
        pezzi = dict(game.board().piece_map())
        for m in pianifica(game):
            pezzo = pezzi.pop(m.da)
            if m.catturata is not None:
                del pezzi[m.catturata]
            if m.torre:
                pezzi[m.torre[1]] = pezzi.pop(m.torre[0])
            pezzi[m.a] = m.promozione or pezzo
        assert pezzi == game.end().board().piece_map(), file.name
