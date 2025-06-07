import os
import shutil
import csv
from typing import Optional, Tuple, List, NamedTuple
from fuzzywuzzy import fuzz
from common.project import get_project
from common.models import Student


class MatchResult(NamedTuple):
    """Result of student name matching attempt."""
    student: Optional[Student]
    match_type: str  # 'exact', 'fuzzy', 'none', 'ambiguous'
    score: Optional[int] = None
    matched_name: Optional[str] = None


def import_photos(csv_file: str, photos_directory: str, name_column: str = "Name",
                 filename_column: str = "Filename", fuzzy_threshold: int = 80) -> None:
    """
    Import student photos from CSV file and photos directory.
    
    Args:
        csv_file: Path to CSV file containing student data
        photos_directory: Directory containing photo files
        name_column: Column name for student names in CSV
        filename_column: Column name for photo filenames in CSV
        fuzzy_threshold: Minimum score for fuzzy matching (0-100, default: 80)
    """
    project = get_project()
    originals_dir = os.path.join(project.get_directory(), "originals")
    
    # Create originals directory if it doesn't exist
    os.makedirs(originals_dir, exist_ok=True)
    
    # Validate inputs
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    if not os.path.exists(photos_directory):
        raise FileNotFoundError(f"Photos directory not found: {photos_directory}")
    
    if not (0 <= fuzzy_threshold <= 100):
        raise ValueError(f"Fuzzy threshold must be between 0 and 100, got: {fuzzy_threshold}")
    
    # Process CSV file
    processed_count = 0
    skipped_count = 0
    fuzzy_matches = []
    ambiguous_matches = []
    missing_names = []
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Validate required columns exist
        if name_column not in reader.fieldnames:
            raise ValueError(f"Name column '{name_column}' not found in CSV. Available columns: {list(reader.fieldnames)}")
        
        if filename_column not in reader.fieldnames:
            raise ValueError(f"Filename column '{filename_column}' not found in CSV. Available columns: {list(reader.fieldnames)}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            # Skip blank rows
            if is_blank_row(row):
                skipped_count += 1
                continue
            
            # Extract student name and filename
            student_name = row[name_column].strip() if row[name_column] else ""
            filename = row[filename_column].strip() if row[filename_column] else ""
            
            # Check for missing student name
            if not student_name:
                missing_names.append(f"Row {row_num}: Missing student name")
                continue
            
            # Parse student name
            first_name, last_name = parse_student_name(student_name)
            
            # Find matching student record
            match_result = find_matching_student(first_name, last_name, fuzzy_threshold)
            
            # Handle different match types
            if match_result.match_type == 'ambiguous':
                ambiguous_matches.append(f"Row {row_num}: Multiple fuzzy matches for '{student_name}' - skipping")
                continue
            elif match_result.match_type == 'fuzzy':
                fuzzy_matches.append(f"Row {row_num}: Fuzzy match: '{student_name}' → '{match_result.matched_name}' (score: {match_result.score})")
            
            # Process photo if filename is provided
            image_name = None
            if filename:
                image_name = process_photo(filename, photos_directory, originals_dir)
                if image_name is None:
                    print(f"Warning: Photo file '{filename}' not found for student '{student_name}'")
            
            # Update or create student record
            update_student_record(match_result, first_name, last_name, image_name, student_name)
            processed_count += 1
    
    # Report results
    print("Import completed:")
    print(f"  - Processed: {processed_count} students")
    print(f"  - Skipped blank rows: {skipped_count}")
    
    if fuzzy_matches:
        print(f"  - Fuzzy matches: {len(fuzzy_matches)}")
        for match in fuzzy_matches:
            print(f"    {match}")
    
    if ambiguous_matches:
        print(f"  - Ambiguous matches (skipped): {len(ambiguous_matches)}")
        for match in ambiguous_matches:
            print(f"    {match}")
    
    if missing_names:
        print(f"  - Rows with missing student names: {len(missing_names)}")
        for missing in missing_names:
            print(f"    {missing}")


def is_blank_row(row: dict) -> bool:
    """Check if a CSV row is effectively blank (no meaningful data)."""
    return all(not str(value).strip() for value in row.values())


def parse_student_name(full_name: str) -> Tuple[str, str]:
    """
    Parse a full name into first and last name.
    Assumes format "First Last" or handles single names.
    """
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    elif len(parts) == 1:
        return parts[0], ""
    else:
        return "", ""


def find_matching_student(first_name: str, last_name: str, fuzzy_threshold: int) -> MatchResult:
    """
    Find matching student record using exact match first, then fuzzy matching.
    
    Args:
        first_name: Student's first name from import
        last_name: Student's last name from import
        fuzzy_threshold: Minimum score for fuzzy matching
        
    Returns:
        MatchResult with student and match details
    """
    import_full_name = f"{first_name} {last_name}".strip()
    
    # Try exact match first
    try:
        student = Student.get(
            (Student.first_name == first_name) &
            (Student.last_name == last_name)
        )
        return MatchResult(student=student, match_type='exact')
    except Student.DoesNotExist:
        pass
    
    # Try fuzzy matching
    all_students = list(Student.select())
    fuzzy_matches = []
    
    for student in all_students:
        db_full_name = f"{student.first_name} {student.last_name}".strip()
        score = fuzz.ratio(import_full_name.lower(), db_full_name.lower())
        
        if score >= fuzzy_threshold:
            fuzzy_matches.append((student, score, db_full_name))
    
    if len(fuzzy_matches) == 0:
        return MatchResult(student=None, match_type='none')
    elif len(fuzzy_matches) == 1:
        student, score, db_name = fuzzy_matches[0]
        return MatchResult(student=student, match_type='fuzzy', score=score, matched_name=db_name)
    else:
        # Multiple matches - this is ambiguous
        return MatchResult(student=None, match_type='ambiguous')


def process_photo(filename: str, photos_directory: str, originals_dir: str) -> Optional[str]:
    """
    Copy photo from source directory to originals directory.

    Args:
        filename: Name of the photo file
        photos_directory: Source directory containing photos
        originals_dir: Destination directory for copied photos

    Returns:
        The filename in originals directory, or None if source file not found
    """
    source_path = os.path.join(photos_directory, filename)
    destination_path = os.path.join(originals_dir, filename)

    if not os.path.exists(source_path):
        return None

    if os.path.exists(destination_path):
        # Compare contents
        if files_are_identical(source_path, destination_path):
            # Contents are the same, do not create a new file
            return filename
        else:
            # Contents differ, generate a unique filename
            destination_filename = generate_unique_filename(filename, originals_dir)
            destination_path = os.path.join(originals_dir, destination_filename)
    else:
        destination_filename = filename

    # Copy the file
    shutil.copy2(source_path, destination_path)
    return destination_filename


def generate_unique_filename(filename: str, directory: str) -> str:
    """
    Generate a unique filename in the target directory.
    If the filename already exists, append a number.
    """
    base_name, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    
    return unique_filename


def files_are_identical(path1: str, path2: str, chunk_size: int = 4096) -> bool:
    """
    Compare two files to determine if their contents are identical.

    Args:
        path1: Path to the first file
        path2: Path to the second file
        chunk_size: Number of bytes to read at a time

    Returns:
        True if files are identical, False otherwise
    """
    if os.path.getsize(path1) != os.path.getsize(path2):
        return False

    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        while True:
            b1 = f1.read(chunk_size)
            b2 = f2.read(chunk_size)
            if b1 != b2:
                return False
            if not b1:  # End of file
                return True


def update_student_record(match_result: MatchResult, first_name: str, last_name: str,
                         image_name: Optional[str], original_name: str) -> None:
    """
    Update or create student record with image filename.
    
    Args:
        match_result: Result from find_matching_student
        first_name: Student's first name from import
        last_name: Student's last name from import
        image_name: Filename of the photo in originals directory
        original_name: Original full name from import file
    """
    if match_result.student is not None:
        # Update existing student
        student = match_result.student
        
        # For fuzzy matches, update the name to the import file version
        if match_result.match_type == 'fuzzy':
            student.first_name = first_name
            student.last_name = last_name
            print(f"Updated name and photo for student: '{match_result.matched_name}' → '{original_name}'")
        else:
            print(f"Updated photo for existing student: {first_name} {last_name}")
        
        student.image_name = image_name
        student.save()
    else:
        # Create new student record (address is required, so use placeholder)
        Student.create(
            first_name=first_name,
            last_name=last_name,
            address="",  # Placeholder - will be filled in later
            image_name=image_name
        )
        print(f"Created new student record: {first_name} {last_name}")