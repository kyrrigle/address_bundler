from __future__ import annotations

import os
import json
import io
import math
from typing import Dict, Any, Optional, Iterator

from PyPDF2 import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import simpleSplit

from common.models import Student
from common.project import get_project


class Box:
    """
    Represents a rectangular area with x, y (top-left coordinates in inches),
    and w, h (width and height in inches).
    """

    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)

    @classmethod
    def from_dict(cls, data: dict) -> "Box":
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            w=data.get("w", 0.0),
            h=data.get("h", 0.0),
        )

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    def __repr__(self):
        return f"Box(x={self.x}, y={self.y}, w={self.w}, h={self.h})"


class Slot:
    """Base class for a template slot."""

    def __init__(self, name: str, slot_data: dict):
        self.name = name
        self.type = slot_data.get("type")
        box_data = slot_data.get("box")
        self.box = Box.from_dict(box_data) if box_data else None
        self.raw = slot_data

    def __repr__(self):
        return f"<Slot name={self.name!r} type={self.type!r}>"


class ImageSlot(Slot):
    def __init__(self, name: str, slot_data: dict):
        super().__init__(name, slot_data)
        # Image-specific fields can be added here


class TextSlot(Slot):
    def __init__(self, name: str, slot_data: dict):
        super().__init__(name, slot_data)
        self.font_name = slot_data.get("font_name")
        self.font_size = slot_data.get("font_size")


class Template:
    def __init__(self, template_path: str):
        # templates have two parts-
        # 1. template json (the template_path)
        # 2. template pdf (the basename of template_path with the extension .pdf)
        self.json_path = template_path
        base, _ = os.path.splitext(template_path)
        self.pdf_path = base + ".pdf"
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self._slots = self._parse_slots(self.data.get("slots", {}))

    def _parse_slots(self, slots_dict: Dict[str, Any]) -> Dict[str, Slot]:
        slots: Dict[str, Slot] = {}
        for name, slot_data in slots_dict.items():
            slot_type = slot_data.get("type")
            if slot_type == "image":
                slots[name] = ImageSlot(name, slot_data)
            elif slot_type == "text":
                slots[name] = TextSlot(name, slot_data)
            else:
                slots[name] = Slot(name, slot_data)
        return slots

    @property
    def template_json(self) -> str:
        """Return the path to the template JSON file."""
        return self.json_path

    @property
    def template_pdf(self) -> str:
        """Return the path to the template PDF file."""
        return self.pdf_path

    @property
    def template_data(self) -> dict:
        """Return the loaded template JSON data."""
        return self.data

    @property
    def slots(self) -> Dict[str, Slot]:
        """Return all slots as a dict of Slot objects keyed by slot name."""
        return self._slots

    def get_slot(self, name: str) -> Optional[Slot]:
        """Get a slot by name."""
        return self._slots.get(name)

    @property
    def image_slots(self) -> Dict[str, "ImageSlot"]:
        """Return all image slots."""
        return {k: v for k, v in self._slots.items() if isinstance(v, ImageSlot)}

    @property
    def text_slots(self) -> Dict[str, "TextSlot"]:
        """Return all text slots."""
        return {k: v for k, v in self._slots.items() if isinstance(v, TextSlot)}

    def iter_slots(self) -> Iterator[Slot]:
        """Iterate over all slots."""
        return iter(self._slots.values())

    def get_slot_requirements(self) -> Dict[str, dict]:
        """
        Return a dict describing the required input for each slot.
        For text slots: expects a string value.
        For image slots: expects a path to an image file.
        """
        requirements = {}
        for name, slot in self._slots.items():
            if isinstance(slot, TextSlot):
                requirements[name] = {
                    "type": "text",
                    "required": True,
                    "description": "Text value required",
                }
            elif isinstance(slot, ImageSlot):
                requirements[name] = {
                    "type": "image",
                    "required": True,
                    "description": "Path to image file required",
                }
            else:
                requirements[name] = {
                    "type": slot.type,
                    "required": True,
                    "description": f"Value required for slot type '{slot.type}'",
                }
        return requirements

    def validate_slot_values(self, slot_values: Dict[str, Any]) -> None:
        """
        Validate that the provided slot_values dict contains all required slots
        and that the values are of the correct type.
        For text slots: value must be a string.
        For image slots: value must be a string path to an existing file.
        Raises ValueError if validation fails.
        """
        requirements = self.get_slot_requirements()
        missing = [name for name in requirements if name not in slot_values]
        if missing:
            raise ValueError(f"Missing required slot values for: {', '.join(missing)}")

        for name, req in requirements.items():
            value = slot_values[name]
            if req["type"] == "text":
                if not isinstance(value, str):
                    raise ValueError(f"Slot '{name}' expects a string value.")
            elif req["type"] == "image":
                if not isinstance(value, str):
                    raise ValueError(f"Slot '{name}' expects a file path as a string.")
                if not os.path.isfile(value):
                    raise ValueError(
                        f"Slot '{name}' expects a valid file path, but '{value}' does not exist."
                    )
            # Other slot types can be extended here as needed


