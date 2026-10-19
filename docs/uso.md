# Guida all'uso

## Installazione

`pgn_gif` si appoggia a [Manim Community](https://www.manim.community/) per
l'animazione e a [python-chess](https://python-chess.readthedocs.io/) per le
regole degli scacchi.

1. **Dipendenze di sistema** (servono a Manim):

   | Sistema        | Comando                                                        |
   |----------------|----------------------------------------------------------------|
   | Debian/Ubuntu  | `sudo apt install libcairo2-dev libpango1.0-dev ffmpeg`        |
   | Fedora         | `sudo dnf install cairo-devel pango-devel ffmpeg`              |
   | macOS          | `brew install cairo pango ffmpeg`                              |
   | Windows        | vedi la [guida di Manim](https://docs.manim.community/en/stable/installation.html) |

   Serve anche un font con i simboli degli scacchi: il programma usa
   **DejaVu Sans**, presente di serie su quasi tutte le distribuzioni Linux
   (`fonts-dejavu-core` su Debian/Ubuntu).

2. **Il pacchetto**:

   ```bash
   git clone https://github.com/Giordi9902/pgn_gif.git
   cd pgn_gif
   pip install .
   ```

   Ora è disponibile il comando `pgn-gif`.

## Riga di comando

```text
pgn-gif [-h] [-o OUTPUT] [-q {l,m,h,k}] [-t TEMPO] pgn
```

| Opzione           | Significato                                             | Predefinito             |
|-------------------|---------------------------------------------------------|-------------------------|
| `pgn`             | file PGN da animare, oppure `-` per leggere da stdin    | —                       |
| `-o, --output`    | percorso della GIF da creare                            | nome del PGN con `.gif` |
| `-q, --qualita`   | `l` 480p15 · `m` 720p30 · `h` 1080p60 · `k` 2160p60      | `m`                     |
| `-t, --tempo`     | secondi di animazione per ogni semimossa                | `0.5`                   |

### Esempi

```bash
# Il caso più semplice: crea partita.gif accanto a partita.pgn
pgn-gif partita.pgn

# GIF leggera per un README o una chat
pgn-gif examples/immortale.pgn -q l -o immortale.gif

# Moviola: un secondo e mezzo per mossa, in alta definizione
pgn-gif examples/sempreverde.pgn -q h -t 1.5

# Da stdin, ad esempio scaricando una partita da Lichess
curl -s https://lichess.org/game/export/<id> | pgn-gif - -o lichess.gif
```

Se il PGN contiene più partite viene animata la prima. Varianti e commenti
vengono ignorati: si anima solo la linea principale.

### Errori

Un PGN vuoto o con una mossa illegale viene rifiutato **prima** di avviare il
rendering, con codice di uscita `1`:

```text
$ pgn-gif rotto.pgn
errore: PGN non valido: illegal san: 'Ke3' in rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2
```

## Dimensione delle GIF

Se `ffmpeg` è nel `PATH`, Manim renderizza prima un MP4 che viene poi
convertito in GIF con una palette ottimizzata e aggiornando solo le zone che
cambiano tra un fotogramma e l'altro. Il risultato è **6–8 volte più leggero**
della GIF che Manim scrive direttamente (es. Partita dell'Opera a 480p:
2,1 MB invece di 13 MB). Senza `ffmpeg` si ripiega sulla GIF di Manim.

Per GIF ancora più piccole: qualità `l` e un `--tempo` più basso.

## Uso diretto con Manim

Lo script è anche una normale scena Manim, utile per sfruttare tutte le
opzioni di Manim (MP4, WebM, anteprima, sfondo trasparente...):

```bash
manim -qm --format=gif pgn_gif.py PartitaPGN      # GIF
manim -qh pgn_gif.py PartitaPGN                   # MP4 1080p
manim -pql pgn_gif.py PartitaPGN                  # anteprima veloce
```

La partita viene scelta così:

1. il file indicato dalla variabile d'ambiente `PGN_GIF_FILE`;
2. altrimenti `partita.pgn` nella cartella corrente;
3. altrimenti la Partita dell'Opera incorporata nello script.

```bash
PGN_GIF_FILE=examples/immortale.pgn manim -qm --format=gif pgn_gif.py PartitaPGN
```

## Uso da Python

```python
from pgn_gif import renderizza

with open("partita.pgn") as f:
    renderizza(f.read(), "partita.gif", qualita="l", tempo_mossa=0.3)
```

## Personalizzazione

Le costanti principali stanno in cima ai due moduli:

| Costante       | File          | Effetto                                   |
|----------------|---------------|-------------------------------------------|
| `LIGHT`, `DARK`| `pgn_core.py` | colori delle case                         |
| `SQ`           | `pgn_core.py` | lato di una casa (unità Manim)            |
| `GLYPH`        | `pgn_core.py` | simboli Unicode dei pezzi                 |
| `TEMPO_MOSSA`  | `pgn_gif.py`  | durata predefinita di una mossa           |
| `FILTRO_GIF`   | `pgn_gif.py`  | filtro ffmpeg (es. `max_colors`)          |
