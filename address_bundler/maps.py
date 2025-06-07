from __future__ import annotations

import os
import re
import colorsys
from typing import Dict, List

import staticmaps

from common.models import Student
from common.project import get_project


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
_PREDEFINED_COLORS = [
    staticmaps.RED,
    staticmaps.GREEN,
    staticmaps.BLUE,
    staticmaps.YELLOW,
    staticmaps.ORANGE,
    staticmaps.PURPLE,
]


def _index_to_color(idx: int) -> staticmaps.Color:
    """
    Return a visually distinct color for an integer index.

    * For the first few indices we reuse a fixed palette for clarity.
    * Beyond that we generate colors in HSV space and convert to RGB.
    """
    if idx < len(_PREDEFINED_COLORS):
        return _PREDEFINED_COLORS[idx]

    # Golden-ratio hop around the color wheel for well-spaced hues
    hue = (idx * 0.61803398875) % 1.0
    r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.7, 0.9))
    return staticmaps.Color(r, g, b, 255)


def _safe_filename(name: str) -> str:
    """
    Convert *name* into a filesystem-safe filename.

    All non-alphanumeric characters are replaced with "_", and leading /
    trailing underscores are stripped.
    """
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()).strip("_")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_maps(width: int = 1200, height: int = 800) -> None:
    """
    Generate map PNGs visualising student locations:

    • **master.png** – all students, colour-coded by *bundle_key*.
    • **bundle_<bundle_key>.png** – one image per bundle (uniform colour).
    """
    # ------------------------------------------------------------------ #
    # 1. Gather data from the database
    # ------------------------------------------------------------------ #
    students: List[Student] = list(
        Student.select().where(
            Student.latitude.is_null(False),
            Student.longitude.is_null(False),
        )
    )

    if not students:
        print("No geocoded students found – nothing to map.")
        return

    # Build a mapping bundle_key → students
    bundles: Dict[str, List[Student]] = {}
    for s in students:
        b_key = s.bundle_key or "unbundled"
        bundles.setdefault(b_key, []).append(s)

    # ------------------------------------------------------------------ #
    # 2. Build the master map (all students, coloured by bundle)
    # ------------------------------------------------------------------ #
    master_ctx = staticmaps.Context()
    master_ctx.set_tile_provider(staticmaps.tile_provider_OSM)

    bundle_keys_sorted = sorted(bundles.keys())
    bundle_color_map = {
        bk: _index_to_color(i) for i, bk in enumerate(bundle_keys_sorted)
    }

    for b_key, members in bundles.items():
        color = bundle_color_map[b_key]
        for s in members:
            coord = staticmaps.create_latlng(s.latitude, s.longitude)
            master_ctx.add_object(staticmaps.Marker(coord, color=color, size=12))

    master_image = master_ctx.render_pillow(width, height)

    # Determine output directory
    try:
        project = get_project()
        output_dir = os.path.join(project.get_directory(), "output", "bundles")
    except Exception:
        output_dir = os.path.join(os.getcwd(), "output", "bundles")

    os.makedirs(output_dir, exist_ok=True)
    master_path = os.path.join(output_dir, "master.png")
    master_image.save(master_path)
    print(f"Master map generated → {master_path}")

    # ------------------------------------------------------------------ #
    # 3. Generate individual maps for each bundle
    # ------------------------------------------------------------------ #
    bundle_marker_color = staticmaps.BLUE  # Uniform colour within each bundle map

    for b_key, members in bundles.items():
        bundle_ctx = staticmaps.Context()
        bundle_ctx.set_tile_provider(staticmaps.tile_provider_OSM)

        for s in members:
            coord = staticmaps.create_latlng(s.latitude, s.longitude)
            bundle_ctx.add_object(
                staticmaps.Marker(coord, color=bundle_marker_color, size=12)
            )

        bundle_image = bundle_ctx.render_pillow(width, height)
        filename = f"bundle_{_safe_filename(b_key)}.png"
        bundle_path = os.path.join(output_dir, filename)
        bundle_image.save(bundle_path)
        print(f"   ↳ bundle {b_key}: {bundle_path}")
