from argparse import ArgumentParser
from collections import deque
from dataclasses import dataclass
from typing import final

import qrcode
from pydantic import BaseModel, TypeAdapter

Point = tuple[int, int]


@dataclass(frozen=True)
class Edge:
    p1: Point
    p2: Point
    rect: Point


def sign(x: int) -> int:
    if x < 0:
        return -1
    if x > 0:
        return 1
    return 0


@final
class QrCodePainter:
    def __init__(self, msg: str):
        qr = qrcode.QRCode()
        qr.add_data(msg)
        qr.make()

        self.square_num = qr.modules_count
        self.squares = TypeAdapter(list[list[bool]]).validate_python(qr.modules)
        self.indexed_squares = [[0 for _ in row] for row in self.squares]
        self.ranges: list[list[Point]] = []
        self.point_chains: list[list[list[Point]]] = []

        for i in range(len(self.squares)):
            for j in range(len(self.squares[i])):
                if not self.squares[i][j] or self.indexed_squares[i][j] != 0:
                    continue

                index = len(self.ranges) + 1
                tuples: list[Point] = []
                queue: deque[Point] = deque([(i, j)])
                inner_edges: list[Edge] = []
                while len(queue) > 0:
                    row, col = queue.popleft()
                    if (
                        not self.squares[row][col]
                        or self.indexed_squares[row][col] != 0
                    ):
                        continue

                    self.indexed_squares[row][col] = index
                    tuples.append((row, col))
                    neighbours: list[Point] = []
                    for k, l in (
                        (row - 1, col),
                        (row, col - 1),
                        (row, col + 1),
                        (row + 1, col),
                    ):
                        inside = k in range(self.square_num) and l in range(
                            self.square_num
                        )
                        if inside:
                            neighbours.append((k, l))
                        if not inside or not self.squares[k][l]:
                            if k == row - 1:
                                inner_edges.append(
                                    Edge((row, col), (row, col + 1), (row, col))
                                )
                            if l == col - 1:
                                inner_edges.append(
                                    Edge((row, col), (row + 1, col), (row, col))
                                )
                            if l == col + 1:
                                inner_edges.append(
                                    Edge((row, col + 1), (row + 1, col + 1), (row, col))
                                )
                            if k == row + 1:
                                inner_edges.append(
                                    Edge((row + 1, col), (row + 1, col + 1), (row, col))
                                )
                    queue.extend(neighbours)

                inner_point_chains: list[list[Point]] = []
                while len(inner_edges) > 0:
                    edge = inner_edges.pop(0)
                    chain: list[Point] = [edge.p1, edge.p2]
                    # print(f"{edge=}")
                    while True:
                        end = chain[-1]
                        found = False
                        cycled = False
                        for k in range(len(inner_edges)):
                            e = inner_edges[k]
                            if (
                                abs(edge.rect[0] - e.rect[0])
                                + abs(edge.rect[1] - e.rect[1])
                                > 1
                            ):
                                continue

                            if e.p1 == end:
                                new_end = e.p2
                            elif e.p2 == end:
                                new_end = e.p1
                            else:
                                continue
                            inner_edges.pop(k)
                            found = True

                            if new_end == chain[0]:
                                cycled = True
                                break

                            chain.append(new_end)
                            edge = e
                            # print(f"{edge=}, {chain[-1]}")
                            break

                        if cycled:
                            break
                        if found:
                            continue

                        # If there is no adjacent edge: choose a non-adjacent one
                        # print(f"{inner_edges=}")
                        for k in range(len(inner_edges)):
                            e = inner_edges[k]

                            if e.p1 == end:
                                new_end = e.p2
                            elif e.p2 == end:
                                new_end = e.p1
                            else:
                                continue
                            inner_edges.pop(k)
                            found = True

                            if new_end == chain[0]:
                                cycled = True
                                break

                            chain.append(new_end)
                            edge = e
                            # print(f"{edge=}, {chain[-1]}")
                            break

                        if cycled:
                            break

                    k = 0
                    while k < len(chain):
                        p1, p2, p3 = chain[k - 1], chain[k], chain[(k + 1) % len(chain)]
                        if all(
                            sign(p3[l] - p2[l]) == sign(p2[l] - p1[l]) for l in (0, 1)
                        ):
                            chain.pop(k)
                        else:
                            k += 1
                    inner_point_chains.append(chain)

                # if len(inner_edge_chains) > 1:
                # print("inner_edge_chains:")
                # print("\n".join(str(c) for c in inner_point_chains))
                self.point_chains.append(inner_point_chains)

                self.ranges.append(tuples)

    def latex(self, size: str, style: str) -> str:
        lines = [
            f"\\begin{{tikzpicture}}[x={size},y={size},qrsquare/.style={{fill=black, draw=none, even odd rule, {style}}}]",
            f"  \\clip (-4, 4) rectangle ({self.square_num + 4}, -{self.square_num + 4});",
        ]
        for chains in self.point_chains:
            cstr = " ".join(
                " -- ".join(f"({p[1]}, {-p[0]})" for p in chain) + " -- cycle"
                for chain in chains
            )
            lines.append(f"  \\draw[qrsquare] {cstr};")
        lines += ["\\end{tikzpicture}%"]
        return "\n".join(lines)


class Args(BaseModel):
    size: str
    style: str
    msg: str


def run():
    parser = ArgumentParser()
    parser.add_argument("size")
    parser.add_argument("style")
    parser.add_argument("msg")
    args = Args.model_validate(vars(parser.parse_args()))
    print(QrCodePainter(args.msg).latex(args.size, args.style))
