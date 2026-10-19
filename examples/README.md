# Partite d'esempio

| File                  | Partita                                              | Mosse | Cosa mostra                       |
|-----------------------|------------------------------------------------------|:-----:|-----------------------------------|
| `opera.pgn`           | Morphy – Duca di Brunswick e Conte Isouard, 1858     | 17    | sacrifici e arrocco lungo         |
| `immortale.pgn`       | Anderssen – Kieseritzky, Londra 1851                 | 23    | "L'Immortale": dà via entrambe le torri |
| `sempreverde.pgn`     | Anderssen – Dufresne, Berlino 1852                   | 24    | "La Sempreverde"                  |
| `mosse_speciali.pgn`  | partita costruita a tavolino                         | 8     | en passant, promozione con cattura, arrocco lungo e corto |

Per rigenerare le GIF in `assets/` (ognuna con un tema diverso):

```bash
pgn-gif examples/opera.pgn          -q l --tema marrone -o assets/opera.gif
pgn-gif examples/immortale.pgn      -q l --tema verde   -o assets/immortale.gif
pgn-gif examples/sempreverde.pgn    -q l --tema blu     -o assets/sempreverde.gif
pgn-gif examples/mosse_speciali.pgn -q l --tema grigio  -o assets/mosse_speciali.gif
```
