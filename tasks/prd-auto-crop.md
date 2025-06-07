# PRD: Auto-Crop Student Photos Feature

## Introduction/Overview

This feature adds an automated photo cropping capability to the lawn signs project that uses facial recognition to intelligently crop student photos to a specific aspect ratio while keeping the subject centered. The feature integrates with the existing validation system and processes all validated photos that haven't been cropped yet.

The goal is to standardize student portrait photos for lawn signs by automatically cropping them to the desired dimensions while maintaining focus on the student's face, reducing manual photo editing work.

## Goals

1. Automatically crop validated student photos to a configurable aspect ratio (default 0.8 width/height)
2. Use facial recognition to center crops around the student's face for optimal portrait composition
3. Maintain maximum image quality and resolution during the cropping process
4. Integrate seamlessly with the existing validation workflow
5. Handle edge cases gracefully (no face detected, multiple faces, processing errors)
6. Provide clear feedback on processing results and any issues encountered

## User Stories

**As a project coordinator**, I want to automatically crop all validated student photos to a consistent aspect ratio so that the lawn signs have a uniform appearance without manual photo editing.

**As a project coordinator**, I want the cropping to intelligently center on the student's face so that the portraits look professional and properly composed.

**As a project coordinator**, I want to be able to configure the aspect ratio for different lawn sign designs so that I can accommodate various layout requirements.

**As a project coordinator**, I want the system to handle photos without detectable faces gracefully so that I can still get usable cropped images even if facial recognition fails.

**As a project coordinator**, I want to see clear reports of which photos were processed successfully and which encountered issues so that I can address any problems manually.

## Functional Requirements

1. **Command Interface**: The system must provide a command `ab-signs auto-crop [--aspect-ratio R]` where R is the width/height ratio (default 0.8).

2. **Face Detection**: The system must use the Python `face_recognition` library to detect faces in student photos.

3. **Intelligent Cropping**: When a face is detected, the system must crop the image to center the face within the specified aspect ratio bounds.

4. **Multiple Face Handling**: When multiple faces are detected, the system must use the largest/most prominent face as the focal point for cropping.

5. **Fallback Cropping**: When no face is detected, the system must report this condition and fall back to center cropping of the image.

6. **File Processing**: The system must process only validated photos that have not yet been cropped.

7. **Output Management**: Cropped photos must be saved to a `<project>/cropped` folder using the original filename.

8. **Quality Preservation**: The system must maintain the highest possible resolution and image quality during the cropping process.

9. **Status Tracking**: The system must update the validation status to track which photos have been successfully cropped.

10. **Error Handling**: The system must continue processing remaining photos when individual photos fail, providing clear error messages for each failure.

11. **Progress Reporting**: The system must provide feedback on processing progress and results, including counts of successful crops, fallback crops, and failures.

## Non-Goals (Out of Scope)

- Manual photo editing or correction capabilities
- Preview or confirmation modes before processing
- Batch processing of specific subsets of students (processes all eligible photos)
- Support for custom crop positioning or manual face selection
- Image enhancement or color correction features
- Support for non-rectangular crop shapes
- Undo functionality for cropped photos

## Design Considerations

- The cropped photos directory structure should mirror the project organization
- Error messages should be clear and actionable for non-technical users
- The aspect ratio parameter should accept decimal values (e.g., 0.8, 1.0, 1.33)
- Face detection confidence thresholds should be reasonable to avoid false positives while catching most faces

## Technical Considerations

- **Dependencies**: Requires Python `face_recognition` library installation
- **Integration**: Should integrate with existing `common/models.py` for status tracking
- **Database Updates**: Must update student records with cropping status and file paths
- **File System**: Should create the `cropped` directory if it doesn't exist
- **Memory Management**: Consider memory usage for batch processing large numbers of high-resolution photos
- **Image Processing**: Use PIL/Pillow for image manipulation to maintain quality
- **Error Logging**: Should log detailed error information for debugging while showing user-friendly messages

## Success Metrics

- **Processing Success Rate**: 95%+ of validated photos should be successfully cropped
- **Face Detection Rate**: 85%+ of photos should have successful face detection (remainder use fallback)
- **Quality Preservation**: Cropped photos should maintain at least 90% of original resolution where possible
- **Performance**: Process photos at a rate of at least 1 photo per 2 seconds on average hardware
- **Error Recovery**: System should complete processing even if 10-20% of individual photos fail

## Open Questions

1. Should there be a maximum file size limit for processing to prevent memory issues?
2. Do we need to preserve EXIF data in the cropped photos?
3. Should the system support different face detection models for improved accuracy?
4. Is there a need for a configuration file to store project-specific cropping preferences?
5. Should cropped photos include metadata indicating they were auto-processed?