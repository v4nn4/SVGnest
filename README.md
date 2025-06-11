# SVG Nest Python

This project provides a Python-based command line interface for a simple SVG nesting example.

The original JavaScript implementation is kept in the `old/` directory.

## Usage

Install the package (Poetry is recommended):

```bash
poetry install
```

To pack all SVGs inside `data/raw` and write a combined SVG to `output/nested.svg` run:

```bash
poetry run python main.py nest
```

The packing algorithm is implemented in `src/placer.py` using `shapely`.
