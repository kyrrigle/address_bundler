"""
address_bundler.pdfs
~~~~~~~~~~~~~~~~~~~~
PDF generation utilities for Address Bundler.

Creates:

* master.pdf              – overview map (clusters.png) plus index of all
  students → bundle key.
* bundle_<bundle>.pdf     – per-bundle map plus roster with addresses.
"""

from __future__ import annotations

import os
from typing import List, Dict

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import Student
from .project import get_project
from .maps import _safe_filename  # reuse internal helper


pdfmetrics.registerFont(TTFont('Symbola', os.path.join(os.path.dirname(__file__), 'resources/Symbola.ttf')))

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _draw_image(c: canvas.Canvas, img_path: str, margin: float, max_height: float) -> float:
    """Draw *img_path* centred on the current page.

    Returns the vertical space used (height).  If the file is missing,
    draws nothing and returns 0.
    """
    if not os.path.isfile(img_path):
        return 0.0

    try:
        from PIL import Image as PILImage  # type: ignore
        iw, ih = PILImage.open(img_path).size
    except Exception:
        iw = ih = 0  # fallback square if PIL missing/unreadable

    page_width, _ = c._pagesize
    avail_width = page_width - 2 * margin

    # Determine draw size
    if iw and ih:
        ratio = ih / iw
        img_width = avail_width
        img_height = img_width * ratio
        if img_height > max_height:
            img_height = max_height
            img_width = img_height / ratio
    else:
        img_width = img_height = min(avail_width, max_height)

    x = (page_width - img_width) / 2
    y = c._pagesize[1] - margin - img_height
    c.drawImage(img_path, x, y, width=img_width, height=img_height)

    return img_height


def _draw_student_table(
    c: canvas.Canvas,
    students: List[Student],
    margin: float,
    y_start: float,
    line_height: float,
    formatter,
) -> None:
    """Render *students* starting at *y_start* using *formatter* for each line."""
    page_width, page_height = c._pagesize
    y = y_start
    c.setFont("Helvetica", 12)
    for s in students:
        if y - line_height < margin:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = page_height - margin
        c.drawString(margin, y, formatter(s))
        y -= line_height


def _draw_bundle_table(
    c: canvas.Canvas,
    students: List[Student],
    margin: float,
    y_start: float,
    line_height: float,
) -> None:
    """
    Render *students* as a table with columns:

        Sorted | Delivered | Student

    The first two columns are empty check-boxes for volunteers to tick,
    while **Student** combines name and address to save space.
    """
    page_width, page_height = c._pagesize
    checkbox_size = line_height * 0.6

    # Column positions
    x_sorted = margin
    x_delivered = x_sorted + checkbox_size + 0.25 * inch
    x_student = x_delivered + checkbox_size + 0.5 * inch

    # ------------------------------------------------------------------ #
    # Header row
    # ------------------------------------------------------------------ #
    y = y_start
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_sorted, y, "Sorted")
    c.drawString(x_delivered, y, "Delivered")
    c.drawString(x_student, y, "Student")

    y -= line_height
    c.setFont("Helvetica", 12)

    for s in students:
        # Page-break handling
        if y - line_height < margin:
            c.showPage()
            y = page_height - margin
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_sorted, y, "Sorted")
            c.drawString(x_delivered, y, "Delivered")
            c.drawString(x_student, y, "Student")
            y -= line_height
            c.setFont("Helvetica", 12)

        # Draw empty check-boxes using a Unicode character for better alignment
        c.setFont('Symbola', 12)
        c.drawString(x_sorted, y, "☐")
        c.drawString(x_delivered, y, "☐")

        # Student details
        c.setFont("Helvetica", 12)
        c.drawString(
            x_student,
            y,
            f"{s.last_name}, {s.first_name} — {s.address}",
        )
        y -= line_height


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_pdfs() -> None:
    """Generate master and per-bundle PDFs for the current project."""

    students: List[Student] = list(Student.select())
    if not students:
        print("No students found – PDF generation skipped.")
        return

    bundles: Dict[str, List[Student]] = {}
    for s in students:
        key = s.bundle_key or "unbundled"
        bundles.setdefault(key, []).append(s)

    # Output directory (where the PNGs already reside)
    try:
        project = get_project()
        output_dir = project.get_directory()
    except Exception:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    margin = 0.5 * inch
    line_height = 0.28 * inch
    page_width, page_height = LETTER

    # ------------------------------------------------------------------ #
    # Master PDF
    # ------------------------------------------------------------------ #
    master_path = os.path.join(output_dir, "master.pdf")
    c = canvas.Canvas(master_path, pagesize=LETTER)

    clusters_png = os.path.join(output_dir, "clusters.png")
    img_height = _draw_image(c, clusters_png, margin, max_height=page_height * 0.5)

    title_y = page_height - margin - (img_height + line_height if img_height else 0)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_width / 2, title_y, "Student Index")

    students_sorted = sorted(students, key=lambda s: (s.last_name, s.first_name))
    _draw_student_table(
        c,
        students_sorted,
        margin,
        title_y - line_height * 1.5,
        line_height,
        formatter=lambda s: f"{s.last_name}, {s.first_name}  —  {s.bundle_key or ''}",
    )

    c.save()
    print(f"Master PDF created → {master_path}")

    # ------------------------------------------------------------------ #
    # Bundle PDFs
    # ------------------------------------------------------------------ #
    for bundle_key, members in sorted(bundles.items()):
        pdf_name = f"bundle_{_safe_filename(bundle_key)}.pdf"
        pdf_path = os.path.join(output_dir, pdf_name)
        c = canvas.Canvas(pdf_path, pagesize=LETTER)

        png_name = f"bundle_{_safe_filename(bundle_key)}.png"
        png_path = os.path.join(output_dir, png_name)
        img_height = _draw_image(c, png_path, margin, max_height=page_height * 0.3)

        title_y = page_height - margin - (img_height + line_height if img_height else 0)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(page_width / 2, title_y, f"Bundle {bundle_key}")

        members_sorted = sorted(
            members, key=lambda s: (s.address.lower(), s.last_name, s.first_name)
        )
        _draw_bundle_table(
            c,
            members_sorted,
            margin,
            title_y - line_height * 1.5,
            line_height,
        )

        c.save()
        print(f"   ↳ bundle {bundle_key}: {pdf_path}")
    print("PDF generation complete.")