import pytest
from address_bundler import summary
from collections import namedtuple

# Minimal mock Student for logic tests
Student = namedtuple("Student", ["address", "latitude", "longitude", "bundle_key"])


def test_compute_town_histogram_full():
    students = [
        Student("123 Main St, Milton, MA 02186", 1.0, 2.0, "A"),
        Student("456 Elm St, Quincy, MA 02169", 3.0, 4.0, "B"),
        Student("789 Oak St, Milton, MA 02186", 5.0, 6.0, None),
        Student("No Town", 7.0, 8.0, None),
    ]
    hist = summary.compute_town_histogram(students)
    assert hist["Milton"] == 2
    assert hist["Quincy"] == 1
    assert hist["Unknown"] == 1


def test_compute_town_histogram_empty():
    students = []
    hist = summary.compute_town_histogram(students)
    assert hist == {}


def test_extract_town_from_address_valid():
    addr = "123 Main St, Milton, MA 02186"
    assert summary.extract_town_from_address(addr) == "Milton"


def test_extract_town_from_address_invalid():
    assert summary.extract_town_from_address("") == "Unknown"
    assert summary.extract_town_from_address(None) == "Unknown"
    assert summary.extract_town_from_address("No commas here") == "Unknown"


def test_is_geocoded_true_false():
    s1 = Student("addr", 1.0, 2.0, None)
    s2 = Student("addr", None, 2.0, None)
    s3 = Student("addr", 1.0, None, None)
    s4 = Student("addr", None, None, None)
    assert summary.is_geocoded(s1) is True
    assert summary.is_geocoded(s2) is False
    assert summary.is_geocoded(s3) is False
    assert summary.is_geocoded(s4) is False


def test_detect_clustering_run():
    s1 = Student("addr", 1.0, 2.0, "A")
    s2 = Student("addr", 1.0, 2.0, None)
    assert summary.detect_clustering_run([s1, s2]) is True
    assert summary.detect_clustering_run([s2]) is False


def test_print_histogram_truncation(capsys):
    # 12 towns, should truncate at 10
    hist = {f"Town{i}": 1 for i in range(12)}
    summary.print_histogram(hist, max_rows=10)
    out = capsys.readouterr().out
    assert "... (2 more towns)" in out
    assert out.count(": 1") == 10


def test_print_histogram_empty(capsys):
    summary.print_histogram({}, max_rows=10)
    out = capsys.readouterr().out
    assert "(No towns found)" in out
