# This file is part of https://github.com/KurtBoehm/svg_path_editor.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import io
from typing import Callable

import cairosvg
import numpy as np
import pytest
import qrcode
from PIL import Image

from polyqr import QrCodePainter

from .defs import test_messages


def _svg_to_mask(svg_bytes: str, n: int):
    png_bytes = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=n,
        output_height=n,
        background_color="black",
        negate_colors=True,
    )
    assert isinstance(png_bytes, bytes)
    return np.array(Image.open(io.BytesIO(png_bytes)).convert("1"), dtype=np.bool_)


def _test_svg(msg: str, make_svg: Callable[[QrCodePainter], str]) -> None:
    """
    Test that the SVG document produced by ``make_svg``, when rasterized
    using `cairosvg`, is equivalent to the output of :class:`qrcode.QRCode`.
    """
    # Reference matrix (True = black)
    qr = qrcode.QRCode()
    qr.add_data(msg)
    qr.make()
    ref_matrix = np.array(qr.modules, dtype=bool)

    # Generate and render the SVG document for the same message.
    painter = QrCodePainter(msg)
    raster = _svg_to_mask(make_svg(painter), painter.n)

    assert np.array_equal(raster, ref_matrix), (
        f"Rendered QR code differs from reference for message: {msg!r}\n"
        f"Reference matrix (True=black):\n{ref_matrix}\n"
        f"Rendered matrix (True=black):\n{raster}"
    )


@pytest.mark.parametrize("msg", test_messages)
def test_qrcode_svg(msg: str) -> None:
    """
    Test that the SVG document produced by :meth:`QrCodePainter.svg`, when rasterized
    using `cairosvg`, is equivalent to the output of :class:`qrcode.QRCode`.
    """
    _test_svg(msg, lambda painter: painter.svg)


@pytest.mark.parametrize("msg", test_messages)
def test_qrcode_svg_paths(msg: str) -> None:
    """
    Test that the SVG document produced by wrapping :meth:`QrCodePainter.svg_paths`,
    when rasterized using `cairosvg`, is equivalent to the output of
    :class:`qrcode.QRCode`.
    """

    def make_svg(painter: QrCodePainter):
        n = painter.n
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            + f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {n} {n}">'
            + "".join(painter.svg_paths)
            + "</svg>"
        )

    _test_svg(msg, make_svg)
