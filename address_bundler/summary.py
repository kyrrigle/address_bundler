import os
from collections import Counter
from typing import List, Dict, Any
import usaddress

from common.models import Student


def compute_town_histogram(students: List[Student]) -> Dict[str, int]:
    """
    Return a dict mapping town names to counts.
    Attempts to extract the town from the address string.
    """
    histogram = Counter()
    for s in students:
        town = extract_town_from_address(s.address)
        histogram[town] += 1
    return dict(histogram)


def print_histogram(histogram: Dict[str, int], max_rows: int = 10) -> None:
    """
    Print a histogram in a readable format, truncating if too many towns.
    """
    if not histogram:
        print("  (No towns found)")
        return
    sorted_items = sorted(histogram.items(), key=lambda x: -x[1])
    for i, (town, count) in enumerate(sorted_items):
        if i >= max_rows:
            print(f"... ({len(histogram) - max_rows} more towns)")
            break
        print(f"  {town}: {count}")


def is_geocoded(student: Student) -> bool:
    """
    Returns True if the student has valid geocoded coordinates.
    """
    return (
        getattr(student, "latitude", None) is not None
        and getattr(student, "longitude", None) is not None
    )


def extract_town_from_address(address: str) -> str:
    """
    Attempts to extract the town from a US-style address string using usaddress.
    Returns 'Unknown' if extraction fails.
    """
    if not address or not isinstance(address, str):
        return "Unknown"
    try:
        tagged, _ = usaddress.tag(address)
        # usaddress uses 'PlaceName' for city/town
        town = tagged.get("PlaceName")
        if town:
            return town.capitalize()
        return "Unknown"
    except Exception:
        return "Unknown"


def detect_clustering_run(students: List[Student]) -> bool:
    """
    Returns True if clustering appears to have been run.
    Heuristic: at least one student has a non-empty bundle_key.
    """
    for s in students:
        if getattr(s, "bundle_key", None):
            return True
    return False


def detect_maps_generated(project) -> bool:
    """
    Returns True if map output files exist in the project directory.
    Looks for 'master.png' in the 'output/bundles' subdirectory.
    """
    project_dir = project.get_directory()
    candidates = [
        os.path.join(project_dir, "output", "bundles", "master.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return True
    return False


def detect_pdfs_generated(project) -> bool:
    """
    Returns True if PDF output files exist in the project directory.
    Looks for 'master.pdf' in the 'output/bundles' subdirectory.
    """
    project_dir = project.get_directory()
    candidates = [
        os.path.join(project_dir, "output", "bundles", "master.pdf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return True
    return False


def run_summary_command():
    """
    Runs the summary command logic, printing a summary of the current project.
    """
    from common.project import get_project
    from .summary_formatter import print_project_summary
    from common.models import Student

    project = get_project()
    students = list(Student.select())
    num_students = len(students)
    town_histogram = compute_town_histogram(students) if num_students > 0 else None
    num_geocoded = (
        sum(1 for s in students if is_geocoded(s)) if num_students > 0 else None
    )
    clustering_run = detect_clustering_run(students) if num_students > 0 else None
    maps_generated = detect_maps_generated(project)
    pdfs_generated = detect_pdfs_generated(project)
    summary_data = {
        "num_students": num_students if num_students > 0 else None,
        "town_histogram": town_histogram,
        "num_geocoded": num_geocoded,
        "num_students_total": num_students if num_students > 0 else None,
        "clustering_run": clustering_run,
        "maps_generated": maps_generated,
        "pdfs_generated": pdfs_generated,
    }
    print_project_summary(summary_data, project=project)
