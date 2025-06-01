from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Dict, List

import numpy as np
from sklearn.cluster import KMeans

from .models import Student
from .project import get_project

# ---------------------------------------------------------------------- #
# Helper functions
# ---------------------------------------------------------------------- #
def _street_name(address: str) -> str:
    """
    Extract the street name from an address.

    1. Strip any leading house number (e.g. ``123 `` or ``42B ``).
    2. Ignore anything after the first comma (city/state/ZIP).
    3. Lower-case the result for stable, case-insensitive sorting.
    """
    if not address:
        return ""
    street = re.sub(r"^\s*\d+[A-Za-z]?\s+", "", address.strip())
    street = street.split(",")[0].strip()
    return street.lower()


def _index_to_excel(n: int) -> str:
    """
    Convert a zero-based integer to its Excel column letters.

    Examples
    --------
    0  -> 'A'
    25 -> 'Z'
    26 -> 'AA'
    27 -> 'AB'
    """
    n += 1  # switch to 1-based indexing
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


# ---------------------------------------------------------------------- #
# Main clustering routine
# ---------------------------------------------------------------------- #
def cluster(bundle_mode: str = "KMEANS") -> None:
    """
    Cluster geocoded students and assign *bundle* keys within each cluster.

    Parameters
    ----------
    bundle_mode : {'STREET', 'KMEANS'}, optional
        * ``STREET`` – sort students by street name inside each geographic
          cluster, then split them into even-sized bundles.
        * ``KMEANS`` (default) – run a **secondary** K-Means on the students
          *inside* each geographic cluster to form bundles by proximity,
          still enforcing the ``bundle_size`` upper limit.

    Notes
    -----
    • Regardless of ``bundle_mode``, the top-level geographic clusters are
      created with K-Means.
    • After the first pass, a **second pass** folds any bundles smaller than
      ``min_bundle_size`` (default 5) into another bundle with remaining
      capacity, then re-letters bundles so they are A, B, C… without gaps.
    """
    # ------------------------------------------------------------------ #
    # Configuration
    # ------------------------------------------------------------------ #
    bundle_mode = bundle_mode.upper()
    if bundle_mode not in {"STREET", "KMEANS"}:
        raise ValueError("bundle_mode must be 'STREET' or 'KMEANS'")

    project = get_project()
    cluster_count = int(project.config.get("cluster_count", 5))
    bundle_size = int(project.config.get("bundle_size", 20))
    min_bundle_size = int(project.config.get("min_bundle_size", 5))

    # ------------------------------------------------------------------ #
    # Fetch data
    # ------------------------------------------------------------------ #
    students: List[Student] = list(
        Student.select().where(
            Student.latitude.is_null(False),
            Student.longitude.is_null(False),
        )
    )

    if not students:
        print("No geocoded students found — run `geocode` first.")
        return

    cluster_count = min(cluster_count, len(students))  # at least one point/cluster
    coords = np.array([[s.latitude, s.longitude] for s in students])

    # ------------------------------------------------------------------ #
    # K-Means (top-level geographic clusters)
    # ------------------------------------------------------------------ #
    kmeans = KMeans(
        n_clusters=cluster_count,
        random_state=0,
        n_init="auto",
    ).fit(coords)

    for student, label in zip(students, kmeans.labels_):
        student.cluster_key = str(label+1)

    # ------------------------------------------------------------------ #
    # Bundling
    # ------------------------------------------------------------------ #
    clusters: Dict[int, List[Student]] = defaultdict(list)
    for student in students:
        clusters[int(student.cluster_key)].append(student)

    for label, members in clusters.items():
        print(f"Cluster {label}: {len(members)} students")

        # Sort once for deterministic chunking (used by both modes)
        members.sort(
            key=lambda s: (_street_name(s.address), s.last_name, s.first_name, s.id)
        )
        n = len(members)
        bundles_needed = math.ceil(n / bundle_size)

        # =============================================================== #
        # 1st pass — create initial bundles
        # =============================================================== #
        if bundle_mode == "STREET" or n <= bundle_size:
            # ---------------------------------------------------------- #
            # Evenly sized, street-sorted bundles
            # ---------------------------------------------------------- #
            base_size = n // bundles_needed
            extra = n % bundles_needed  # distribute remainder

            start = 0
            for b in range(bundles_needed):
                size = base_size + (1 if b < extra else 0)
                bundle_letter = _index_to_excel(b)
                for student in members[start : start + size]:
                    student.bundle_key = f"{label}-{bundle_letter}"
                print(f"  Bundle {label}-{bundle_letter}: {size} students")
                start += size
        else:
            # ---------------------------------------------------------- #
            # K-MEANS bundling inside this geographic cluster
            # ---------------------------------------------------------- #
            coords_sub = np.array([[s.latitude, s.longitude] for s in members])

            # Secondary K-Means to get roughly even-sized proximity bundles
            inner_kmeans = KMeans(
                n_clusters=bundles_needed,
                random_state=0,
                n_init="auto",
            ).fit(coords_sub)

            subclusters: Dict[int, List[Student]] = defaultdict(list)
            for student, sublabel in zip(members, inner_kmeans.labels_):
                subclusters[int(sublabel)].append(student)

            letter_index = 0
            for sublabel in sorted(subclusters.keys()):
                chunk = subclusters[sublabel]

                # If K-Means produced an oversize chunk, split it sequentially
                for i in range(0, len(chunk), bundle_size):
                    part = chunk[i : i + bundle_size]
                    bundle_letter = _index_to_excel(letter_index)
                    for student in part:
                        student.bundle_key = f"{label}-{bundle_letter}"
                    print(f"  Bundle {label}-{bundle_letter}: {len(part)} students")
                    letter_index += 1

        # =============================================================== #
        # 2nd pass — consolidate tiny bundles (< min_bundle_size)
        # =============================================================== #
        bundles: Dict[str, List[Student]] = defaultdict(list)
        for s in members:
            bundles[s.bundle_key].append(s)

        # Identify under-sized bundles
        tiny_keys = [
            k for k, lst in bundles.items() if len(lst) < min_bundle_size
        ]

        for tiny_key in tiny_keys:
            tiny_students = bundles[tiny_key]
            sz = len(tiny_students)

            # Find a bundle with enough remaining capacity
            candidates = [
                k
                for k, lst in bundles.items()
                if k != tiny_key and len(lst) + sz <= bundle_size
            ]
            if not candidates:
                # No room anywhere; leave tiny bundle as-is
                continue

            # Prefer the bundle with the most remaining capacity
            target_key = max(candidates, key=lambda k: bundle_size - len(bundles[k]))

            for s in tiny_students:
                s.bundle_key = target_key
                bundles[target_key].append(s)
            del bundles[tiny_key]

        # --------------------------------------------------------------- #
        # Renumber bundles so letters are consecutive (A, B, C…)
        # --------------------------------------------------------------- #
        final_keys = sorted(bundles.keys(), key=lambda k: k.split("-")[-1])
        for new_idx, old_key in enumerate(final_keys):
            new_letter = _index_to_excel(new_idx)
            new_key = f"{label}-{new_letter}"

            if new_key != old_key:
                for s in bundles[old_key]:
                    s.bundle_key = new_key
            print(f"  Bundle {new_key}: {len(bundles[old_key])} students (final)")

    # ------------------------------------------------------------------ #
    # Persist
    # ------------------------------------------------------------------ #
    with Student._meta.database.atomic():
        Student.bulk_update(students, fields=[Student.cluster_key, Student.bundle_key])

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print(
        f"Clustered {len(students)} students into {cluster_count} "
        f"cluster{'s' if cluster_count != 1 else ''} "
        f"with bundle size {bundle_size} "
        f"using {bundle_mode} bundling."
    )