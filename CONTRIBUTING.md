# Contributing

Thanks for your interest! Here's how to get going.

## Development setup

```bash
git clone https://github.com/Giordi9902/pgn_gif.git
cd pgn_gif
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Manim needs Cairo, Pango and ffmpeg; see the
[Manim installation guide](https://docs.manim.community/en/stable/installation.html).

## Tests

```bash
pytest                 # the whole suite
pytest -m "not slow"   # logic only, no GIF rendering (a couple of seconds)
```

## Guidelines

- Chess logic belongs in `pgn_core.py`, which must not import Manim: this
  keeps it testable in milliseconds.
- `pgn_gif.py` only contains the graphics and the command line.
- Every new rule or edge case comes with a test in `tests/test_core.py`.
- Any game added to `examples/` is validated automatically by the tests.
