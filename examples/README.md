# Partite d'esempio

| File                  | Partita                                              | Mosse | Cosa mostra                       |
|-----------------------|------------------------------------------------------|:-----:|-----------------------------------|
| `opera.pgn`           | Morphy – Duca di Brunswick e Conte Isouard, 1858     | 17    | sacrifici e arrocco lungo         |
| `immortale.pgn`       | Anderssen – Kieseritzky, Londra 1851                 | 23    | "L'Immortale": dà via entrambe le torri |
| `sempreverde.pgn`     | Anderssen – Dufresne, Berlino 1852                   | 24    | "La Sempreverde"                  |
| `mosse_speciali.pgn`  | partita costruita a tavolino                         | 8     | en passant, promozione con cattura, arrocco lungo e corto |

Per rigenerare le GIF in `assets/`:

```bash
for f in examples/*.pgn; do
  pgn-gif "$f" -q l -o "assets/$(basename "${f%.pgn}").gif"
done
```
