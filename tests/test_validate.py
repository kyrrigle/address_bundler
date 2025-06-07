import os
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from lawn_signs.validate import (
    validate_student_images,
    validate_student_image,
    reset_validation_status,
    ValidationResult
)
from common.models import Student


class TestValidationResult:
    """Test the ValidationResult class."""
    
    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(True)
        assert result.is_valid is True
        assert result.reason is None
    
    def test_invalid_result_with_reason(self):
        """Test creating an invalid result with reason."""
        reason = "File not found"
        result = ValidationResult(False, reason)
        assert result.is_valid is False
        assert result.reason == reason
    
    def test_invalid_result_without_reason(self):
        """Test creating an invalid result without reason."""
        result = ValidationResult(False)
        assert result.is_valid is False
        assert result.reason is None


class TestValidateStudentImage:
    """Test the validate_student_image function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.student = Mock(spec=Student)
        self.student.image_name = "test_image.jpg"
        self.min_resolution = 1000000
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_image(self, filename, width=1200, height=1000, format='JPEG'):
        """Helper to create test images."""
        image_path = os.path.join(self.temp_dir, filename)
        image = Image.new('RGB', (width, height), color='red')
        image.save(image_path, format=format)
        return image_path
    
    def test_no_image_name(self):
        """Test validation when student has no image name."""
        self.student.image_name = None
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert result.reason == "No image file specified"
    
    def test_empty_image_name(self):
        """Test validation when student has empty image name."""
        self.student.image_name = ""
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert result.reason == "No image file specified"
    
    def test_image_file_not_found(self):
        """Test validation when image file doesn't exist."""
        self.student.image_name = "nonexistent.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert result.reason == "Image file not found"
    
    def test_valid_jpeg_image(self):
        """Test validation of valid JPEG image."""
        self.create_test_image("test.jpg", 1200, 1000, 'JPEG')
        self.student.image_name = "test.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert result.is_valid
        assert result.reason is None
    
    def test_valid_png_image(self):
        """Test validation of valid PNG image."""
        self.create_test_image("test.png", 1200, 1000, 'PNG')
        self.student.image_name = "test.png"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert result.is_valid
        assert result.reason is None
    
    def test_unsupported_format(self):
        """Test validation of unsupported image format."""
        # Create a GIF image (unsupported format)
        image_path = os.path.join(self.temp_dir, "test.gif")
        image = Image.new('RGB', (1200, 1000), color='red')
        image.save(image_path, format='GIF')
        
        self.student.image_name = "test.gif"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert "Unsupported format: GIF" in result.reason
    
    def test_resolution_too_low(self):
        """Test validation when image resolution is too low."""
        # Create image with resolution below minimum
        self.create_test_image("low_res.jpg", 800, 600, 'JPEG')  # 480,000 pixels
        self.student.image_name = "low_res.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert "Resolution too low" in result.reason
        assert "800x600 (480000 pixels, minimum 1000000)" in result.reason
    
    def test_resolution_exactly_minimum(self):
        """Test validation when image resolution exactly meets minimum."""
        # Create image with exactly minimum resolution
        self.create_test_image("exact.jpg", 1000, 1000, 'JPEG')  # 1,000,000 pixels
        self.student.image_name = "exact.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert result.is_valid
        assert result.reason is None
    
    def test_custom_minimum_resolution(self):
        """Test validation with custom minimum resolution."""
        # Create image that's valid for lower threshold but not higher
        self.create_test_image("medium.jpg", 800, 600, 'JPEG')  # 480,000 pixels
        self.student.image_name = "medium.jpg"
        
        # Should be valid with low threshold
        result = validate_student_image(self.student, self.temp_dir, 400000)
        assert result.is_valid
        
        # Should be invalid with high threshold
        result = validate_student_image(self.student, self.temp_dir, 500000)
        assert not result.is_valid
        assert "Resolution too low" in result.reason
    
    def test_corrupted_image_file(self):
        """Test validation when image file is corrupted."""
        # Create a file that's not a valid image
        corrupt_path = os.path.join(self.temp_dir, "corrupt.jpg")
        with open(corrupt_path, 'w') as f:
            f.write("This is not an image file")
        
        self.student.image_name = "corrupt.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert "Cannot read image file" in result.reason
    
    @patch('lawn_signs.validate.Image.open')
    def test_image_open_exception(self, mock_open):
        """Test validation when Image.open raises an exception."""
        mock_open.side_effect = IOError("Test error")
        
        # Create a real file so file existence check passes
        test_path = os.path.join(self.temp_dir, "test.jpg")
        with open(test_path, 'w') as f:
            f.write("dummy content")
        
        self.student.image_name = "test.jpg"
        result = validate_student_image(self.student, self.temp_dir, self.min_resolution)
        assert not result.is_valid
        assert "Cannot read image file: Test error" in result.reason


class TestResetValidationStatus:
    """Test the reset_validation_status function."""
    
    def test_reset_validation_status(self):
        """Test resetting a student's validation status."""
        student = Mock(spec=Student)
        student.image_valid = 'valid'
        
        reset_validation_status(student)
        
        assert student.image_valid == 'unknown'
        student.save.assert_called_once()


