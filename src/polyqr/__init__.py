from argparse import ArgumentParser
from collections import Counter, deque
from collections.abc import Iterable
from typing import cast, final

import qrcode

# 2D integer grid point (row, column).
Point = tuple[int, int]
Edge = tuple[Point, Point]


def normalized_edge(p: Point, q: Point) -> Edge:
    """Canonical representation of an undirected edge with sorted endpoints."""
    return (p, q) if p <= q else (q, p)


def collinear(a: Point, b: Point, c: Point) -> bool:
    """Return True if three grid points are collinear, i.e. share a row or a column."""
    return (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1])


def _wrap_svg(n: int, content: str) -> str:
    """Wrap the content into a minimal SVG document with viewBox [0, n]×[0, n]."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        + f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {n} {n}">'
        + content
        + "</svg>"
    )


def connected_components(adj: dict[Point, set[Point]]) -> list[set[Point]]:
    """Return all connected components of an undirected graph."""
    unvisited: set[Point] = set(adj)
    components: list[set[Point]] = []

    while unvisited:
        start = unvisited.pop()
        component = {start}
        queue: deque[Point] = deque([start])

        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v in unvisited:
                    unvisited.remove(v)
                    component.add(v)
                    queue.append(v)

        components.append(component)

    return components


@final
class QrCodePainter:
    """
    Convert a QR code into a TikZ picture or SVG paths built from polygon outlines.

    Each connected component is merged into a set of polygons.
    """

    def __init__(self, msg: str) -> None:
        # Generate the Boolean matrix that represents the QR code.
        qr = qrcode.QRCode()
        qr.add_data(msg)
        qr.make()

        self.n = qr.modules_count
        assert all(all(isinstance(v, bool) for v in row) for row in qr.modules)
        self.modules = cast(list[list[bool]], qr.modules)

        # For each connected component: list of closed point chains (polygons)
        # that forn one composite path.
        self.point_chains: list[list[list[Point]]] = []
        self._extract_polygons()

    def _extract_polygons(self) -> None:
        """Extract simplified polygon boundaries for all connected components."""

        def neighbors(r: int, c: int) -> Iterable[Point]:
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.n:
                    yield nr, nc

        visited = [[False] * self.n for _ in range(self.n)]

        for r in range(self.n):
            for c in range(self.n):
                if not self.modules[r][c] or visited[r][c]:
                    continue

                # Flood-fill this connected component and count its square edges.
                queue: deque[Point] = deque([(r, c)])
                visited[r][c] = True
                edge_counts: Counter[Edge] = Counter()

                while queue:
                    cr, cc = queue.popleft()

                    # Count every edge of this module.
                    p00, p01 = (cr, cc), (cr, cc + 1)
                    p10, p11 = (cr + 1, cc), (cr + 1, cc + 1)
                    for p, q in ((p00, p01), (p00, p10), (p01, p11), (p10, p11)):
                        edge_counts[normalized_edge(p, q)] += 1

                    # Add unvisited neighbors to the queue and mark them as visited.
                    for nr, nc in neighbors(cr, cc):
                        if self.modules[nr][nc] and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))

                # Edges used exactly once form the boundary graph (outer and holes).
                boundary_edges = {e for e, cnt in edge_counts.items() if cnt == 1}
                assert boundary_edges

                # Build adjacency list of the boundary graph.
                adj: dict[Point, set[Point]] = {}
                for p, q in boundary_edges:
                    adj.setdefault(p, set()).add(q)
                    adj.setdefault(q, set()).add(p)

                components = connected_components(adj)
                components.sort(key=len, reverse=True)

                # Find the best cycle for each component (largest to smallest).
                chains: list[list[Point]] = []
                for component in components:
                    # Starting vertex is arbitrary → choose lexicographic minimum.
                    init = min(component)
                    edges_left = {
                        e
                        for e in boundary_edges
                        if e[0] in component or e[1] in component
                    }

                    # Construct the initial cycle with a preference for edges
                    # that are not collinear with the preceding edge (if there is one).
                    # This ensures “wall-hugging” behaviour when entering a hole,
                    # which leads to more visually pleasing results when rounding
                    # corners.
                    chain = [init]
                    prec: Point | None = None

                    while True:
                        curr = chain[-1]
                        closing = normalized_edge(curr, init)
                        if closing in edges_left:
                            edges_left.remove(closing)
                            break

                        # Available edges from curr that are still unused.
                        succs = [
                            v
                            for v in adj[curr]
                            if normalized_edge(curr, v) in edges_left
                        ]

                        if prec is not None:
                            # Prefer a turn (non-collinear) over going straight.
                            pv = prec
                            succs.sort(key=lambda sv: collinear(pv, curr, sv))
                        succ = succs[0]

                        chain.append(succ)
                        edges_left.remove(normalized_edge(curr, succ))
                        prec = curr

                    # The cycle does not cover the entire connected component.
                    # Extend the cycle by constructing a new cycle that uses
                    # edges that are not included in the cycle already, i.e. those
                    # in `edges_left`, if available (still preferring turns).
                    # If there is no such edge, use the same successor used before.
                    while len(set(chain)) < len(component):
                        new_chain = [init]
                        prec = None
                        idx = 1

                        while True:
                            curr = new_chain[-1]
                            succs = [
                                v
                                for v in adj[curr]
                                if normalized_edge(curr, v) in edges_left
                            ]
                            if not succs:
                                if idx == len(chain):
                                    break
                                # Follow previous chain when no unused edge is available.
                                succ = chain[idx]
                                idx += 1
                            else:
                                if prec is not None:
                                    pv = prec
                                    succs.sort(key=lambda sv: collinear(pv, curr, sv))
                                succ = succs[0]
                                edges_left.remove(normalized_edge(curr, succ))

                            new_chain.append(succ)
                            prec = curr

                        chain = new_chain

                    # Remove collinear vertices to simplify polygons.
                    i = 0
                    while i < len(chain):
                        p0, p1, p2 = chain[i - 1], chain[i], chain[(i + 1) % len(chain)]
                        if collinear(p0, p1, p2):
                            del chain[i]
                        else:
                            i += 1

                    chains.append(chain)

                self.point_chains.append(chains)

    def tikz(self, *, size: str, style: str) -> str:
        """Return TikZ code that draws all polygons of the QR code."""
        lines = [
            f"\\begin{{tikzpicture}}[x={size},y={size},"
            + f"qrpoly/.style={{fill=black, draw=none, even odd rule, {style}}}]",
        ]

        for chains in self.point_chains:
            # Each chain becomes a closed path.
            chain_str = " ".join(
                " -- ".join(f"({c}, {-r})" for r, c in chain) + " -- cycle"
                for chain in chains
            )
            lines.append(f"  \\draw[qrpoly] {chain_str};")

        lines.append("\\end{tikzpicture}%")
        return "\n".join(lines)

    def _generate_svg_polygons(self, *, relative: bool) -> Iterable[str]:
        """
        Yield one SVG path-data string per polygon group.

        When `relative=True`, successive groups may use relative `m` moves
        from the end of the previous group.
        """

        def move(p: Point | None, q: Point) -> str:
            ax, ay = q
            abs_cmd = f"M{ax} {ay}"
            if p is None:
                return abs_cmd
            rel_cmd = f"m{ax - p[0]} {ay - p[1]}"
            return abs_cmd if len(abs_cmd) <= len(rel_cmd) else rel_cmd

        def line(axis: str, src: int, dst: int) -> str:
            abs_arg, rel_arg = str(dst), str(dst - src)
            abs_cmd, rel_cmd = axis.upper() + abs_arg, axis + rel_arg
            return abs_cmd if len(abs_arg) <= len(rel_arg) else rel_cmd

        prev: Point | None = None
        for chains in self.point_chains:
            parts: list[str] = []
            for chain in chains:
                # Each chain becomes a closed path.
                p0 = chain[0]
                parts.append(move(prev, p0))
                x, y = p0

                for nx, ny in chain[1:]:
                    dx, dy = nx - x, ny - y
                    assert dx == 0 or dy == 0, f"{dx} {dy}"
                    parts.append(line("h", x, nx) if dy == 0 else line("v", y, ny))
                    x, y = nx, ny

                parts.append("z")
                if relative:
                    prev = p0

            yield "".join(parts)

    @property
    def svg_paths(self) -> Iterable[str]:
        """Yield one SVG <path> element per polygon group."""
        for poly in self._generate_svg_polygons(relative=False):
            yield f'<path fill-rule="evenodd" d="{poly}"/>'

    @property
    def svg_path(self) -> str:
        """Return a single SVG <path> element containing all polygons."""
        path = "".join(self._generate_svg_polygons(relative=True))
        return f'<path fill-rule="evenodd" d="{path}"/>'

    @property
    def svg(self) -> str:
        """Return a complete SVG document containing the merged path."""
        return _wrap_svg(self.n, self.svg_path)


def run_tikz() -> None:
    """CLI entry point that prints TikZ code for a QR code."""
    parser = ArgumentParser()
    parser.add_argument("size", help="Edge length of one QR code module")
    parser.add_argument("style", help="TikZ style options applied to each polygon")
    parser.add_argument("msg", help="Message to encode as a QR code")
    args = parser.parse_args()
    print(QrCodePainter(args.msg).tikz(size=args.size, style=args.style))
