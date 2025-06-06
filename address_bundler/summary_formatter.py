"""
summary_formatter.py

Screen-only, parameterized output formatting for the 'ab summary' CLI command in Project Summary Mode.

- Visually organizes summary output using tables, lists, and sections.
- All formatting is parameterized (no hard-coded output).
- Handles missing/partial data and truncates the town histogram if there are many towns.
- No file output; screen-only.
- Independently testable and under 500 lines.

Expected input: a dict with the following keys (all optional):
    - num_students: int
    - town_histogram: dict[str, int]
    - num_geocoded: int
    - num_students_total: int
    - clustering_run: bool
    - maps_generated: bool
    - pdfs_generated: bool

Example usage:
    from address_bundler.summary_formatter import print_project_summary

    summary_data = {
        "num_students": 120,
        "town_histogram": {"Milton": 80, "Quincy": 20, "Boston": 10, "Unknown": 10},
        "num_geocoded": 110,
        "num_students_total": 120,
        "clustering_run": True,
        "maps_generated": False,
        "pdfs_generated": True,
    }
    print_project_summary(summary_data)
"""

from typing import Dict, Any, Optional, List, Tuple

# Parameterized formatting options
MAX_TOWN_ROWS = 10
SECTION_DIVIDER = "-" * 40
YES = "Yes"
NO = "No"
MISSING = "(missing)"
UNKNOWN = "Unknown"

def print_project_summary(
    summary: Dict[str, Any],
    max_town_rows: int = MAX_TOWN_ROWS,
    section_divider: str = SECTION_DIVIDER,
    project: Optional[Any] = None
) -> None:
    """
    Print a visually organized, parameterized project summary to the screen.
    Handles missing/partial data and truncates long histograms.
    Delegates formatting to get_project_summary_lines for consistency.
    """
    lines = get_project_summary_lines(
        summary,
        max_town_rows=max_town_rows,
        section_divider=section_divider,
        project=project
    )
    for line in lines:
        print(line)

def _print_town_histogram(histogram: Optional[Dict[str, int]], max_rows: int = MAX_TOWN_ROWS) -> None:
    """
    Print a histogram of towns, sorted by count descending, truncating if too many towns.
    """
    if not histogram:
        print(f"  {MISSING}")
        return
    sorted_items = sorted(
        histogram.items(),
        key=lambda x: (-x[1], str(x[0]) if x[0] is not None else "")
    )
    total_towns = len(sorted_items)
    for i, (town, count) in enumerate(sorted_items):
        if i >= max_rows:
            print(f"  ... ({total_towns - max_rows} more towns)")
            break
        print(f"  {town or UNKNOWN}: {count}")

# For independent testability
def get_project_summary_lines(
    summary: Dict[str, Any],
    max_town_rows: int = MAX_TOWN_ROWS,
    section_divider: str = SECTION_DIVIDER,
    project: Optional[Any] = None
) -> List[str]:
    """
    Return the summary as a list of lines (for testing or alternative output).
    Optionally includes project configuration if a project is provided.
    """
    lines = []
    lines.append(section_divider)
    lines.append("PROJECT SUMMARY")
    lines.append(section_divider)

    # Project configuration section
    config = None
    if project is not None and hasattr(project, "config"):
        config = project.config

    # School name
    school_name = None
    if config is not None:
        school_name = config.get("school_name", None)
    if school_name:
        lines.append(f"School name: {school_name}")
    else:
        lines.append(f"School name: {MISSING}")

    # Bundle size
    bundle_size = None
    if config is not None:
        bundle_size = config.get("bundle_size", None)
    if bundle_size is not None:
        lines.append(f"Bundle size: {bundle_size}")
    else:
        lines.append(f"Bundle size: {MISSING}")

    # Min bundle size
    min_bundle_size = None
    if config is not None:
        min_bundle_size = config.get("min_bundle_size", None)
    if min_bundle_size is not None:
        lines.append(f"Min bundle size: {min_bundle_size}")
    else:
        lines.append(f"Min bundle size: {MISSING}")

    lines.append("")  # Spacer

    # Total students
    num_students = summary.get("num_students")
    if num_students is not None:
        lines.append(f"Total students imported: {num_students}")
    else:
        lines.append(f"Total students imported: {MISSING}")

    # Town histogram
    lines.append("")
    lines.append("Towns in addresses:")
    lines.extend(_get_town_histogram_lines(summary.get("town_histogram"), max_rows=max_town_rows))

    # Geocoded count
    num_geocoded = summary.get("num_geocoded")
    num_students_total = summary.get("num_students_total", num_students)
    if num_geocoded is not None and num_students_total is not None:
        lines.append(f"\nAddresses geocoded: {num_geocoded} / {num_students_total}")
    elif num_geocoded is not None:
        lines.append(f"\nAddresses geocoded: {num_geocoded} / {MISSING}")
    else:
        lines.append(f"\nAddresses geocoded: {MISSING}")

    # Clustering status
    clustering_run = summary.get("clustering_run")
    lines.append(f"Clustering run: {YES if clustering_run else NO if clustering_run is not None else MISSING}")

    # Maps generated
    maps_generated = summary.get("maps_generated")
    lines.append(f"Maps generated: {YES if maps_generated else NO if maps_generated is not None else MISSING}")

    # PDFs generated
    pdfs_generated = summary.get("pdfs_generated")
    lines.append(f"PDFs generated: {YES if pdfs_generated else NO if pdfs_generated is not None else MISSING}")

    lines.append(section_divider)
    return lines

def _get_town_histogram_lines(histogram: Optional[Dict[str, int]], max_rows: int = MAX_TOWN_ROWS) -> List[str]:
    """
    Return the histogram of towns as a list of lines.
    """
    if not histogram:
        return [f"  {MISSING}"]
    sorted_items = sorted(
        histogram.items(),
        key=lambda x: (-x[1], str(x[0]) if x[0] is not None else "")
    )
    total_towns = len(sorted_items)
    lines = []
    for i, (town, count) in enumerate(sorted_items):
        if i >= max_rows:
            lines.append(f"  ... ({total_towns - max_rows} more towns)")
            break
        lines.append(f"  {town or UNKNOWN}: {count}")
    return lines

# Example test
if __name__ == "__main__":
    # Example with all fields
    summary_data = {
        "num_students": 120,
        "town_histogram": {"Milton": 80, "Quincy": 20, "Boston": 10, "Unknown": 10, "Weymouth": 5, "Dedham": 3, "Canton": 2, "Braintree": 2, "Randolph": 1, "Newton": 1, "Cambridge": 1},
        "num_geocoded": 110,
        "num_students_total": 120,
        "clustering_run": True,
        "maps_generated": False,
        "pdfs_generated": True,
    }
    print_project_summary(summary_data)

    # Example with missing/partial data
    print("\n" + "="*40 + "\n")
    summary_data_partial = {
        "num_students": None,
        "town_histogram": None,
        "num_geocoded": None,
        "clustering_run": None,
        "maps_generated": None,
        "pdfs_generated": None,
    }
    print_project_summary(summary_data_partial)