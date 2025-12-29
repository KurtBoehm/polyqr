import io

import cairosvg
import numpy as np
import pytest
import qrcode
from PIL import Image

from polyqr import QrCodePainter

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
def test_rendered_svg(msg: str) -> None:
    """
    Test that the SVG document produced by :meth:`QrCodePainter.svg`, when rasterized
    using `cairosvg`, is equivalent to the output of :class:`qrcode.QRCode`.
    """

    # Reference matrix (True = black)
    qr = qrcode.QRCode()
    qr.add_data(msg)
    qr.make()
    ref_matrix = np.array(qr.modules, dtype=bool)

    # Produce the SVG document for the same message.
    painter = QrCodePainter(msg)
    raster = svg_to_mask(painter.svg, painter.n)

    assert np.array_equal(raster, ref_matrix), (
        f"Rendered QR code differs from reference for message: {msg!r}\n"
        f"Reference matrix (True=black):\n{ref_matrix}\n"
        f"Rendered matrix (True=black):\n{raster}"
    )
