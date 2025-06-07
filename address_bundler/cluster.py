from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Dict, List

import numpy as np
from sklearn.cluster import KMeans

from common.models import Student
from common.project import get_project


# ---------------------------------------------------------------------- #
# Helper functions
# ---------------------------------------------------------------------- #
def _street_name(address: str) -> str:
    """
    Extract the street name from an address, ignoring house number
    and anything after the first comma. Returned in lower-case so that
    results are stable irrespective of capitalisation.
    """
    if not address:
        return ""
    street = re.sub(r"^\\s*\\d+[A-Za-z]?\\s+", "", address.strip())
    street = street.split(",")[0].strip()
    return street.lower()


def _index_to_excel(n: int) -> str:
    """
    Convert zero-based index → Excel column letters.
    0→A, 25→Z, 26→AA, etc.
    """
    n += 1  # switch to 1-based
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


# ---------------------------------------------------------------------- #
# Main bundling routine
# ---------------------------------------------------------------------- #
def cluster() -> None:
    """
    Bundle students directly with a **single** K-Means run.

    All students are assigned the same ``cluster_key`` (``"1"``).  The number
    of K-Means clusters is chosen so that the largest cluster will not exceed
    ``bundle_size``.  After initial assignment, bundles smaller than
    ``min_bundle_size`` are folded into larger bundles with spare capacity and
    finally re-lettered so bundle keys are consecutive.
    """
    # ------------------------------------------------------------------ #
    # Configuration
    # ------------------------------------------------------------------ #
    project = get_project()
    bundle_size = int(project.config.get("bundle_size", 20))
    min_bundle_size = int(project.config.get("min_bundle_size", 10))

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

    n_students = len(students)
    bundles_needed = max(1, math.ceil(n_students / bundle_size))
    coords = np.array([[s.latitude, s.longitude] for s in students])

    # ------------------------------------------------------------------ #
    # Single K-Means to create proximity-based bundles
    # ------------------------------------------------------------------ #
    kmeans = KMeans(
        n_clusters=bundles_needed,
        random_state=0,
        n_init="auto",
    ).fit(coords)

    # Group by resulting label
    subclusters: Dict[int, List[Student]] = defaultdict(list)
    for student, label in zip(students, kmeans.labels_):
        subclusters[int(label)].append(student)
        # cluster_key removed – no assignment necessary

    # ------------------------------------------------------------------ #
    # Assign initial bundle keys (split oversize clusters if necessary)
    # ------------------------------------------------------------------ #
    letter_index = 0
    bundles: Dict[str, List[Student]] = defaultdict(list)

    for label in sorted(subclusters.keys()):
        chunk = subclusters[label]
        # Sort deterministically before sequential splitting
        chunk.sort(
            key=lambda s: (_street_name(s.address), s.last_name, s.first_name, s.id)
        )

        for i in range(0, len(chunk), bundle_size):
            part = chunk[i : i + bundle_size]
            bundle_letter = _index_to_excel(letter_index)
            bundle_key = f"1-{bundle_letter}"
            for s in part:
                s.bundle_key = bundle_key
            bundles[bundle_key].extend(part)
            print(f"Bundle {bundle_key}: {len(part)} students")
            letter_index += 1

    # ------------------------------------------------------------------ #
    # Fold bundles smaller than min_bundle_size
    # ------------------------------------------------------------------ #
    tiny_keys = [k for k, lst in bundles.items() if len(lst) < min_bundle_size]

    for tiny_key in tiny_keys:
        tiny_students = bundles[tiny_key]
        sz = len(tiny_students)

        # Candidate bundles with spare capacity
        candidates = [
            k
            for k, lst in bundles.items()
            if k != tiny_key and len(lst) + sz <= bundle_size
        ]
        if not candidates:
            continue  # cannot merge; leave as-is

        # Pick bundle with most remaining capacity
        target_key = max(candidates, key=lambda k: bundle_size - len(bundles[k]))

        for s in tiny_students:
            s.bundle_key = target_key
            bundles[target_key].append(s)
        del bundles[tiny_key]

    # ------------------------------------------------------------------ #
    # Renumber bundle letters so they are consecutive (A, B, C…)
    # ------------------------------------------------------------------ #
    final_keys = sorted(bundles.keys(), key=lambda k: k.split("-")[-1])
    for new_idx, old_key in enumerate(final_keys):
        new_letter = _index_to_excel(new_idx)
        new_key = f"1-{new_letter}"
        if new_key != old_key:
            for s in bundles[old_key]:
                s.bundle_key = new_key
        print(f"Bundle {new_key}: {len(bundles[old_key])} students (final)")

    # ------------------------------------------------------------------ #
    # Persist
    # ------------------------------------------------------------------ #
    with Student._meta.database.atomic():
        Student.bulk_update(students, fields=[Student.bundle_key])

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    bundle_count = len({s.bundle_key for s in students})
    print(
        f"Bundled {n_students} students into {bundle_count} "
        f"bundle{'s' if bundle_count != 1 else ''} "
        f"(max {bundle_size}, min {min_bundle_size})."
    )