def render_template(
    template: Template, slot_values: Dict[str, Any], output_path: str
) -> None:
    """
    Render the provided `template` with the given `slot_values` into `output_path`.

    * Validates slot values first.
    * Builds an overlay PDF in-memory using ReportLab.
    * Draws each `ImageSlot` or `TextSlot` based on its `Box`.
    * Merges overlay with the template PDF and saves the result.
    """
    # 1. Ensure all required input is present and well-typed
    template.validate_slot_values(slot_values)

    # 2. Read the template PDF to fetch page dimensions
    reader = PdfReader(template.template_pdf)
    base_page = reader.pages[0]
    page_width = float(base_page.mediabox.width)
    page_height = float(base_page.mediabox.height)

    # 3. Create an in-memory canvas matching the template size
    packet = io.BytesIO()
    canv = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # Helper: draw wrapped, centered text inside a box whose coordinates are top-left based
    def _draw_text(text: str, box: Box, font_name: str, font_size: int) -> None:
        """
        Draw `text` inside `box`, wrapping horizontally (max width) and
        centering the entire block vertically.
        """
        max_width = box.w * inch - 0.2 * inch  # slight horizontal padding
        leading = font_size * 1.2
        lines = simpleSplit(text, font_name, font_size, max_width)
        text_height = font_size + (len(lines) - 1) * leading

        # Convert box top-left to PDF bottom-left
        x_left_pts = box.x * inch
        y_bottom_pts = page_height - (box.y * inch) - (box.h * inch)
        region_center_y = y_bottom_pts + (box.h * inch) / 2

        # Baseline of first line so that the block is vertically centered
        y_start = region_center_y + text_height / 2 - font_size

        canv.setFont(font_name, font_size)
        x_center = x_left_pts + (box.w * inch) / 2
        y = y_start
        for line in lines:
            canv.drawCentredString(x_center, y, line)
            y -= leading

    # 4. Iterate over each defined slot and paint onto canvas
    for name, slot in template.slots.items():
        value = slot_values[name]
        box = slot.box
        if box is None:
            # Skip slots without a defined drawing box
            continue

        if isinstance(slot, ImageSlot):
            # Convert coordinates: template uses top-left origin in inches,
            # ReportLab uses bottom-left in points.
            x_pts = box.x * inch
            y_pts = page_height - (box.y * inch) - (box.h * inch)
            canv.drawImage(
                value,
                x_pts,
                y_pts,
                width=box.w * inch,
                height=box.h * inch,
                preserveAspectRatio=True,
                anchor="c",
            )
        elif isinstance(slot, TextSlot):
            font_name = slot.font_name or "Helvetica"
            font_size = slot.font_size or 12
            _draw_text(str(value), box, font_name, font_size)
        else:
            # Unknown slot type – ignore for now
            continue

    # 5. Finalise overlay and merge with base template
    canv.save()
    packet.seek(0)
    overlay_page = PdfReader(packet).pages[0]
    base_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(base_page)
    with open(output_path, "wb") as fh:
        writer.write(fh)


