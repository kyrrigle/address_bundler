import os
from typing import List, Tuple, Optional
from PIL import Image
from common.project import get_project
from common.models import Student


def validate_student_images(min_resolution: int = 1000000) -> None:
    """
    Validate all student images and update their validation status.
    
    Args:
        min_resolution: Minimum total pixels required (width * height)
    """
    project = get_project()
    originals_dir = os.path.join(project.get_directory(), "originals")
    
    if not os.path.exists(originals_dir):
        print("No originals directory found - no images to validate")
        return
    
    students = Student.select().where(Student.image_name.is_null(False))
    
    validated_count = 0
    valid_count = 0
    invalid_count = 0
    
    for student in students:
        validation_result = validate_student_image(student, originals_dir, min_resolution)
        
        if validation_result.is_valid:
            student.image_valid = 'valid'
            valid_count += 1
        else:
            student.image_valid = 'invalid'
            invalid_count += 1
            # Report invalid image
            print(f"INVALID: {student.first_name} {student.last_name} - {student.image_name} - {validation_result.reason}")
        
        student.save()
        validated_count += 1
    
    print(f"\nValidation completed:")
    print(f"  - Total validated: {validated_count}")
    print(f"  - Valid images: {valid_count}")
    print(f"  - Invalid images: {invalid_count}")


class ValidationResult:
    """Result of image validation."""
    
    def __init__(self, is_valid: bool, reason: Optional[str] = None):
        self.is_valid = is_valid
        self.reason = reason


def validate_student_image(student: Student, originals_dir: str, min_resolution: int) -> ValidationResult:
    """
    Validate a single student's image.
    
    Args:
        student: Student record with image_name
        originals_dir: Directory containing original images
        min_resolution: Minimum total pixels required
        
    Returns:
        ValidationResult indicating if image is valid and reason if not
    """
    if not student.image_name:
        return ValidationResult(False, "No image file specified")
    
    image_path = os.path.join(originals_dir, student.image_name)
    
    # Check if file exists
    if not os.path.exists(image_path):
        return ValidationResult(False, "Image file not found")
    
    try:
        # Try to open and validate the image
        with Image.open(image_path) as img:
            # Verify it's a supported format
            if img.format not in ['JPEG', 'PNG']:
                return ValidationResult(False, f"Unsupported format: {img.format}")
            
            # Check resolution
            width, height = img.size
            total_pixels = width * height
            
            if total_pixels < min_resolution:
                return ValidationResult(False, f"Resolution too low: {width}x{height} ({total_pixels} pixels, minimum {min_resolution})")
            
            # If we get here, image is valid
            return ValidationResult(True)
            
    except Exception as e:
        return ValidationResult(False, f"Cannot read image file: {str(e)}")


def reset_validation_status(student: Student) -> None:
    """
    Reset a student's image validation status to 'unknown'.
    Called when image is updated/changed.
    
    Args:
        student: Student record to reset
    """
    student.image_valid = 'unknown'
    student.save()