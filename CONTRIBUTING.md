# Contribuire

Grazie dell'interesse! Ecco come muoversi.

## Ambiente di sviluppo

```bash
git clone https://github.com/Giordi9902/pgn_gif.git
cd pgn_gif
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Manim ha bisogno di Cairo, Pango e ffmpeg; vedi la
[guida di installazione di Manim](https://docs.manim.community/en/stable/installation.html).

## Test

```bash
pytest                 # tutta la suite
pytest -m "not slow"   # solo la logica, senza renderizzare GIF (pochi secondi)
```

## Linee guida

- La logica degli scacchi va in `pgn_core.py`, che non deve importare Manim:
  così resta testabile in pochi millisecondi.
- `pgn_gif.py` contiene solo la parte grafica e la riga di comando.
- Ogni nuova regola o caso particolare va accompagnato da un test in
  `tests/test_core.py`.
- Codice, commenti e messaggi sono in italiano: manteniamo lo stile.
- Se aggiungi una partita in `examples/`, viene validata automaticamente dai test.
