import pytest
import os
import tempfile
import csv
import shutil
from unittest.mock import patch, MagicMock
from lawn_signs.import_photos import (
    find_matching_student,
    parse_student_name,
    import_photos,
    MatchResult,
    is_blank_row
)
from common.models import Student


class MockStudentDoesNotExist(Exception):
    """Mock exception class for Student.DoesNotExist."""
    pass


class TestParseStudentName:
    """Test student name parsing functionality."""
    
    def test_parse_full_name(self):
        """Test parsing a standard first and last name."""
        first, last = parse_student_name("John Smith")
        assert first == "John"
        assert last == "Smith"
    
    def test_parse_multiple_last_names(self):
        """Test parsing names with multiple last name parts."""
        first, last = parse_student_name("Mary Jane Watson")
        assert first == "Mary"
        assert last == "Jane Watson"
    
    def test_parse_single_name(self):
        """Test parsing a single name."""
        first, last = parse_student_name("Madonna")
        assert first == "Madonna"
        assert last == ""
    
    def test_parse_empty_name(self):
        """Test parsing empty or whitespace-only names."""
        first, last = parse_student_name("")
        assert first == ""
        assert last == ""
        
        first, last = parse_student_name("   ")
        assert first == ""
        assert last == ""


class TestFindMatchingStudent:
    """Test student matching functionality."""
    
    @patch('lawn_signs.import_photos.Student')
    def test_exact_match_found(self, mock_student_class):
        """Test exact match is found and returned."""
        mock_student = MagicMock()
        mock_student_class.get.return_value = mock_student
        
        result = find_matching_student("John", "Smith", 80)
        
        assert result.match_type == 'exact'
        assert result.student == mock_student
        assert result.score is None
        assert result.matched_name is None
    
    @patch('lawn_signs.import_photos.Student')
    def test_no_exact_match_no_fuzzy_match(self, mock_student_class):
        """Test when no exact match and no fuzzy matches meet threshold."""
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        mock_student_class.select.return_value = []
        
        result = find_matching_student("John", "Smith", 80)
        
        assert result.match_type == 'none'
        assert result.student is None
    
    @patch('lawn_signs.import_photos.Student')
    def test_fuzzy_match_single_result(self, mock_student_class):
        """Test single fuzzy match above threshold."""
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        mock_student = MagicMock()
        mock_student.first_name = "Johnny"
        mock_student.last_name = "Smith"
        mock_student_class.select.return_value = [mock_student]
        
        result = find_matching_student("John", "Smith", 80)
        
        assert result.match_type == 'fuzzy'
        assert result.student == mock_student
        assert result.score >= 80
        assert result.matched_name == "Johnny Smith"
    
    @patch('lawn_signs.import_photos.Student')
    def test_fuzzy_match_multiple_results_ambiguous(self, mock_student_class):
        """Test multiple fuzzy matches above threshold are marked ambiguous."""
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        mock_student1 = MagicMock()
        mock_student1.first_name = "Johnny"
        mock_student1.last_name = "Smith"
        
        mock_student2 = MagicMock()
        mock_student2.first_name = "John"
        mock_student2.last_name = "Smyth"
        
        mock_student_class.select.return_value = [mock_student1, mock_student2]
        
        result = find_matching_student("John", "Smith", 80)
        
        assert result.match_type == 'ambiguous'
        assert result.student is None
    
    @patch('lawn_signs.import_photos.Student')
    def test_fuzzy_match_below_threshold(self, mock_student_class):
        """Test fuzzy matches below threshold are ignored."""
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        mock_student = MagicMock()
        mock_student.first_name = "Bob"
        mock_student.last_name = "Jones"
        mock_student_class.select.return_value = [mock_student]
        
        result = find_matching_student("John", "Smith", 80)
        
        assert result.match_type == 'none'
        assert result.student is None


class TestIsBlankRow:
    """Test blank row detection."""
    
    def test_completely_empty_row(self):
        """Test row with all empty values."""
        row = {"Name": "", "Filename": "", "Other": ""}
        assert is_blank_row(row) is True
    
    def test_whitespace_only_row(self):
        """Test row with only whitespace values."""
        row = {"Name": "   ", "Filename": "\t", "Other": "\n"}
        assert is_blank_row(row) is True
    
    def test_row_with_data(self):
        """Test row with actual data."""
        row = {"Name": "John Smith", "Filename": "", "Other": ""}
        assert is_blank_row(row) is False
    
    def test_mixed_blank_and_data(self):
        """Test row with some blank and some data."""
        row = {"Name": "", "Filename": "photo.jpg", "Other": ""}
        assert is_blank_row(row) is False


