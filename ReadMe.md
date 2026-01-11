# 🧩 PolyQR: QR Codes as Polygons

PolyQR turns a message into a QR code where each contiguous black region is drawn as **one merged polygon**, not as a grid of tiny squares.
This **eliminates hideous hairline gaps** between modules that appear with naive approaches (example below) and **minimizes the number of points per polygon** to keep the output compact.

PolyQR can generate:

- **TikZ** code with full styling support (e.g. rounded corners)
- **SVG** paths that are aggressively minimized to save space

The `pytest`-based **test suite** with **100% coverage** (for both TikZ and SVG) lives in the [`tests` directory](https://github.com/KurtBoehm/polyqr/blob/main/tests).

[![Tests with 100% coverage](https://github.com/KurtBoehm/polyqr/actions/workflows/test.yml/badge.svg)](https://github.com/KurtBoehm/polyqr/actions/workflows/test.yml)

## 📦 Installation

PolyQR is available [on PyPI](https://pypi.org/project/polyqr/) and can be installed with `pip`:

```sh
pip install polyqr
```

## 🖼️ TikZ Output

PolyQR provides the command-line tool `polyqr_tikz`:

```sh
polyqr_tikz "1mm" "rounded corners=0.25mm" "https://github.com/KurtBoehm/polyqr"
```

This prints a `tikzpicture` environment of the following form to `stdout`:

```latex
\begin{tikzpicture}[x=1mm, y=1mm, qrpoly/.style={fill=black, draw=none, even odd rule, rounded corners=0.25mm}]
  % \draw commands to draw a QR code representing https://github.com/KurtBoehm/polyqr
\end{tikzpicture}
```

If the optional flag `--full-size` is supplied, the size argument (`1mm` above) specifies the size of the entire QR code rather than the size of each module.

Because each connected component is rendered as a single polygon, TikZ styles such as `rounded corners` apply only to the outer boundary of each contiguous region.
This also removes visible gaps between modules, which are apparent when each module is drawn as a separate square (view full-screen):

| Separate squares                                                                           | PolyQR                                                                                       | PolyQR with rounded corners                                                                                  |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| ![Basic TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-basic.png) | ![PolyQR TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-polyqr.png) | ![Rounded PolyQR TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-polyqr-rounded.png) |

The LaTeX source used to generate these examples is in [`docs/tikz.tex`](https://github.com/KurtBoehm/polyqr/blob/main/docs/tikz.tex).

TikZ code can also be generated directly from Python:

```python
from polyqr import QrCodePainter

painter = QrCodePainter("https://github.com/KurtBoehm/polyqr")

print(painter.tikz(size="1mm", style="rounded corners=0.25mm", full_size=False))
```

## 🖼️ SVG Output

PolyQR can also generate very compact SVG paths:

- The entire QR code (or each contiguous area) becomes a single `<path>` using `fill-rule="evenodd"` to handle holes.
- All segments are axis-aligned and encoded using only `M`, `H`, `V`, and `Z`.
- For every move/line, absolute vs. relative commands are chosen to minimize text length.

SVG generation is available programmatically:

```python
from polyqr import QrCodePainter

painter = QrCodePainter("https://github.com/KurtBoehm/polyqr")

# Full SVG document as a string
svg_doc = painter.svg

# Single <path> element covering the full QR code
svg_path = painter.svg_path

# Generator over <path> elements, one per contiguous region
for path in painter.svg_paths:
    print(path)
```

[`qrcode`](https://pypi.org/project/qrcode/), which PolyQR uses to generate the underlying module matrix, can also output SVG via `qrcode.svg.SvgPathImage` (among others).
`SvgPathImage` avoids gaps by merging all modules into a single `<path>`, but the resulting SVG is much larger.

For the message `https://github.com/KurtBoehm/polyqr`:

- `SvgPathImage` output: ≈ 6.4 kB ([`docs/svg-qrcode.svg`](https://github.com/KurtBoehm/polyqr/blob/main/docs/svg-qrcode.svg))
- `QrCodePainter.svg` output: ≈ 1.6 kB ([`docs/svg-polyqr.svg`](https://github.com/KurtBoehm/polyqr/blob/main/docs/svg-polyqr.svg))

That is a 75% reduction with identical geometry.

## 🧠 Algorithm Overview

PolyQR converts a message into merged polygons in three main stages:

1. **QR code generation**:
   - Uses [`qrcode`](https://pypi.org/project/qrcode/) to build a Boolean module matrix for the input message.
2. **Connected components and boundary extraction**:
   - Runs a 4-neighbour BFS flood fill on the module grid to find connected black regions.
   - For each module in a component, its four unit-square edges are added to a `Counter` in canonical (sorted-endpoint) form.
   - Any edge seen exactly once lies on the region’s boundary (either an outer boundary or a hole).
3. **Cycle tracing and polygon simplification**:
   - Builds an undirected adjacency graph from the remaining boundary edges.
   - For each connected component of this boundary graph, traces a single “wall-hugging” cycle:
     - At each step, the walk prefers turning over going straight, which yields visually pleasing outlines around holes when rounded corners are used.
     - If the initial cycle does not visit every vertex of the component, it is iteratively extended by following any remaining unused edges (again preferring turns) until the component is fully covered.
   - Each resulting cycle is simplified by removing collinear vertices.

The result is a small set of rectilinear polygons that exactly cover the QR modules.

## 🧪 Testing

PolyQR includes `pytest`-based tests that cover the entire code base with 100% code coverage.

Development dependencies can be installed via the `dev` extra:

```sh
pip install .[dev]
```

All tests (including coverage reporting via `pytest-cov`) can then be run from the project root:

```sh
pytest --cov
```

The TikZ tests are relatively slow, as they require `pdflatex` to compile a LaTeX document to PDF, which is then rasterized using PyMuPDF.
To keep test times reasonable, the `dev` dependencies include `pytest-xdist`, so tests can be run in parallel:

```sh
pytest --cov -n auto  # or a fixed number of workers
```

## 📜 License

This library is licensed under the Mozilla Public License 2.0, provided in [`License`](https://github.com/KurtBoehm/polyqr/blob/main/License).