class TestValidateStudentImages:
    """Test the validate_student_images function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = tempfile.mkdtemp()
        self.originals_dir = os.path.join(self.project_dir, "originals")
        os.makedirs(self.originals_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.project_dir, ignore_errors=True)
    
    def create_test_image(self, filename, width=1200, height=1000, format='JPEG'):
        """Helper to create test images in originals directory."""
        image_path = os.path.join(self.originals_dir, filename)
        image = Image.new('RGB', (width, height), color='red')
        image.save(image_path, format=format)
        return image_path
    
    @patch('lawn_signs.validate.get_project')
    @patch('lawn_signs.validate.Student.select')
    def test_no_originals_directory(self, mock_select, mock_get_project, capsys):
        """Test validation when originals directory doesn't exist."""
        # Mock project to return directory without originals
        mock_project = Mock()
        mock_project.get_directory.return_value = self.temp_dir
        mock_get_project.return_value = mock_project
        
        validate_student_images()
        
        captured = capsys.readouterr()
        assert "No originals directory found - no images to validate" in captured.out
        mock_select.assert_not_called()
    
    @patch('lawn_signs.validate.get_project')
    @patch('lawn_signs.validate.Student.select')
    def test_no_students_with_images(self, mock_select, mock_get_project, capsys):
        """Test validation when no students have images."""
        # Mock project
        mock_project = Mock()
        mock_project.get_directory.return_value = self.project_dir
        mock_get_project.return_value = mock_project
        
        # Mock empty student query
        mock_query = Mock()
        mock_query.where.return_value = []
        mock_select.return_value = mock_query
        
        validate_student_images()
        
        captured = capsys.readouterr()
        assert "Total validated: 0" in captured.out
        assert "Valid images: 0" in captured.out
        assert "Invalid images: 0" in captured.out
    
    @patch('lawn_signs.validate.get_project')
    @patch('lawn_signs.validate.Student.select')
    def test_validate_mixed_students(self, mock_select, mock_get_project, capsys):
        """Test validation with mix of valid and invalid students."""
        # Mock project
        mock_project = Mock()
        mock_project.get_directory.return_value = self.project_dir
        mock_get_project.return_value = mock_project
        
        # Create test images
        self.create_test_image("valid.jpg", 1200, 1000, 'JPEG')
        self.create_test_image("invalid.jpg", 800, 600, 'JPEG')  # Too small
        
        # Create mock students
        valid_student = Mock(spec=Student)
        valid_student.first_name = "John"
        valid_student.last_name = "Doe"
        valid_student.image_name = "valid.jpg"
        
        invalid_student = Mock(spec=Student)
        invalid_student.first_name = "Jane"
        invalid_student.last_name = "Smith"
        invalid_student.image_name = "invalid.jpg"
        
        missing_student = Mock(spec=Student)
        missing_student.first_name = "Bob"
        missing_student.last_name = "Johnson"
        missing_student.image_name = "missing.jpg"
        
        # Mock student query
        mock_query = Mock()
        mock_query.where.return_value = [valid_student, invalid_student, missing_student]
        mock_select.return_value = mock_query
        
        validate_student_images(min_resolution=1000000)
        
        # Check that students were updated correctly
        assert valid_student.image_valid == 'valid'
        assert invalid_student.image_valid == 'invalid'
        assert missing_student.image_valid == 'invalid'
        
        # Check that save was called on all students
        valid_student.save.assert_called_once()
        invalid_student.save.assert_called_once()
        missing_student.save.assert_called_once()
        
        # Check output
        captured = capsys.readouterr()
        assert "Total validated: 3" in captured.out
        assert "Valid images: 1" in captured.out
        assert "Invalid images: 2" in captured.out
        assert "INVALID: Jane Smith - invalid.jpg - Resolution too low" in captured.out
        assert "INVALID: Bob Johnson - missing.jpg - Image file not found" in captured.out
    
    @patch('lawn_signs.validate.get_project')
    @patch('lawn_signs.validate.Student.select')
    def test_validate_with_custom_resolution(self, mock_select, mock_get_project, capsys):
        """Test validation with custom minimum resolution."""
        # Mock project
        mock_project = Mock()
        mock_project.get_directory.return_value = self.project_dir
        mock_get_project.return_value = mock_project
        
        # Create test image that's valid for lower resolution
        self.create_test_image("medium.jpg", 800, 600, 'JPEG')  # 480,000 pixels
        
        # Create mock student
        student = Mock(spec=Student)
        student.first_name = "Test"
        student.last_name = "User"
        student.image_name = "medium.jpg"
        
        # Mock student query
        mock_query = Mock()
        mock_query.where.return_value = [student]
        mock_select.return_value = mock_query
        
        # Test with lower resolution requirement
        validate_student_images(min_resolution=400000)
        
        assert student.image_valid == 'valid'
        student.save.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Valid images: 1" in captured.out
        assert "Invalid images: 0" in captured.out
    
    @patch('lawn_signs.validate.get_project')
    @patch('lawn_signs.validate.Student.select')
    @patch('lawn_signs.validate.validate_student_image')
    def test_validation_exception_handling(self, mock_validate, mock_select, mock_get_project, capsys):
        """Test that exceptions during validation are handled gracefully."""
        # Mock project
        mock_project = Mock()
        mock_project.get_directory.return_value = self.project_dir
        mock_get_project.return_value = mock_project
        
        # Create mock student
        student = Mock(spec=Student)
        student.first_name = "Test"
        student.last_name = "User"
        student.image_name = "test.jpg"
        
        # Mock student query
        mock_query = Mock()
        mock_query.where.return_value = [student]
        mock_select.return_value = mock_query
        
        # Mock validation to raise exception
        mock_validate.side_effect = Exception("Test exception")
        
        # This should not crash
        with pytest.raises(Exception, match="Test exception"):
            validate_student_images()