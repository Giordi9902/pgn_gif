# Usage guide

## Installation

`pgn_gif` relies on [Manim Community](https://www.manim.community/) for the
animation and on [python-chess](https://python-chess.readthedocs.io/) for the
rules of chess.

1. **System dependencies** (needed by Manim):

   | System         | Command                                                        |
   |----------------|----------------------------------------------------------------|
   | Debian/Ubuntu  | `sudo apt install libcairo2-dev libpango1.0-dev ffmpeg`        |
   | Fedora         | `sudo dnf install cairo-devel pango-devel ffmpeg`              |
   | macOS          | `brew install cairo pango ffmpeg`                              |
   | Windows        | see the [Manim guide](https://docs.manim.community/en/stable/installation.html) |

   Text is set in **DejaVu Sans**, which ships with almost every Linux
   distribution (`fonts-dejavu-core` on Debian/Ubuntu); if it is missing,
   Pango picks a similar font.

2. **The package**:

   ```bash
   git clone https://github.com/Giordi9902/pgn_gif.git
   cd pgn_gif
   pip install .
   ```

   The `pgn-gif` command is now available.

## Command line

```text
pgn-gif [-h] [-o OUTPUT] [-q {l,m,h,k}] [-t MOVE_TIME] [--theme THEME] pgn
```

| Option            | Meaning                                                 | Default                 |
|-------------------|---------------------------------------------------------|-------------------------|
| `pgn`             | PGN file to animate, or `-` to read from stdin          | —                       |
| `-o, --output`    | path of the GIF to create                               | PGN name with `.gif`    |
| `-q, --quality`   | `l` 480p15 · `m` 720p30 · `h` 1080p60 · `k` 2160p60      | `m`                     |
| `-t, --move-time` | seconds of animation for each ply                       | `0.5`                   |
| `--theme`         | board colours: `brown`, `green`, `blue`, `gray`         | `brown`                 |

### Themes

| Theme   | Light squares | Dark squares | Inspired by      |
|---------|---------------|--------------|------------------|
| `brown` | `#F0D9B5`     | `#B58863`    | Lichess (classic)|
| `green` | `#EEEED2`     | `#769656`    | Chess.com        |
| `blue`  | `#DEE3E6`     | `#8CA2AD`    | Lichess (blue)   |
| `gray`  | `#E0E0E0`     | `#A0A0A0`    | —                |

### Examples

```bash
# The simplest case: creates game.gif next to game.pgn
pgn-gif game.pgn

# A lightweight GIF for a README or a chat
pgn-gif examples/immortal_game.pgn -q l -o immortal.gif

# Slow motion: one and a half seconds per move, in full HD, blue theme
pgn-gif examples/evergreen_game.pgn -q h -t 1.5 --theme blue

# From stdin, e.g. downloading a game from Lichess
curl -s https://lichess.org/game/export/<id> | pgn-gif - -o lichess.gif
```

If the PGN contains several games, the first one is animated. Variations and
comments are ignored: only the mainline is animated.

### Errors

An empty PGN, or one with an illegal move, is rejected **before** rendering
starts, with exit code `1`:

```text
$ pgn-gif broken.pgn
error: invalid PGN: illegal san: 'Ke3' in rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2
```

## GIF size

When `ffmpeg` is on the `PATH`, Manim first renders an MP4 which is then
converted to a GIF with an optimized palette, updating only the regions that
change between one frame and the next. The result is **about 12× lighter**
than the GIF Manim writes directly (e.g. the Opera Game at 480p: 3.4 MB
instead of 42 MB). Without `ffmpeg` it falls back to Manim's GIF.

For even smaller GIFs: quality `l` and a lower `--move-time`.

## Using Manim directly

The script is also a regular Manim scene, handy to take advantage of every
Manim option (MP4, WebM, preview, transparent background...):

```bash
manim -qm --format=gif pgn_gif.py ChessGame      # GIF
manim -qh pgn_gif.py ChessGame                   # 1080p MP4
manim -pql pgn_gif.py ChessGame                  # quick preview
```

The game is chosen as follows:

1. the file named by the `PGN_GIF_FILE` environment variable;
2. otherwise `game.pgn` in the current directory;
3. otherwise the Opera Game built into the script.

The theme is chosen with the `PGN_GIF_THEME` variable:

```bash
PGN_GIF_FILE=examples/immortal_game.pgn PGN_GIF_THEME=green manim -qm --format=gif pgn_gif.py ChessGame
```

## From Python

```python
from pgn_gif import render_gif

with open("game.pgn") as f:
    render_gif(f.read(), "game.gif", quality="l", move_time=0.3, theme="blue")
```

## Customization

The main constants sit at the top of the two modules:

| Constant       | File          | Effect                                    |
|----------------|---------------|-------------------------------------------|
| `THEMES`       | `pgn_core.py` | board themes: add one and it shows up in `--theme` right away |
| `SQ`           | `pgn_core.py` | side of a square (Manim units)            |
| `BACKGROUND`, `GOLD`, `MUTED_TEXT` | `pgn_gif.py` | background and panel colours |
| `FONT`         | `pgn_gif.py`  | text font                                 |
| `MOVE_TIME`    | `pgn_gif.py`  | default duration of a move                |
| `GIF_FILTER`   | `pgn_gif.py`  | ffmpeg filter (e.g. `max_colors`)         |

A theme is a `Theme(light, dark, highlight, border)`:

```python
THEMES["purple"] = Theme("#E8E0F0", "#8B6FA8", "#F2C14E", "#4A3A5C")
```
