import pytest
from address_bundler import summary_formatter

SECTION_DIVIDER = "-" * 40

def test_full_summary():
    summary = {
        "num_students": 5,
        "town_histogram": {"Milton": 3, "Quincy": 1, "Unknown": 1},
        "num_geocoded": 4,
        "num_students_total": 5,
        "clustering_run": True,
        "maps_generated": True,
        "pdfs_generated": False,
    }
    lines = summary_formatter.get_project_summary_lines(summary)
    assert "Total students imported: 5" in lines
    assert "  Milton: 3" in lines
    assert "  Quincy: 1" in lines
    assert "  Unknown: 1" in lines
    assert "\nAddresses geocoded: 4 / 5" in lines
    assert "Clustering run: Yes" in lines
    assert "Maps generated: Yes" in lines
    assert "PDFs generated: No" in lines

def test_partial_summary_missing_fields():
    summary = {
        "num_students": None,
        "town_histogram": None,
        "num_geocoded": None,
        "clustering_run": None,
        "maps_generated": None,
        "pdfs_generated": None,
    }
    lines = summary_formatter.get_project_summary_lines(summary)
    assert f"Total students imported: {summary_formatter.MISSING}" in lines
    assert f"  {summary_formatter.MISSING}" in lines
    assert f"\nAddresses geocoded: {summary_formatter.MISSING}" in lines
    assert f"Clustering run: {summary_formatter.MISSING}" in lines
    assert f"Maps generated: {summary_formatter.MISSING}" in lines
    assert f"PDFs generated: {summary_formatter.MISSING}" in lines

def test_empty_histogram():
    summary = {
        "num_students": 0,
        "town_histogram": {},
        "num_geocoded": 0,
        "clustering_run": False,
        "maps_generated": False,
        "pdfs_generated": False,
    }
    lines = summary_formatter.get_project_summary_lines(summary)
    assert "Total students imported: 0" in lines
    assert "  (missing)" in lines or "  {}" in lines  # Accepts either missing or empty

def test_histogram_truncation():
    # 12 towns, should truncate at 10
    histogram = {f"Town{i}": 1 for i in range(12)}
    summary = {
        "num_students": 12,
        "town_histogram": histogram,
        "num_geocoded": 12,
        "clustering_run": True,
        "maps_generated": True,
        "pdfs_generated": True,
    }
    lines = summary_formatter.get_project_summary_lines(summary)
    # Should show 10 towns, then truncation line
    town_lines = [line for line in lines if line.startswith("  Town")]
    assert len(town_lines) == 10
    trunc_lines = [line for line in lines if "more towns" in line]
    assert trunc_lines
    assert "  ... (2 more towns)" in trunc_lines[0]

def test_histogram_with_unknown_and_empty_town():
    histogram = {"Milton": 2, "": 1, None: 1}
    summary = {
        "num_students": 4,
        "town_histogram": histogram,
        "num_geocoded": 4,
        "clustering_run": False,
        "maps_generated": False,
        "pdfs_generated": False,
    }
    lines = summary_formatter.get_project_summary_lines(summary)
    # Should show "Unknown" for empty/None keys
    assert any("Unknown: 1" in line for line in lines)

def test_independent_histogram_lines():
    # Directly test _get_town_histogram_lines
    histogram = {"A": 2, "B": 1}
    lines = summary_formatter._get_town_histogram_lines(histogram, max_rows=1)
    assert lines[0] == "  A: 2"
    assert lines[1].startswith("  ... (1 more towns)")
def test_get_project_summary_lines_with_project_config():
    from address_bundler import summary_formatter

    class DummyProject:
        def __init__(self):
            self.config = {
                "school_name": "Test School",
                "bundle_size": 42,
                "min_bundle_size": 7,
            }

    summary = {
        "num_students": 10,
        "town_histogram": {"TownA": 5, "TownB": 5},
        "num_geocoded": 8,
        "num_students_total": 10,
        "clustering_run": True,
        "maps_generated": True,
        "pdfs_generated": False,
    }
    project = DummyProject()
    lines = summary_formatter.get_project_summary_lines(summary, project=project)
    assert any("School name: Test School" in line for line in lines)
    assert any("Bundle size: 42" in line for line in lines)
    assert any("Min bundle size: 7" in line for line in lines)