# 🧩 PolyQR: QR Codes as Polygons

PolyQR is a small library that turns a message into a QR code where each contiguous black region is drawn as **one merged polygon** instead of separate squares, eliminating tiny gaps between modules.
PolyQR also **minimizes the number of points** needed to represent each polygon to keep the output compact.

PolyQR can generate both **TikZ** code, which supports rich styling such as rounded corners, and **SVG** paths, which are fully minimized to save space.
Both variants use the **even-odd fill rule** to support holes in connected components.

Lastly, [`tests`](tests) provides **`pytest`-based tests** for both TikZ and SVG output.

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

Since the connected components are merged into a single polygon, effects such as `rounded corners` only apply to the outer boundary of each contiguous area.

The same behaviour can also be achieved programmatically:

```python
from polyqr import QrCodePainter

painter = QrCodePainter("https://github.com/KurtBoehm/polyqr")

print(painter.tikz(size="1mm", style="rounded corners=0.25mm"))
```

## 🖼️ SVG Output

In addition to TikZ, PolyQR can also generate **minimized SVG paths**:

- Either each contiguous area or the full QR code becomes a single `<path>` element using `fill-rule="evenodd"` to handle holes correctly.
- Apart from `M` and `Z`, all commands are `H` and `V` (since QR code outlines are axis-aligned), keeping the path syntax short.
- For each segment, absolute or relative `M`/`H`/`V` commands are chosen depending on which textual representation is shorter, yielding a fully minimized path string.

PolyQR only provides programmatic access to SVG path generation.
In addition to being able to generate a full SVG document, PolyQR can also produce a single `<path>` element for the whole QR code or a generator over `<path>` elements, one per connected component:

```python
from polyqr import QrCodePainter

painter = QrCodePainter("https://github.com/KurtBoehm/polyqr")

# Full SVG document as a string
svg_doc = painter.svg

# Get the <path> element for the path representing the full QR code
svg_path = painter.svg_path

# Iterate over individual <path> elements for each component area
for path in painter.svg_paths:
    print(path)
```

## 🧠 Algorithm Overview

PolyQR uses the following steps to convert a message into merged polygons for each contiguous area:

1. **QR code generation**:
   - The [`qrcode`](https://pypi.org/project/qrcode/) library is used to generate the Boolean module matrix for the given message.
2. **Connected components and boundary extraction**:
   - **Connected-component labelling** is performed with a **4-neighbour breadth-first search (BFS) flood fill** over the module grid.
   - For each module in a component, its four unit square edges are added to a `Counter` in a canonical (sorted endpoint) form.
   - Any edge seen **exactly once** lies on the component’s boundary (outer boundary or a hole), while interior edges shared by two cells cancel out.
3. **Cycle tracing and polygon simplification**:
   - From the remaining boundary edges, an undirected adjacency graph is constructed.
   - Cycles (closed rings) are traced by walking this graph; each cycle corresponds to one polygon ring (outer boundary or hole).
   - The cycles are simplified by removing vertices that are **collinear** with their neighbours.

The result is a small set of rectilinear polygons that exactly cover the black QR modules.

## 🧪 Testing

PolyQR includes **pytest-based tests** for TikZ and SVG output, covering QR code generation, polygon extraction and simplification, and formatting.
The test dependencies are specified as the `optional-dependencies` group named `dev`, which can be installed with:

```sh
pip3 install .[dev]
```

All tests can then be run with (with the project root as the working directory):

```sh
pytest
```

The TikZ tests are relatively slow, as they require `pdflatex` to compile a LaTeX document to PDF, which is then rasterized via PyMuPDF.
To reduce runtime, the `dev` dependencies include `pytest-xdist` so tests can be executed in parallel:

```sh
pytest -n 8  # or any other number of processes
```
