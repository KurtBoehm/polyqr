# This file is part of https://github.com/KurtBoehm/svg_path_editor.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from io import BytesIO
from pathlib import Path
from shutil import which
from subprocess import run
from tempfile import TemporaryDirectory
from typing import cast

import fitz
import qrcode
from qrcode.image.svg import SvgImage, SvgPathImage

from polyqr import QrCodePainter

msg = "https://github.com/KurtBoehm/polyqr"

base_path = Path(__file__).parent
tikz_path = base_path / "tikz.tex"

# Create a LaTeX file with three TikZ pictures representing
# https://github.com/KurtBoehm/polyqr as a QR code: A PolyQR version, a PolyQR version
# with rounded corners, and a basic one that draws each module as a separate rectangle.
with open(tikz_path, "w") as f:
    print(r"\documentclass[tikz]{standalone}", file=f)
    print(file=f)
    print(r"\usepackage{tikz}", file=f)
    print(file=f)
    print(r"\begin{document}", file=f)

    # Add a PolyQR version
    painter = QrCodePainter(msg)
    print(painter.tikz(size="1mm", style=""), file=f)

    # Add a PolyQR version with rounded corners
    painter = QrCodePainter(msg)
    print(painter.tikz(size="1mm", style="rounded corners=0.25mm"), file=f)

    # Add a basic version that converts the output of `qrcode.svg.SvgImage`,
    # which generates an SVG `rect` element for each module, into the equivalent
    # TikZ code with one rectangle per module.
    qr = qrcode.QRCode()
    qr.add_data(msg)
    qr.make()
    img = qr.make_image(image_factory=SvgImage)
    io = BytesIO()
    img.save(io)
    svg = io.getvalue().decode()
    regex = re.compile(
        r'<svg:rect x="(\d+)mm" y="(\d+)mm" width="(\d+)mm" height="(\d+)mm" />'
    )

    print(r"\begin{tikzpicture}[x=1mm, y=-1mm]", file=f)
    for m in regex.findall(svg):
        x, y, w, h = cast(tuple[str, str, str, str], m)
        print(f"  \\fill ({x}, {y}) rectangle ++ ({w}, {h});", file=f)
    print(r"\end{tikzpicture}", file=f)
    print(r"\end{document}", file=f)

# Compile the generated LaTeX code, rasterize each page at a 640×640 pixel resolution,
# and optimize the resulting PNG files if `oxipng` is available.
with TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    run(["pdflatex", "-output-directory", tmp, tikz_path])

    target_width = 640
    names = ["polyqr", "polyqr-rounded", "basic"]

    with fitz.Document(tmp / "tikz.pdf") as doc:
        for i in range(len(doc)):
            page = doc[i]
            rect = cast(fitz.Rect, page.rect)

            # `rect.width` is in points (1/72 inch). We want `target_width` in pixels.
            zoom = target_width / rect.width
            matrix = fitz.Matrix(zoom, zoom)

            # Render the page at given zoom.
            pix = page.get_pixmap(matrix=matrix, alpha=True)
            pix_path = base_path / f"tikz-{names[i]}.png"
            pix.save(pix_path)
            if which("oxipng") is not None:
                run(["oxipng", "-o6", "--strip", "all", pix_path], check=True)

# Create an SVG version of the QR code using `qrcode.svg.SvgPathImage`.
with open(base_path / "svg-qrcode.svg", "wb") as f:
    qr = qrcode.QRCode(border=0)
    qr.add_data(msg)
    qr.make()
    img = qr.make_image(image_factory=SvgPathImage)
    img.save(f)

# Create an SVG version of the QR code using PolyQR.
with open(base_path / "svg-polyqr.svg", "w") as f:
    painter = QrCodePainter(msg)
    print(painter.svg, file=f)
