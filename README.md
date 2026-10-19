<div align="center">

# ♞ pgn_gif

**Trasforma qualsiasi partita di scacchi in notazione PGN in una GIF animata.**

[![test](https://github.com/Giordi9902/pgn_gif/actions/workflows/test.yml/badge.svg)](https://github.com/Giordi9902/pgn_gif/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Manim](https://img.shields.io/badge/animato%20con-Manim-ECE7E2)](https://www.manim.community/)
[![Licenza: MIT](https://img.shields.io/badge/licenza-MIT-green.svg)](LICENSE)

<img src="assets/opera.gif" alt="La Partita dell'Opera di Morphy animata" width="720">

*La Partita dell'Opera — Morphy contro il Duca di Brunswick e il Conte Isouard, Parigi 1858.*

</div>

---

## ✨ Caratteristiche

- **Un comando, una GIF**: `pgn-gif partita.pgn` e hai finito.
- **Regole complete**: catture, en passant, arrocco corto e lungo, promozione (anche con cattura) — tutte animate.
- **Notazione sempre visibile**: ogni mossa compare in SAN (`12. O-O-O`, `16... Nxb8`) accanto alla scacchiera, con il risultato finale.
- **GIF leggere**: conversione ottimizzata con ffmpeg, **6–8 volte più piccole** dell'output diretto di Manim.
- **Validazione in anticipo**: un PGN con mosse illegali viene rifiutato con un messaggio chiaro, prima di perdere tempo a renderizzare.
- **Tre modi di usarlo**: riga di comando, scena Manim, funzione Python.
- **Testato**: 35 test, dalla geometria della scacchiera al rendering completo, su Python 3.10–3.13.

## 🚀 Avvio rapido

```bash
# 1. Dipendenze di sistema di Manim (Debian/Ubuntu; per altri sistemi vedi docs/uso.md)
sudo apt install libcairo2-dev libpango1.0-dev ffmpeg

# 2. Installazione
git clone https://github.com/Giordi9902/pgn_gif.git
cd pgn_gif
pip install .

# 3. Via!
pgn-gif examples/immortale.pgn
```

## 🎬 Galleria

<table>
  <tr>
    <td align="center"><img src="assets/immortale.gif" alt="L'Immortale" width="400"><br><b>L'Immortale</b><br>Anderssen – Kieseritzky, 1851</td>
    <td align="center"><img src="assets/sempreverde.gif" alt="La Sempreverde" width="400"><br><b>La Sempreverde</b><br>Anderssen – Dufresne, 1852</td>
  </tr>
  <tr>
    <td align="center" colspan="2"><img src="assets/mosse_speciali.gif" alt="Mosse speciali" width="400"><br><b>Mosse speciali</b><br>en passant · promozione con cattura · arrocco lungo e corto</td>
  </tr>
</table>

I PGN di partenza sono in [`examples/`](examples/).

## 🛠️ Uso

### Riga di comando

```text
pgn-gif [-h] [-o OUTPUT] [-q {l,m,h,k}] [-t TEMPO] pgn
```

| Opzione         | Significato                                         | Predefinito             |
|-----------------|-----------------------------------------------------|-------------------------|
| `pgn`           | file PGN, oppure `-` per leggere da stdin           | —                       |
| `-o, --output`  | GIF da creare                                       | nome del PGN con `.gif` |
| `-q, --qualita` | `l` 480p · `m` 720p · `h` 1080p · `k` 4K            | `m`                     |
| `-t, --tempo`   | secondi per semimossa                               | `0.5`                   |

```bash
pgn-gif examples/sempreverde.pgn -q h -t 1.5           # moviola in alta definizione
curl -s https://lichess.org/game/export/<id> | pgn-gif - -o lichess.gif
```

### Come scena Manim

```bash
PGN_GIF_FILE=examples/opera.pgn manim -qm --format=gif pgn_gif.py PartitaPGN
```

Senza `PGN_GIF_FILE` viene usato `partita.pgn` della cartella corrente, oppure la Partita dell'Opera incorporata.

### Da Python

```python
from pgn_gif import renderizza

renderizza(open("partita.pgn").read(), "partita.gif", qualita="l", tempo_mossa=0.3)
```

## 📚 Documentazione

| Documento                                      | Contenuto                                                  |
|------------------------------------------------|------------------------------------------------------------|
| [Guida all'uso](docs/uso.md)                   | installazione per sistema, tutte le opzioni, personalizzazione |
| [Come funziona](docs/come_funziona.md)         | architettura, casi speciali degli scacchi, ottimizzazione GIF |
| [Contribuire](CONTRIBUTING.md)                 | ambiente di sviluppo e linee guida                         |

## 🧪 Test

```bash
pip install -e ".[dev]"
pytest                  # suite completa (~5 s)
pytest -m "not slow"    # solo la logica, senza renderizzare
```

Tra i test c'è una simulazione che riapplica il piano di animazione di ogni partita d'esempio e verifica che la posizione finale coincida, pezzo per pezzo, con quella calcolata da python-chess.

## 🗂️ Struttura

```text
pgn_gif/
├── pgn_core.py        # logica pura: lettura PGN e piano delle mosse (solo python-chess)
├── pgn_gif.py         # scena Manim, rendering e riga di comando
├── examples/          # partite PGN d'esempio
├── assets/            # GIF generate dagli esempi
├── docs/              # documentazione
└── tests/             # test pytest
```

## 📄 Licenza

Distribuito con licenza [MIT](LICENSE).

Costruito con [Manim Community](https://www.manim.community/) e [python-chess](https://python-chess.readthedocs.io/).
