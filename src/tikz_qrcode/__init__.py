from argparse import ArgumentParser
from collections import deque
from dataclasses import dataclass
from typing import final

import qrcode
from pydantic import BaseModel, TypeAdapter

# A QR code square is identified by its (row, column) coordinates.
Point = tuple[int, int]


@dataclass(frozen=True)
class Edge:
    """Undirected edge of a polygon that surrounds a black region."""

    p1: Point
    p2: Point
    # the QR code square the edge belongs to
    square: Point


def manhattan_distance(e0: Edge, e1: Edge) -> int:
    """Manhattan distance between the squares of two edges."""
    return abs(e0.square[0] - e1.square[0]) + abs(e0.square[1] - e1.square[1])


def sign(x: int) -> int:
    """-1, 0 or +1 depending on the sign of `x`."""
    if x < 0:
        return -1
    if x > 0:
        return 1
    return 0


def collinear(p1: Point, p2: Point, p3: Point) -> bool:
    """True if and only if p1→p2 and p2→p3 are collinear."""
    return all(sign(p3[i] - p2[i]) == sign(p2[i] - p1[i]) for i in (0, 1))


@final
class QrCodePainter:
    """
    Convert a QR code into a TikZ picture made of polygon outlines.
    Contiguous black squares are merged into a single polygon.
    """

    def __init__(self, msg: str):
        # Generate the boolean matrix that represents the QR code.
        qr = qrcode.QRCode()
        qr.add_data(msg)
        qr.make()

        self.square_num = qr.modules_count
        self.squares = TypeAdapter(list[list[bool]]).validate_python(qr.modules)

        # 0: not visited. >0: component index.
        self.indexed_squares = [[0 for _ in row] for row in self.squares]

        # Store a list of its outer point chains (forming a polygon) for each component.
        self.point_chains: list[list[list[Point]]] = []

        # Flood-fill each black region and collect its border edges.
        index: int = 1
        for i in range(len(self.squares)):
            for j in range(len(self.squares[i])):
                # Skip white and previously visited black squares
                if not self.squares[i][j] or self.indexed_squares[i][j] != 0:
                    continue

                # BFS queue for the current component
                queue: deque[Point] = deque([(i, j)])
                # Edges for the current component
                inner_edges: list[Edge] = []
                while queue:
                    row, col = queue.popleft()
                    if (
                        not self.squares[row][col]
                        or self.indexed_squares[row][col] != 0
                    ):
                        continue

                    # Mark the square as belonging to the current component
                    self.indexed_squares[row][col] = index

                    # Examine the four orthogonal neighbours.
                    for k, l in (
                        (row - 1, col),
                        (row, col - 1),
                        (row, col + 1),
                        (row + 1, col),
                    ):
                        inside = 0 <= k < self.square_num and 0 <= l < self.square_num
                        if inside:
                            queue.append((k, l))

                        # Neighbour outside the matrix or white → this side is a border.
                        if not inside or not self.squares[k][l]:
                            # top
                            if k == row - 1:
                                inner_edges.append(
                                    Edge((row, col), (row, col + 1), (row, col))
                                )
                            # left
                            if l == col - 1:
                                inner_edges.append(
                                    Edge((row, col), (row + 1, col), (row, col))
                                )
                            # right
                            if l == col + 1:
                                inner_edges.append(
                                    Edge((row, col + 1), (row + 1, col + 1), (row, col))
                                )
                            # bottom
                            if k == row + 1:
                                inner_edges.append(
                                    Edge((row + 1, col), (row + 1, col + 1), (row, col))
                                )

                # Stitch border edges into closed chains (polygons).
                inner_point_chains: list[list[Point]] = []
                while inner_edges:
                    # Start a new chain with any remaining edge
                    edge = inner_edges.pop(0)
                    chain: list[Point] = [edge.p1, edge.p2]

                    while True:
                        # current chain endpoint
                        end = chain[-1]
                        found = False
                        cycled = False

                        # Prefer an edge to a neighbouring square.
                        for k in range(len(inner_edges)):
                            e = inner_edges[k]
                            # Squares must be neighbours (Manhattan distance ≤ 1)
                            if manhattan_distance(edge, e) > 1:
                                continue

                            # `e` must share a vertex with the chain end
                            new_end = (
                                e.p2 if e.p1 == end else e.p1 if e.p2 == end else None
                            )
                            if new_end is None:
                                continue

                            inner_edges.pop(k)
                            found = True

                            if new_end == chain[0]:
                                # closed loop
                                cycled = True
                            else:
                                chain.append(new_end)
                                edge = e
                            break

                        if cycled:
                            break
                        if found:
                            continue

                        # No neighbour found: Fall back to any touching edge
                        for k in range(len(inner_edges)):
                            e = inner_edges[k]

                            new_end = (
                                e.p2 if e.p1 == end else e.p1 if e.p2 == end else None
                            )
                            if new_end is None:
                                continue

                            inner_edges.pop(k)
                            found = True

                            if new_end == chain[0]:
                                cycled = True
                                break

                            chain.append(new_end)
                            edge = e
                            break

                        assert found
                        if cycled:
                            break

                    # Remove collinear points.
                    k = 0
                    while k < len(chain):
                        p0, p1, p2 = chain[k - 1], chain[k], chain[(k + 1) % len(chain)]
                        if collinear(p0, p1, p2):
                            chain.pop(k)
                        else:
                            k += 1

                    inner_point_chains.append(chain)

                # Store the polygon for this component
                self.point_chains.append(inner_point_chains)
                index += 1

    def latex(self, size: str, style: str) -> str:
        """Produce TikZ code that draws the collected polygons."""
        lines = [
            f"\\begin{{tikzpicture}}[x={size},y={size},"
            + f"qrpoly/.style={{fill=black, draw=none, even odd rule, {style}}}]",
        ]

        for chains in self.point_chains:
            # Each chain becomes a closed path
            # TikZ uses (x, y) where x = column, y = -row.
            chain_str = " ".join(
                " -- ".join(f"({c}, {-r})" for r, c in chain) + " -- cycle"
                for chain in chains
            )
            lines.append(f"  \\draw[qrpoly] {chain_str};")

        lines.append("\\end{tikzpicture}%")
        return "\n".join(lines)


class Args(BaseModel):
    size: str
    style: str
    msg: str


def run() -> None:
    parser = ArgumentParser()
    parser.add_argument("size", help="Edge length of one QR code square")
    parser.add_argument("style", help="TikZ style options for each polygon")
    parser.add_argument("msg", help="Message to encode")
    args = Args.model_validate(vars(parser.parse_args()))
    print(QrCodePainter(args.msg).latex(args.size, args.style))
