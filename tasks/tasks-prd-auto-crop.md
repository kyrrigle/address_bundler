## Relevant Files

- `lawn_signs/auto_crop.py` - Main module containing auto-crop functionality, face detection logic, fallback center-crop logic, and quality-preserving image processing.
- `tests/test_auto_crop.py` - Unit tests for auto-crop functionality, including center-crop fallback and quality preservation.
- `lawn_signs/main.py` - Updated to include the new auto-crop command interface.
- `common/models.py` - Student model, cropping status tracking, and query for students needing cropping.
- `requirements.txt` or `pyproject.toml` - Updated to include face_recognition dependency.
- `common/migrate_add_cropping_status.py` - Migration script to add cropping_status field to the student table if missing.

### Notes

- The `face_recognition` library requires additional system dependencies (dlib, cmake) that may need separate installation.
- Cropped photos will be stored in a `<project>/cropped` directory structure.
- The system will update the Student model to track cropping status alongside existing validation status.
- Unit tests should typically be placed alongside the code files they are testing.
- Use `pytest` to run tests. Running without a path executes all tests found by the pytest configuration.

## Tasks

- [x] 1.0 Set up dependencies and project structure for auto-crop feature
  - [x] 1.1 Add face_recognition dependency to pyproject.toml
  - [x] 1.2 Update project documentation with system dependency requirements (dlib, cmake)
  - [x] 1.3 Create lawn_signs/auto_crop.py module file
  - [x] 1.4 Create tests/test_auto_crop.py test file
  - [x] 1.5 Add necessary imports (PIL, face_recognition, os, pathlib) to auto_crop.py

- [x] 2.0 Implement face detection and intelligent cropping logic
  - [x] 2.1 Create function to load and detect faces in images using face_recognition library
  - [x] 2.2 Implement intelligent crop calculation that centers on the largest detected face
  - [x] 2.3 Create fallback center-crop logic for images with no detected faces
  - [x] 2.4 Implement aspect ratio validation and crop boundary calculation
  - [x] 2.5 Create image cropping function using PIL that maintains maximum quality
  - [x] 2.6 Add logic to handle multiple faces by selecting the largest/most prominent one
  - [x] 2.7 Implement quality preservation during image processing (avoid unnecessary recompression)
  - [x] 2.8 Review the code created for task 2.0 and add unit tests where needed

- [x] 3.0 Create command interface and integrate with existing CLI
  - [x] 3.1 Add auto-crop command option to lawn_signs/main.py docstring
  - [x] 3.2 Add --aspect-ratio parameter with default value of 0.8
  - [x] 3.3 Implement command parsing logic for auto-crop in main.py
  - [x] 3.4 Create main auto_crop_command function that orchestrates the cropping process
  - [x] 3.5 Add progress reporting and user feedback during batch processing

- [x] 4.0 Update database model to track cropping status
  - [x] 4.2 Add cropping_status field to Student model (e.g., 'not_cropped', 'cropped', 'failed')
  - [x] 4.3 Create database migration or update logic for new fields
  - [x] 4.4 Implement functions to query students that need cropping (validated but not cropped)
  - [x] 4.5 Add database update logic to save cropping results (remember we are not storing a 2nd path for the crop, we just want to put it in a `cropped` directory)

- [ ] 5.0 Implement batch processing and error handling for photo cropping
  - [ ] 5.1 Create function to create cropped directory structure if it doesn't exist
  - [ ] 5.2 Implement batch processing loop that processes all eligible students
  - [ ] 5.3 Add comprehensive error handling for individual photo processing failures
  - [ ] 5.4 Implement detailed logging for debugging while showing user-friendly messages
  - [ ] 5.5 Create result reporting system showing success/failure counts and face detection rates
  - [ ] 5.6 Add graceful continuation when individual photos fail (don't stop entire batch)
  - [ ] 5.7 Implement memory management considerations for processing large batches
  - [ ] 5.8 Add validation to ensure only validated photos are processed for cropping
