# Example games

| File                  | Game                                             | Moves | What it shows                     |
|-----------------------|--------------------------------------------------|:-----:|-----------------------------------|
| `opera_game.pgn`      | Morphy – Duke Karl / Count Isouard, Paris 1858   | 17    | sacrifices and queenside castling |
| `immortal_game.pgn`   | Anderssen – Kieseritzky, London 1851             | 23    | "The Immortal Game": gives up both rooks |
| `evergreen_game.pgn`  | Anderssen – Dufresne, Berlin 1852                | 24    | "The Evergreen Game"              |
| `special_moves.pgn`   | composed position                                | 8     | en passant, promotion with capture, queenside and kingside castling |

To regenerate the GIFs in `assets/` (each one with a different theme):

```bash
pgn-gif examples/opera_game.pgn     -q l --theme brown -o assets/opera_game.gif
pgn-gif examples/immortal_game.pgn  -q l --theme green -o assets/immortal_game.gif
pgn-gif examples/evergreen_game.pgn -q l --theme blue  -o assets/evergreen_game.gif
pgn-gif examples/special_moves.pgn  -q l --theme gray  -o assets/special_moves.gif
```
