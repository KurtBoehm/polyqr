import subprocess
from pathlib import Path

import fitz
import numpy as np
import pytest
import qrcode

from polyqr import QrCodePainter

from .defs import test_messages

# Minimal LaTeX wrapper used to compile the TikZ snippet into a PDF.
_LATEX_TEMPLATE = """
\\documentclass[tikz]{{standalone}}
\\usepackage{{tikz}}
\\begin{{document}}
{body}
\\end{{document}}
"""


# The test strings where partially generated using GPT-5
@pytest.mark.parametrize("msg", test_messages)
def test_rendered_tikz(msg: str, tmp_path: Path) -> None:
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
    tikz = painter.tikz(size="1pt", style="")

    # Write the full LaTeX document and compile it to a single-page PDF.
    tex_path = tmp_path / "qr_test.tex"
    tex_path.write_text(_LATEX_TEMPLATE.format(body=tikz))

    # Run pdflatex in nonstop mode, stop on errors, and write outputs next to the .tex.
    subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            tex_path.parent,
            tex_path,
        ],
        check=True,
    )
    pdf_path = tex_path.with_suffix(".pdf")

    # Render the PDF page to a grayscale image with a scale chosen so that there is
    # one pixel per module. Since the output is black-and-white, a simple mid-gray
    # threshold (128) produces a clean Boolean array.
    with fitz.Document(pdf_path) as doc:
        page = doc[0]
        # points → pixels at 1 pixel per module
        scale = qr.modules_count / page.rect.width
        pix = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            colorspace=fitz.csGRAY,
            alpha=False,
        )
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        # ``True`` corresponds to black
        raster = img < 128

    assert np.array_equal(raster, ref_matrix), (
        f"Rendered QR code differs from reference for message: {msg!r}\n"
        f"Reference matrix (True=black):\n{ref_matrix}\n"
        f"Rendered matrix (True=black):\n{raster}"
    )
