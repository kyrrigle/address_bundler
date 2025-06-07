import os
import tempfile
import shutil
import csv
import unittest
from unittest.mock import patch, MagicMock
from lawn_signs.import_photos import (
    parse_student_name,
    is_blank_row,
    generate_unique_filename,
    process_photo,
)


class TestImportPhotos(unittest.TestCase):

    def test_parse_student_name(self):
        """Test parsing of student names."""
        # Normal case
        first, last = parse_student_name("John Doe")
        self.assertEqual(first, "John")
        self.assertEqual(last, "Doe")

        # Multiple last names
        first, last = parse_student_name("Mary Jane Smith")
        self.assertEqual(first, "Mary")
        self.assertEqual(last, "Jane Smith")

        # Single name
        first, last = parse_student_name("Madonna")
        self.assertEqual(first, "Madonna")
        self.assertEqual(last, "")

        # Empty name
        first, last = parse_student_name("")
        self.assertEqual(first, "")
        self.assertEqual(last, "")

    def test_is_blank_row(self):
        """Test detection of blank rows."""
        # Completely blank row
        self.assertTrue(is_blank_row({"Name": "", "Filename": ""}))

        # Row with whitespace only
        self.assertTrue(is_blank_row({"Name": "  ", "Filename": "\t"}))

        # Row with data
        self.assertFalse(is_blank_row({"Name": "John", "Filename": ""}))

        # Row with filename only
        self.assertFalse(is_blank_row({"Name": "", "Filename": "photo.jpg"}))

    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No existing file
            unique = generate_unique_filename("test.jpg", temp_dir)
            self.assertEqual(unique, "test.jpg")

            # Create the file
            with open(os.path.join(temp_dir, "test.jpg"), "w") as f:
                f.write("test")

            # Should generate unique name
            unique = generate_unique_filename("test.jpg", temp_dir)
            self.assertEqual(unique, "test_1.jpg")

            # Create that one too
            with open(os.path.join(temp_dir, "test_1.jpg"), "w") as f:
                f.write("test")

            # Should generate another unique name
            unique = generate_unique_filename("test.jpg", temp_dir)
            self.assertEqual(unique, "test_2.jpg")

    def test_process_photo(self):
        """Test photo processing and copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source and destination directories
            source_dir = os.path.join(temp_dir, "source")
            dest_dir = os.path.join(temp_dir, "dest")
            os.makedirs(source_dir)
            os.makedirs(dest_dir)

            # Create a test photo
            source_photo = os.path.join(source_dir, "test.jpg")
            with open(source_photo, "w") as f:
                f.write("test photo content")

            # Process the photo
            result = process_photo("test.jpg", source_dir, dest_dir)

            # Check result
            self.assertEqual(result, "test.jpg")
            self.assertTrue(os.path.exists(os.path.join(dest_dir, "test.jpg")))

            # Test with non-existent file
            result = process_photo("missing.jpg", source_dir, dest_dir)
            self.assertIsNone(result)

    def test_process_photo_duplicate_content_vs_different_content(self):
        """Test that process_photo only generates a new filename if contents differ."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = os.path.join(temp_dir, "source")
            dest_dir = os.path.join(temp_dir, "dest")
            os.makedirs(source_dir)
            os.makedirs(dest_dir)

            # Create a photo in source and copy to dest
            photo_name = "student.jpg"
            content1 = b"photo content 123"
            source_photo = os.path.join(source_dir, photo_name)
            with open(source_photo, "wb") as f:
                f.write(content1)
            # First copy: should use original name
            result1 = process_photo(photo_name, source_dir, dest_dir)
            self.assertEqual(result1, photo_name)
            self.assertTrue(os.path.exists(os.path.join(dest_dir, photo_name)))

            # Second copy, identical content: should NOT create a new file
            result2 = process_photo(photo_name, source_dir, dest_dir)
            self.assertEqual(result2, photo_name)
            # Only one file should exist
            self.assertEqual(
                len([f for f in os.listdir(dest_dir) if f.startswith("student")]), 1
            )

            # Now, overwrite source with different content
            content2 = b"DIFFERENT content"
            with open(source_photo, "wb") as f:
                f.write(content2)
            # Third copy, different content: should create a new file
            result3 = process_photo(photo_name, source_dir, dest_dir)
            self.assertNotEqual(result3, photo_name)
            self.assertTrue(os.path.exists(os.path.join(dest_dir, result3)))
            # There should now be two files
            self.assertEqual(
                len([f for f in os.listdir(dest_dir) if f.startswith("student")]), 2
            )


if __name__ == "__main__":
    unittest.main()
