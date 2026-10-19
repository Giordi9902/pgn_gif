# How it works

The project is split into two modules with clear responsibilities:

```text
 game.pgn
     │
     ▼
┌──────────────────────────────┐
│ pgn_core.py   (chess only)   │   load_game()   → validates the PGN
│                              │   plan_moves()  → one MovePlan per ply
│                              │   piece_svg()   → SVG of each piece
└──────────────┬───────────────┘
               │  MovePlan(from_sq, to_sq, captured, rook, promotion, label, check)
               ▼
┌──────────────────────────────┐
│ pgn_gif.py    (Manim)        │   ChessGame.construct() → animations
│                              │   render_gif()          → MP4 → GIF
└──────────────┬───────────────┘
               ▼
           game.gif
```

## `pgn_core.py`: the logic

It does not import Manim, so it is tested in milliseconds.

`plan_moves(game)` walks the mainline with a `chess.Board` and, **before**
playing each move, extracts everything needed to animate it:

| Field              | Contents                                                     |
|--------------------|--------------------------------------------------------------|
| `from_sq`, `to_sq` | origin and destination of the moving piece                   |
| `captured`         | square of the piece to remove, or `None`                     |
| `rook`             | `(from, to)` of the rook if the move is castling             |
| `promotion`        | the new `chess.Piece` if a pawn promotes                     |
| `label`            | text to display, e.g. `12. O-O-O` or `16... Nxb8`            |
| `check`            | square of the king in check after the move, or `None`        |

The tricky cases:

- **En passant**: the captured pawn is *not* on the destination square, but
  on the rank of the origin square and the file of the destination.
- **Castling**: python-chess represents it as a two-square king move; the
  rook has to be moved separately (h→f for kingside, a→d for queenside).
- **Promotion**: the pawn arrives, then gets replaced by the new piece in
  the colour of the side that moved.
- **SAN notation**: it depends on the position (`+`, `#`, disambiguation such
  as `Nbd7`), so it must be computed before `board.push()`; check, on the
  other hand, is read afterwards.

### The pieces

The SVGs come from python-chess's `chess.svg.piece()` (the "cburnett" set,
the same as Lichess and Wikipedia): they are not copied into the repository
but generated on the fly. Each piece is drawn in a 45×45 box, but Manim's
`SVGMobject` fits the object to its content: without a fix a pawn would be
as tall as a king. `piece_svg()` therefore adds a transparent 45×45
rectangle as the first element, so every piece keeps its original
proportions.

## `pgn_gif.py`: the graphics

`ChessGame.construct()` builds the scene in layers, bottom to top:

```text
shadow → frame → 64 squares → coordinates → last-move highlight → check glow → pieces
```

1. draws the frame with its shadow, the squares and the coordinates (inside
   the squares, in the colour of the opposite square, as on Lichess);
2. creates an `SVGMobject` for each piece, keeping them in a
   `square → object` dict;
3. for each `MovePlan`, in parallel: moves the highlight, shrinks and fades
   out the captured piece, moves the piece (brought to the front) and the
   rook if any, lights up the red glow on check, highlights the side to
   move, cross-fades the label and extends the progress bar;
4. at the end shows the result (`1-0`, `0-1`, `½-½`, `*`) and its
   description.

## GIF optimization

GIFs written directly by Manim are dithered, so every frame changes even
when the scene is still: GIF's frame-difference compression cannot work and
files weigh tens of MB (42 MB for the Opera Game at 480p).

`render_gif()` renders an MP4 instead and converts it with ffmpeg:

```text
split[a][b];
[a] palettegen=max_colors=96:stats_mode=full [p];   # a single palette for the whole GIF
[b][p] paletteuse=dither=none:diff_mode=rectangle    # only rewrite the changed rectangle
```

The scene has few colours, so 96 are enough. `stats_mode=full` matters:
with `stats_mode=diff` (palette computed only from changing pixels) faint
ghosts remain where pieces have passed. Result: 3.4 MB instead of 42.

## Tests

| File                   | What it checks                                             |
|------------------------|------------------------------------------------------------|
| `tests/test_core.py`   | geometry, themes, piece SVGs, PGN parsing, headers, labels, captures, en passant, castling (4 variants), promotions, checks, examples. Includes a replay of the plan compared with python-chess's final position. |
| `tests/test_render.py` | real GIF rendering from the CLI, with several themes, and error handling (marked `slow`). |
