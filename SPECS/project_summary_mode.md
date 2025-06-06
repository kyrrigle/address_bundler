# Functional Specification: Project Summary Mode

## Overview
Add a CLI command ab summary to the project, handled via the existing main.py entry point using the docopt library for command line parsing. This command prints a well-formatted, easy-to-read summary of the current project state to the screen, including key statistics and status indicators for data import, geocoding, clustering, map generation, and PDF generation.

---

## Functional Requirements

### 1. Inputs
- **Project Data**: Access to the current project state, including:
  - Imported students and their addresses
  - Geocoding results
  - Clustering status
  - Map generation status
  - PDF generation status

### 2. Outputs
- **Text Summary**: Printed to the screen (stdout), including:
  - Total number of students imported
  - Histogram of towns found in addresses
  - Number of addresses geocoded
  - Whether clustering has been run
  - Whether maps have been generated
  - Whether PDFs have been generated

### 3. User Flow
1. User runs the CLI command: ab summary
2. main.py parses the command using docopt and dispatches to the summary handler.
3. System gathers current project data.
4. System computes required statistics and status flags.
5. System prints a formatted summary to the screen.

### 4. Constraints
- Output must be readable and visually organized (tables, lists, or sections).
- No file output; summary is for screen only.
- Must handle missing or incomplete data gracefully.
- Each module <500 lines.

### 5. Edge Cases
- No students imported: Show “No data imported” message.
- No addresses geocoded: Indicate as “0 geocoded.”
- No clustering/maps/PDFs: Indicate as “Not run” or “Not generated.”
- Large number of towns: Truncate or summarize histogram if needed.

---

## Pseudocode

### main.py (docopt CLI entry point)

```python
"""
Usage:
  ab summary
  ... (other commands)
"""

from docopt import docopt

def main():
    args = docopt(__doc__)
    if args['summary']:
        handle_summary()

def handle_summary():
    project = load_project()
    summarize_project(project)
```

### Module: summarize_project

```python
def summarize_project(project):
    """
    Print a summary of the current project state.
    Args:
        project: Project object with all relevant data and status.
    """
    # 1. Students imported
    num_students = len(project.students)
    print(f"Total students imported: {num_students}")

    # 2. Histogram of towns
    town_histogram = compute_town_histogram(project.students)
    print("Towns in addresses:")
    print_histogram(town_histogram)

    # 3. Geocoded count
    num_geocoded = sum(1 for s in project.students if s.geocoded)
    print(f"Addresses geocoded: {num_geocoded} / {num_students}")

    # 4. Clustering status
    print("Clustering run:", "Yes" if project.clustering_run else "No")

    # 5. Maps generated
    print("Maps generated:", "Yes" if project.maps_generated else "No")

    # 6. PDFs generated
    print("PDFs generated:", "Yes" if project.pdfs_generated else "No")
```

### Module: compute_town_histogram

```python
def compute_town_histogram(students):
    """
    Return a dict mapping town names to counts.
    """
    histogram = {}
    for s in students:
        town = s.address.town if s.address else "Unknown"
        histogram[town] = histogram.get(town, 0) + 1
    return histogram
```

### Module: print_histogram

```python
def print_histogram(histogram, max_rows=10):
    """
    Print a histogram in a readable format, truncating if too many towns.
    """
    sorted_items = sorted(histogram.items(), key=lambda x: -x[1])
    for i, (town, count) in enumerate(sorted_items):
        if i >= max_rows:
            print(f"... ({len(histogram) - max_rows} more towns)")
            break
        print(f"  {town}: {count}")
```

### TDD Anchors

- [ ] Test: ab summary with full data (students, geocoded, clustering, maps, PDFs).
- [ ] Test: ab summary with no students imported.
- [ ] Test: ab summary with partial data (some geocoded, clustering not run, etc.).
- [ ] Test: Histogram with many towns (truncation).
- [ ] Test: Handles missing address/town fields.

---

## Notes

- All data access should be via the project object or injected dependencies.
- No hard-coded output; all formatting should be parameterized if possible.
- Each module should be <500 lines and independently testable.
- The CLI entry point and command parsing must remain in main.py using docopt.