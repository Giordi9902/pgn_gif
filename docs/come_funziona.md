# Come funziona

Il progetto è diviso in due moduli con responsabilità nette:

```text
 partita.pgn
     │
     ▼
┌──────────────────────────────┐
│ pgn_core.py   (solo chess)   │   carica_partita() → valida il PGN
│                              │   pianifica()      → una Mossa per semimossa
└──────────────┬───────────────┘
               │  Mossa(da, a, catturata, torre, promozione, etichetta)
               ▼
┌──────────────────────────────┐
│ pgn_gif.py    (Manim)        │   PartitaPGN.construct() → animazioni
│                              │   renderizza()           → MP4 → GIF
└──────────────┬───────────────┘
               ▼
          partita.gif
```

## `pgn_core.py`: la logica

Non importa Manim, quindi si testa in millisecondi.

`pianifica(game)` scorre la linea principale con una `chess.Board` e, **prima**
di eseguire ogni mossa, ne ricava tutto ciò che serve per animarla:

| Campo         | Contenuto                                                        |
|---------------|------------------------------------------------------------------|
| `da`, `a`     | casa di partenza e arrivo del pezzo che si muove                 |
| `catturata`   | casa del pezzo da far sparire, oppure `None`                     |
| `torre`       | `(da, a)` della torre se la mossa è un arrocco                   |
| `promozione`  | il nuovo `chess.Piece` se un pedone promuove                     |
| `etichetta`   | testo da mostrare, es. `12. O-O-O` o `16... Nxb8`                |

I casi delicati:

- **En passant**: il pedone catturato *non* sta sulla casa d'arrivo, ma sulla
  stessa traversa della casa di partenza e sulla colonna di quella d'arrivo.
- **Arrocco**: python-chess lo rappresenta come una mossa del re di due case;
  la torre va spostata a parte (h→f per l'arrocco corto, a→d per il lungo).
- **Promozione**: il pedone arriva, poi viene sostituito dal nuovo pezzo del
  colore di chi ha mosso.
- **Notazione SAN**: dipende dalla posizione (`+`, `#`, disambiguazioni come
  `Nbd7`), quindi va calcolata prima di `board.push()`.

## `pgn_gif.py`: la grafica

`PartitaPGN.construct()`:

1. disegna 64 `Square` e le coordinate a–h, 1–8;
2. crea un `Text` Unicode (♚♛♜♝♞♟) per ogni pezzo, tenendoli in un
   dizionario `casa → oggetto`;
3. per ogni `Mossa` lancia in parallelo: dissolvenza del pezzo catturato,
   spostamento del pezzo (e della torre), aggiornamento dell'etichetta;
4. alla fine mostra il risultato (`1-0`, `0-1`, `½-½`, `*`).

I pezzi bianchi e neri usano lo stesso glifo pieno: cambia solo il colore di
riempimento, con un contorno del colore opposto per farli risaltare su
entrambe le case.

## Ottimizzazione della GIF

Le GIF scritte direttamente da Manim applicano un dithering che fa cambiare
ogni fotogramma, anche quando la scena è ferma: la compressione differenziale
del formato GIF non può lavorare e i file pesano 10–20 MB.

`renderizza()` invece produce un MP4 e lo converte con ffmpeg:

```text
split[a][b];
[a] palettegen=max_colors=64:stats_mode=diff [p];   # palette dai pixel che cambiano
[b][p] paletteuse=dither=none:diff_mode=rectangle    # riscrive solo il rettangolo modificato
```

La scacchiera ha pochi colori, quindi 64 sono più che sufficienti.

## Test

| File                   | Cosa verifica                                              |
|------------------------|------------------------------------------------------------|
| `tests/test_core.py`   | geometria, lettura PGN, etichette, catture, en passant, arrocchi (4 varianti), promozioni, esempi. Include una simulazione che riapplica il piano e confronta la posizione finale con python-chess. |
| `tests/test_render.py` | rendering vero di una GIF dalla CLI e gestione degli errori (marcati `slow`). |
