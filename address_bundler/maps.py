from __future__ import annotations

import os
import re
import colorsys
from typing import Dict, List

import staticmaps

from .models import Student
from .project import get_project


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
    Return a visually distinct color for the *idx*-th cluster.

    * For the first few clusters we reuse a fixed palette for clarity.
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
    Create png maps visualising student locations:

    • *clusters.png* – all clusters, each with a unique color.
    • *cluster_<cluster_key>.png* – one image per cluster, bundles in unique colors.
    • *bundle_<bundle_key>.png* – one image per bundle (uniform color).
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

    clusters: Dict[str, List[Student]] = {}
    for s in students:
        key = s.cluster_key or "unclustered"
        clusters.setdefault(key, []).append(s)

    # ------------------------------------------------------------------ #
    # 2. Build the static map containing *all* clusters
    # ------------------------------------------------------------------ #
    ctx = staticmaps.Context()
    ctx.set_tile_provider(staticmaps.tile_provider_OSM)

    for idx, (cluster_key, members) in enumerate(clusters.items()):
        color = _index_to_color(idx)
        for student in members:
            coord = staticmaps.create_latlng(student.latitude, student.longitude)
            ctx.add_object(staticmaps.Marker(coord, color=color, size=12))

    # Ensure the resulting image frames all points nicely
    image = ctx.render_pillow(width, height)

    # ------------------------------------------------------------------ #
    # 3. Determine output path and save
    # ------------------------------------------------------------------ #
    project = None
    try:
        project = get_project()
    except Exception:
        # Not in a project context – fall back to CWD
        pass

    output_dir = project.get_directory() if project else os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "clusters.png")

    image.save(output_path)
    print(f"Cluster map generated → {output_path}")

    # ------------------------------------------------------------------ #
    # 4. Generate individual maps for each cluster
    # ------------------------------------------------------------------ #
    for c_idx, (cluster_key, members) in enumerate(clusters.items()):
        cluster_ctx = staticmaps.Context()
        cluster_ctx.set_tile_provider(staticmaps.tile_provider_OSM)

        # Use bundle keys to pick colours within this cluster map
        bundle_keys = sorted({s.bundle_key or "unbundled" for s in members})
        bundle_color_map = {
            bk: _index_to_color(i) for i, bk in enumerate(bundle_keys)
        }

        for s in members:
            coord = staticmaps.create_latlng(s.latitude, s.longitude)
            color = bundle_color_map[s.bundle_key or "unbundled"]
            cluster_ctx.add_object(staticmaps.Marker(coord, color=color, size=12))

        cluster_image = cluster_ctx.render_pillow(width, height)
        filename = f"cluster_{_safe_filename(cluster_key)}.png"
        cluster_path = os.path.join(output_dir, filename)
        cluster_image.save(cluster_path)
        print(f"   ↳ {cluster_key}: {cluster_path}")

    # ------------------------------------------------------------------ #
    # 5. Generate individual maps for each bundle
    # ------------------------------------------------------------------ #
    bundles: Dict[str, List[Student]] = {}
    for s in students:
        b_key = s.bundle_key or "unbundled"
        bundles.setdefault(b_key, []).append(s)

    # All bundle maps use the same marker color for clarity
    bundle_marker_color = staticmaps.BLUE

    for b_idx, (bundle_key, members) in enumerate(bundles.items()):
        bundle_ctx = staticmaps.Context()
        bundle_ctx.set_tile_provider(staticmaps.tile_provider_OSM)

        for s in members:
            coord = staticmaps.create_latlng(s.latitude, s.longitude)
            bundle_ctx.add_object(staticmaps.Marker(coord, color=bundle_marker_color, size=12))

        bundle_image = bundle_ctx.render_pillow(width, height)
        filename = f"bundle_{_safe_filename(bundle_key)}.png"
        bundle_path = os.path.join(output_dir, filename)
        bundle_image.save(bundle_path)
        print(f"   ↳ bundle {bundle_key}: {bundle_path}")