import io

import cairosvg
import numpy as np
import pytest
import qrcode
from PIL import Image

from tikz_qrcode import QrCodePainter

from .defs import test_messages


def svg_to_mask(svg_bytes: str, n: int):
    png_bytes = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=n,
        output_height=n,
        background_color="black",
        negate_colors=True,
    )
    assert isinstance(png_bytes, bytes)
    return np.array(Image.open(io.BytesIO(png_bytes)).convert("1"), dtype=np.bool_).T


@pytest.mark.parametrize("msg", test_messages)
def test_rendered_tikz(msg: str) -> None:
    """
    Test that the code produced by :meth:`QrCodePainter.tikz`, when rendered using
    pdfLaTeX and rasterized PyMuPDF, is equivalent to the output of
    :class:`qrcode.QRCode`.

    This test requires a working LaTeX installation with pdflatex and TikZ.
    """

    # Reference matrix (True = black)
    qr = qrcode.QRCode()
    qr.add_data(msg)
    qr.make()
    ref_matrix = np.array(qr.modules, dtype=bool)

    # Produce TikZ for the same message with an arbitrary module size.
    painter = QrCodePainter(msg)
    raster = svg_to_mask(painter.svg, painter.n)

    assert np.array_equal(raster, ref_matrix), (
        f"Rendered QR code differs from reference for message: {msg!r}\n"
        f"Reference matrix (True=black):\n{ref_matrix}\n"
        f"Rendered matrix (True=black):\n{raster}"
    )