class TestImportPhotosIntegration:
    """Integration tests for the main import_photos function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.temp_dir, "test.csv")
        self.photos_dir = os.path.join(self.temp_dir, "photos")
        os.makedirs(self.photos_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_csv(self, rows):
        """Helper to create test CSV files."""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Filename"])
            writer.writeheader()
            writer.writerows(rows)
    
    def create_test_photo(self, filename):
        """Helper to create test photo files."""
        photo_path = os.path.join(self.photos_dir, filename)
        with open(photo_path, 'wb') as f:
            f.write(b"fake image data")
        return photo_path
    
    @patch('lawn_signs.import_photos.get_project')
    @patch('lawn_signs.import_photos.Student')
    def test_invalid_fuzzy_threshold(self, mock_student_class, mock_get_project):
        """Test that invalid fuzzy thresholds raise ValueError."""
        mock_get_project.return_value.get_directory.return_value = self.temp_dir
        self.create_test_csv([{"Name": "John Smith", "Filename": ""}])
        
        with pytest.raises(ValueError, match="Fuzzy threshold must be between 0 and 100"):
            import_photos(self.csv_file, self.photos_dir, fuzzy_threshold=150)
        
        with pytest.raises(ValueError, match="Fuzzy threshold must be between 0 and 100"):
            import_photos(self.csv_file, self.photos_dir, fuzzy_threshold=-10)
    
    @patch('lawn_signs.import_photos.get_project')
    @patch('lawn_signs.import_photos.Student')
    def test_missing_csv_columns(self, mock_student_class, mock_get_project):
        """Test error handling for missing CSV columns."""
        mock_get_project.return_value.get_directory.return_value = self.temp_dir
        
        # Create CSV with wrong column names
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Student", "Photo"])
            writer.writeheader()
            writer.writerow({"Student": "John Smith", "Photo": "photo.jpg"})
        
        with pytest.raises(ValueError, match="Name column 'Name' not found in CSV"):
            import_photos(self.csv_file, self.photos_dir)
    
    @patch('lawn_signs.import_photos.get_project')
    @patch('lawn_signs.import_photos.Student')
    @patch('builtins.print')
    def test_fuzzy_match_reporting(self, mock_print, mock_student_class, mock_get_project):
        """Test that fuzzy matches are properly reported."""
        mock_get_project.return_value.get_directory.return_value = self.temp_dir
        self.create_test_csv([{"Name": "John Smith", "Filename": ""}])
        
        # Mock exact match failure
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        # Mock fuzzy match success
        mock_student = MagicMock()
        mock_student.first_name = "Johnny"
        mock_student.last_name = "Smith"
        mock_student_class.select.return_value = [mock_student]
        
        import_photos(self.csv_file, self.photos_dir, fuzzy_threshold=80)
        
        # Check that fuzzy match was reported
        printed_output = [call[0][0] for call in mock_print.call_args_list]
        fuzzy_reports = [msg for msg in printed_output if "Fuzzy match:" in msg]
        assert len(fuzzy_reports) > 0
        assert "John Smith" in str(fuzzy_reports)
        assert "Johnny Smith" in str(fuzzy_reports)
    
    @patch('lawn_signs.import_photos.get_project')
    @patch('lawn_signs.import_photos.Student')
    @patch('builtins.print')
    def test_ambiguous_match_handling(self, mock_print, mock_student_class, mock_get_project):
        """Test that ambiguous matches are properly handled and reported."""
        mock_get_project.return_value.get_directory.return_value = self.temp_dir
        self.create_test_csv([{"Name": "John Smith", "Filename": ""}])
        
        # Mock exact match failure
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        # Mock multiple fuzzy matches
        mock_student1 = MagicMock()
        mock_student1.first_name = "Johnny"
        mock_student1.last_name = "Smith"
        
        mock_student2 = MagicMock()
        mock_student2.first_name = "John"
        mock_student2.last_name = "Smyth"
        
        mock_student_class.select.return_value = [mock_student1, mock_student2]
        
        import_photos(self.csv_file, self.photos_dir, fuzzy_threshold=80)
        
        # Check that ambiguous match was reported
        printed_output = [call[0][0] for call in mock_print.call_args_list]
        ambiguous_reports = [msg for msg in printed_output if "Multiple fuzzy matches" in msg]
        assert len(ambiguous_reports) > 0


class TestNicknameFuzzyMatching:
    """Test fuzzy matching with common nickname variations."""
    
    @patch('lawn_signs.import_photos.Student')
    def test_common_nickname_variations(self, mock_student_class):
        """Test that common nickname variations match with high scores."""
        mock_student_class.DoesNotExist = MockStudentDoesNotExist
        mock_student_class.get.side_effect = MockStudentDoesNotExist()
        
        test_cases = [
            ("Mike", "Michael", "Johnson"),
            ("Charlie", "Charles", "Brown"),
            ("Bob", "Robert", "Wilson"),
            ("Jim", "James", "Davis"),
        ]
        
        for import_first, db_first, last_name in test_cases:
            mock_student = MagicMock()
            mock_student.first_name = db_first
            mock_student.last_name = last_name
            mock_student_class.select.return_value = [mock_student]
            
            result = find_matching_student(import_first, last_name, 70)
            
            # Should find a fuzzy match for common nickname variations
            assert result.match_type in ['fuzzy', 'exact'], f"Failed to match {import_first} with {db_first}"
            if result.match_type == 'fuzzy':
                assert result.score >= 70, f"Score too low for {import_first} → {db_first}: {result.score}"