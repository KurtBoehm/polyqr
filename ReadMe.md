# 🧩 PolyQR: QR Codes as Polygons

PolyQR is a small library that turns a message into a QR code where each contiguous black region is drawn as **one merged polygon**, not a grid of tiny squares.
This eliminates the **hideous hairline gaps** between modules that appear with naïve approaches (an example is shown later) and also minimizes the number of points per polygon to keep the output compact.

PolyQR can generate:

- **TikZ** code with full styling support (e.g. rounded corners)
- **SVG** paths that are fully minimized to save space

The [`tests`](https://github.com/KurtBoehm/polyqr/blob/main/tests) directory contains **`pytest`-based tests** for both TikZ and SVG.

## 🖼️ TikZ Output

PolyQR provides the command-line tool `polyqr_tikz`, which can be called like this:

```sh
polyqr_tikz "1mm" "rounded corners=0.25mm" "https://github.com/KurtBoehm/polyqr"
```

This prints a `tikzpicture` environment of the following form to `stdout`:

```latex
\begin{tikzpicture}[x=1mm, y=1mm, qrpoly/.style={fill=black, draw=none, even odd rule, rounded corners=0.25mm}]
  % \draw commands to draw a QR code representing https://github.com/KurtBoehm/polyqr
\end{tikzpicture}
```

Because each connected component is rendered as a single polygon, TikZ styles such as `rounded corners` apply only to the outer boundary of each contiguous region.
This also eliminates visible gaps between modules, which you can see when comparing to a basic version that draws each module as a separate rectangle:

| Basic                                                                                      | PolyQR                                                                                       | PolyQR with rounded corners                                                                                  |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| ![Basic TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-basic.png) | ![PolyQR TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-polyqr.png) | ![Rounded PolyQR TikZ](https://raw.githubusercontent.com/KurtBoehm/polyqr/main/docs/tikz-polyqr-rounded.png) |

The LaTeX file used to generate these examples is at [`docs/tikz.tex`](https://github.com/KurtBoehm/polyqr/blob/main/docs/tikz.tex).

You can also generate TikZ code directly from Python:

```python
from polyqr import QrCodePainter

painter = QrCodePainter("https://github.com/KurtBoehm/polyqr")

print(painter.tikz(size="1mm", style="rounded corners=0.25mm"))
```

## 🖼️ SVG Output

PolyQR can also generate **highly minimized SVG paths**:

- Either the entire QR code or each contiguous area becomes a single `<path>` element using `fill-rule="evenodd"` to handle holes.
- All segments are axis-aligned and therefore encoded using only `M`, `H`, `V`, and `Z` commands.
- For every move/line, **absolute vs. relative** commands are chosen based on which textual form is shorter.

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
`SvgPathImage` avoids gaps by collecting all modules into a single `<path>`, but its output is much larger.

For the message `https://github.com/KurtBoehm/polyqr`:

- `SvgPathImage` output: ≈ **6.4 kB** ([`docs/svg-qrcode.svg`](https://github.com/KurtBoehm/polyqr/blob/main/docs/svg-qrcode.svg))
- `QrCodePainter.svg` output: ≈ **1.7 kB** ([`docs/svg-polyqr.svg`](https://github.com/KurtBoehm/polyqr/blob/main/docs/svg-polyqr.svg))

That is a **size reduction of more than 70%** with identical geometry.

## 🧠 Algorithm Overview

PolyQR converts a message into merged polygons in three main stages:

1. **QR code generation**:
   - Uses [`qrcode`](https://pypi.org/project/qrcode/) to build a **Boolean module matrix** for the input message.
2. **Connected components and boundary extraction**:
   - Runs a **4-neighbour BFS flood fill** on the module grid to find connected black regions.
   - For each module in a component, its four unit-square edges are added to a `Counter` in canonical (sorted-endpoint) form.
   - Any edge seen **exactly once** lies on the region’s boundary (outer boundary or hole); interior edges shared by two modules cancel out.
3. **Cycle tracing and polygon simplification**:
   - Builds an undirected adjacency graph from the remaining boundary edges.
   - For each connected component of this boundary graph, traces a **single “wall-hugging” cycle**:
     - At each step, the walk prefers **non-collinear turns** over going straight, producing visually pleasing outlines around holes when rounded corners are used.
     - If the initial cycle does not visit every vertex of the component, it is **iteratively extended** by following any remaining unused edges (again preferring turns) until the component is fully covered.
   - Each resulting cycle is simplified by **removing collinear vertices**.

The result is a small set of rectilinear polygons that exactly cover the QR modules.

## 🧪 Testing

PolyQR includes **pytest-based tests** for TikZ and SVG output, covering QR code generation, polygon extraction and simplification, and output formatting.
The development dependencies can be installed via the `dev` optional group:

```sh
pip3 install .[dev]
```

All tests can then be run from the project root:

```sh
pytest
```

The TikZ tests are relatively slow, as they require `pdflatex` to compile a LaTeX document to PDF, which is then rasterized via PyMuPDF.
To keep test times reasonable, the `dev` dependencies include `pytest-xdist`, so tests can be executed in parallel:

```sh
pytest -n 8  # or any other number of workers
```
