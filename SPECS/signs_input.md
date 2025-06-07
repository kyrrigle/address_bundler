# Functional Specification: Signs input

## Overview

In order to start working on the signs, a list of student names and photos need to be imported into the project.
This is done using the following command:

    ab-signs import <csv-file> <photos-directory> [--name-column NAME] [--filename-column NAME] [--fuzzy-threshold SCORE]

Once imported, the database has been updated creating student records when needed and setting the filename.
The project folder will have an `originals/` directory to hold the original photos.

## Functional Requirements

### 1. Inputs

The csv file and directory of photos supplied on the command line, with optional fuzzy matching threshold parameter.

### 2. Outputs

- The database has been updated
- There is a new column called `image_name` that will be the filename within the `<project>/originals/`
- The photos will be copied to `<project>/originals` directory (which may need to be created)
- Fuzzy name matches are reported during import with match scores

### 3. Name Matching Logic

- **Exact Match**: First attempt exact match on first_name + last_name combination
- **Fuzzy Match**: If no exact match found, perform fuzzy matching using fuzzywuzzy library
- **Fuzzy Threshold**: Configurable score threshold (default: 80) for determining valid fuzzy matches
- **Match Reporting**: All fuzzy matches should be reported with the match score and both name versions
- **Name Updates**: On fuzzy match, update the existing student record to use the new name from the import file

### 4. Constraints

- Student records in the database may already exist, the photo being imported should replace the existing in originals if there is one
- Photo names should be unique
- The csv file does not need to specify a photo for every student. The image_name column should be left null in this case
- Blank rows (no student name or image) should be silently skipped
- Student names are required. Report on any rows that are missing a student name
- Fuzzy matching should handle common nickname variations (e.g., "Charlie" ↔ "Charles", "Mike" ↔ "Michael")
- Only one fuzzy match per import name should be accepted (highest scoring match above threshold)
- If multiple database records match above the fuzzy threshold, report the ambiguity and skip the import for that name

### 5. Fuzzy Matching Requirements

- Use fuzzywuzzy library for string similarity scoring
- Compare full names (first_name + " " + last_name) for fuzzy matching
- Configurable threshold via command line parameter `--fuzzy-threshold` (range: 0-100, default: 80)
- Report format: "Fuzzy match: 'Import Name' → 'Database Name' (score: XX)"
- Update existing student record with the import file's name version on successful fuzzy match

## Notes

- Code should be modular and testable
- Create test cases as you go
- Fuzzy matching adds complexity - ensure thorough testing of edge cases
- Consider performance implications when fuzzy matching against large student databases (max expected size 1000 students)
