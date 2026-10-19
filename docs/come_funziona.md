# Come funziona

Il progetto è diviso in due moduli con responsabilità nette:

```text
 partita.pgn
     │
     ▼
┌──────────────────────────────┐
│ pgn_core.py   (solo chess)   │   carica_partita() → valida il PGN
│                              │   pianifica()      → una Mossa per semimossa
│                              │   pezzo_svg()      → SVG di ogni pezzo
└──────────────┬───────────────┘
               │  Mossa(da, a, catturata, torre, promozione, etichetta, scacco)
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
| `scacco`      | casa del re sotto scacco dopo la mossa, oppure `None`            |

I casi delicati:

- **En passant**: il pedone catturato *non* sta sulla casa d'arrivo, ma sulla
  stessa traversa della casa di partenza e sulla colonna di quella d'arrivo.
- **Arrocco**: python-chess lo rappresenta come una mossa del re di due case;
  la torre va spostata a parte (h→f per l'arrocco corto, a→d per il lungo).
- **Promozione**: il pedone arriva, poi viene sostituito dal nuovo pezzo del
  colore di chi ha mosso.
- **Notazione SAN**: dipende dalla posizione (`+`, `#`, disambiguazioni come
  `Nbd7`), quindi va calcolata prima di `board.push()`; lo scacco invece si
  legge dopo.

### I pezzi

Gli SVG vengono da `chess.svg.piece()` di python-chess (set "cburnett", lo
stesso di Lichess e Wikipedia): non sono copiati nel repository, ma generati
al volo. Ogni pezzo è disegnato in un riquadro 45×45, ma `SVGMobject` di Manim
adatta l'oggetto al suo contenuto: senza correzioni un pedone verrebbe alto
quanto un re. `pezzo_svg()` aggiunge quindi un rettangolo trasparente 45×45
come primo elemento, così tutti i pezzi mantengono le proporzioni originali.

## `pgn_gif.py`: la grafica

`PartitaPGN.construct()` costruisce la scena a livelli, dal basso verso l'alto:

```text
ombra → cornice → 64 case → coordinate → evidenza ultima mossa → alone di scacco → pezzi
```

1. disegna cornice con ombra, case e coordinate (dentro le case, nel colore
   della casa opposta, come su Lichess);
2. crea un `SVGMobject` per ogni pezzo, tenendoli in un dizionario
   `casa → oggetto`;
3. per ogni `Mossa`, in parallelo: sposta l'evidenziazione, fa sparire il
   pezzo catturato rimpicciolendolo, muove il pezzo (portato in primo piano) e
   l'eventuale torre, accende l'alone rosso se c'è scacco, mette in risalto il
   giocatore che deve muovere, cambia l'etichetta con una dissolvenza e
   allunga la barra di avanzamento;
4. alla fine mostra il risultato (`1-0`, `0-1`, `½-½`, `*`) e la sua
   descrizione.

## Ottimizzazione della GIF

Le GIF scritte direttamente da Manim applicano un dithering che fa cambiare
ogni fotogramma, anche quando la scena è ferma: la compressione differenziale
del formato GIF non può lavorare e i file pesano decine di MB (42 MB per la
Partita dell'Opera a 480p).

`renderizza()` invece produce un MP4 e lo converte con ffmpeg:

```text
split[a][b];
[a] palettegen=max_colors=96:stats_mode=full [p];   # un'unica palette per tutta la GIF
[b][p] paletteuse=dither=none:diff_mode=rectangle    # riscrive solo il rettangolo modificato
```

La scena ha pochi colori, quindi 96 bastano. `stats_mode=full` è importante:
con `stats_mode=diff` (palette calcolata solo sui pixel che cambiano) restano
deboli aloni dove i pezzi sono passati. Risultato: 3,4 MB invece di 42.

## Test

| File                   | Cosa verifica                                              |
|------------------------|------------------------------------------------------------|
| `tests/test_core.py`   | geometria, temi, SVG dei pezzi, lettura PGN, intestazioni, etichette, catture, en passant, arrocchi (4 varianti), promozioni, scacchi, esempi. Include una simulazione che riapplica il piano e confronta la posizione finale con python-chess. |
| `tests/test_render.py` | rendering vero di una GIF dalla CLI, con più temi, e gestione degli errori (marcati `slow`). |
