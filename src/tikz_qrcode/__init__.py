from argparse import ArgumentParser
from collections import Counter, deque
from collections.abc import Iterable
from typing import cast, final

import qrcode

# A 2D grid point at integer coordinates (row, column).
Point = tuple[int, int]
Edge = tuple[Point, Point]


def normalized_edge(p: Point, q: Point) -> Edge:
    """Canonical representation of an undirected edge with sorted vertices."""
    return (p, q) if p <= q else (q, p)


def collinear(a: Point, b: Point, c: Point) -> bool:
    """Whether three grid points are collinear, i.e. share the same row or column."""
    return (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1])


def _wrap_svg(n: int, content: str):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        + f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {n} {n}">'
        + content
        + "</svg>"
    )


@final
class QrCodePainter:
    """
    Convert a QR code into a TikZ picture made of polygon outlines.
    Contiguous black areas are merged into polygons.
    """

    def __init__(self, msg: str) -> None:
        # Generate the Boolean matrix that represents the QR code.
        qr = qrcode.QRCode()
        qr.add_data(msg)
        qr.make()

        self.n = qr.modules_count
        assert all(all(isinstance(v, bool) for v in row) for row in qr.modules)
        self.modules = cast(list[list[bool]], qr.modules)

        # each list-of-list contained herein is a list of point chains
        # that need to be drawn as one composite path using the even-odd rule
        self.point_chains: list[list[list[Point]]] = []
        self._extract_polygons()

    def _extract_polygons(self) -> None:
        """Identify connected module components and construct simplified boundaries."""

        def neighbors(r: int, c: int) -> Iterable[tuple[int, int]]:
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.n:
                    yield nr, nc

        visited = [[False] * self.n for _ in range(self.n)]

        for r in range(self.n):
            for c in range(self.n):
                if not self.modules[r][c] or visited[r][c]:
                    continue

                # Flood-fill to collect all modules in this component.
                queue: deque[Point] = deque([(r, c)])
                visited[r][c] = True
                edge_counts: Counter[Edge] = Counter()

                while queue:
                    cr, cc = queue.popleft()

                    # Count each outer edge of the module.
                    p00, p01 = (cr, cc), (cr, cc + 1)
                    p10, p11 = (cr + 1, cc), (cr + 1, cc + 1)
                    for p, q in ((p00, p01), (p00, p10), (p01, p11), (p10, p11)):
                        edge_counts[normalized_edge(p, q)] += 1

                    # Add unvisited neighbors to the queue and mark them as visited.
                    for nr, nc in neighbors(cr, cc):
                        if self.modules[nr][nc] and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))

                # Edges used exactly once form the outer boundary (including holes).
                boundary_edges = {e for e, cnt in edge_counts.items() if cnt == 1}
                assert boundary_edges

                # Build the unordered adjacency list for the boundary graph.
                adj: dict[Point, set[Point]] = {}
                for p, q in boundary_edges:
                    adj.setdefault(p, set()).add(q)
                    adj.setdefault(q, set()).add(p)

                edges_left = set(boundary_edges)
                chains: list[list[Point]] = []

                # Find and simplify cycles.
                while edges_left:
                    start, _ = next(iter(edges_left))
                    prev: Point | None = None
                    cur = start
                    chain = [cur]

                    # Find the cycle.
                    while True:
                        found = False
                        for v in adj[cur]:
                            e = normalized_edge(cur, v)
                            if e in edges_left and v != prev:
                                edges_left.remove(e)
                                prev, cur = cur, v
                                found = True
                                break
                        assert found
                        if cur == start:
                            # Cycle closed.
                            break
                        chain.append(cur)

                    # Simplify the cycle by removing collinear vertices.
                    i = 0
                    while i < len(chain):
                        p0, p1, p2 = chain[i - 1], chain[i], chain[(i + 1) % len(chain)]
                        if collinear(p0, p1, p2):
                            del chain[i]
                        else:
                            i += 1

                    chains.append(chain)

                self.point_chains.append(chains)

    def latex(self, size: str, style: str) -> str:
        """Produce TikZ code that draws the collected polygons."""
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
        def move(p: Point | None, q: Point):
            sq = f"M{q[0]} {q[1]}"
            if p is None:
                return sq
            return min(sq, f"m{q[0] - p[0]} {q[1] - p[1]}", key=len)

        def line(lower: str, src: int, dst: int) -> str:
            sa, sd = str(dst), str(dst - src)
            return lower.upper() + sa if len(sa) <= len(sd) else lower + sd

        prev: Point | None = None
        for chains in self.point_chains:
            s = ""
            for chain in chains:
                # Each chain becomes a closed path.
                p0 = chain[0]
                s += move(prev, chain[0])
                xp, yp = p0
                for x, y in chain[1:]:
                    dx, dy = x - xp, y - yp
                    assert dx == 0 or dy == 0, f"{dx} {dy}"
                    s += line("h", xp, x) if dy == 0 else line("v", yp, y)
                    xp, yp = x, y
                s += "z"
                if relative:
                    prev = p0
            yield s

    @property
    def svg_paths(self) -> Iterable[str]:
        for poly in self._generate_svg_polygons(relative=False):
            yield '<path fill-rule="evenodd" d="' + poly + '"/>'

    @property
    def svg_path(self) -> str:
        path = "".join(self._generate_svg_polygons(relative=True))
        return '<path fill-rule="evenodd" d="' + path + '"/>'

    def as_svg(self, use_paths: bool = False) -> str:
        return _wrap_svg(
            self.n, "".join(self.svg_paths) if use_paths else self.svg_path
        )

    @property
    def svg(self) -> str:
        return self.as_svg()


def run() -> None:
    parser = ArgumentParser()
    parser.add_argument("size", help="Edge length of one QR code square")
    parser.add_argument("style", help="TikZ style options for each polygon")
    parser.add_argument("msg", help="Message to encode")
    args = parser.parse_args()
    print(QrCodePainter(args.msg).latex(args.size, args.style))