def build_contact_sheet(
    sign_files: list[str],
    output_path: str,
    per_page: int = 10,
    cols: int = 2,
) -> None:
    """
    Create a contact-sheet PDF placing up to ``per_page`` sign files (PDF or image)
    on each page in a ``cols``-column grid (rows are calculated automatically).

    • Page size: US-Letter portrait (8.5 × 11 inch ⇒ 612 × 792 pt)
    • Thumbnails are scaled to fit inside their cell while preserving aspect.
    • Accepts both PDF files (first page rasterized) and image files (jpg, png, jpeg).

    Parameters
    ----------
    sign_files : list[str]
        Paths to individual sign files (PDF or image).
    output_path : str
        Destination file for the contact sheet.
    per_page : int
        Maximum number of signs per page.
    cols : int
        Number of columns in the grid (default 2).
    """
    if not sign_files:
        return

    from pdf2image import convert_from_path
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    import tempfile
    from PIL import Image
    import warnings

    page_w, page_h = 612.0, 792.0  # 72 pt per inch
    rows = math.ceil(per_page / cols)
    slot_w = page_w / cols
    slot_h = page_h / rows

    pages = []
    slot_index = 0
    canv = None
    img_cache = {}

    for idx, file_path in enumerate(sign_files):
        if slot_index == 0:
            packet = io.BytesIO()
            canv = canvas.Canvas(packet, pagesize=(page_w, page_h))

        row = slot_index // cols
        col = slot_index % cols

        # Determine file type and get PIL image
        if file_path not in img_cache:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                images = convert_from_path(file_path, first_page=1, last_page=1)
                img_cache[file_path] = images[0]
            elif ext in [".jpg", ".jpeg", ".png"]:
                img_cache[file_path] = Image.open(file_path).convert("RGB")
            else:
                # Skip unsupported file types
                continue
        img = img_cache[file_path]

        # Calculate scaling to fit in slot while preserving aspect ratio
        img_w, img_h = img.size
        scale = min((slot_w - 10) / img_w, (slot_h - 10) / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale

        x_off = col * slot_w + (slot_w - draw_w) / 2
        y_off = page_h - (row + 1) * slot_h + (slot_h - draw_h) / 2

        # Resize and compress the image before embedding to reduce PDF size
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore"
            )  # Suppress PIL DecompressionBombWarning for large images
            resized_img = img.resize((int(draw_w), int(draw_h)), Image.LANCZOS)
        img_buffer = io.BytesIO()
        # Save as JPEG with moderate quality to reduce size
        resized_img.save(img_buffer, format="JPEG", quality=70, optimize=True)
        img_buffer.seek(0)
        # Draw the compressed image
        canv.drawImage(
            ImageReader(img_buffer),
            x_off,
            y_off,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
            anchor="c",
        )

        slot_index += 1
        if slot_index >= per_page or idx == len(sign_files) - 1:
            canv.save()
            packet.seek(0)
            pages.append(packet.read())
            slot_index = 0

    # Combine all pages into a single PDF
    writer = PdfWriter()
    for page_bytes in pages:
        pdf_page = PdfReader(io.BytesIO(page_bytes)).pages[0]
        writer.add_page(pdf_page)

    with open(output_path, "wb") as fh:
        writer.write(fh)


def render_templates_command(force: bool = False, per_page: int = 10) -> None:
    """
    Render signs for every student whose photo has already been cropped
    **and** build a contact-sheet PDF that lays out up to ``per_page`` signs
    on each page.

    Parameters
    ----------
    force : bool
        If ``True`` re-render even if signs already exist.
    per_page : int
        Maximum number of signs per page in the contact sheet (default 10).
    """
    import sys
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # ------------------------------------------------------------------ paths
    project = get_project()
    project_path = project.get_directory()
    root = os.path.abspath(project_path)
    template_json = os.path.join(root, "template.json")
    signs_dir = os.path.join(root, "signs")
    cropped_dir = os.path.join(root, "cropped")

    # Validate template -------------------------------------------------------
    if not os.path.isfile(template_json):
        logging.error("Template JSON not found: %s", template_json)
        sys.exit(1)

    template = Template(template_json)

    # Prepare output dir ------------------------------------------------------
    os.makedirs(signs_dir, exist_ok=True)

    # ---------------------------------------------------------------- students
    students = list(Student.get_students_needing_signs(force=force))
    if not students:
        print("No signs need rendering – all caught up.")
        return

    rendered_count = 0
    failures: list[tuple[str, str]] = []

    # ------------------------------------------------------------- main loop
    for student in students:
        student_name = f"{student.first_name} {student.last_name}".strip()

        if not student.image_name:
            failures.append((student_name, "missing image_name in database"))
            continue

        cropped_photo = os.path.join(cropped_dir, student.image_name)
        if not os.path.isfile(cropped_photo):
            failures.append((student_name, f"cropped photo not found: {cropped_photo}"))
            continue

        output_pdf = os.path.join(
            signs_dir, os.path.splitext(student.image_name)[0] + ".pdf"
        )
        if os.path.exists(output_pdf) and not force:
            logging.info("Skipping %s (sign already exists)", student_name)
            continue

        slot_values = {
            "photo": cropped_photo,
            "name": student_name,
        }

        try:
            render_template(template, slot_values, output_pdf)
            rendered_count += 1
            logging.info("Rendered sign for %-30s → %s", student_name, output_pdf)
        except Exception as exc:  # pylint: disable=broad-except
            failures.append((student_name, str(exc)))
            logging.exception("Failed rendering sign for %s", student_name)

    # ---------------------------------------------------------------- summary
    print(f"\nFinished: {rendered_count} sign(s) created in '{signs_dir}'.")

    # ----------------------------------------------------------- contact sheet
    try:
        sign_files = [
            os.path.join(signs_dir, f)
            for f in sorted(os.listdir(signs_dir))
            if f.lower().endswith(".pdf")
        ]
        contact_sheet_path = os.path.join(root, "contact_sheet.pdf")
        build_contact_sheet(sign_files, contact_sheet_path, per_page=per_page)
        print(f"Contact sheet created → {contact_sheet_path}")
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to create contact sheet: %s", exc)

    if failures:
        print("\n⚠️  The following sign(s) failed to render:")
        for name, reason in failures:
            print(f"  • {name}: {reason}")
        sys.exit(2)
