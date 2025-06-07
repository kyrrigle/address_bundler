"""Auto-crop utilities for the lawn-signs project.

Current status
--------------

cropping logic.

The required third-party libraries (Pillow and face_recognition) and standard
library helpers (os, pathlib) are now imported so that subsequent tasks can
focus on implementation rather than project wiring.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
# Standard library
import os
from pathlib import Path

# Third-party libraries
from PIL import Image  # type: ignore
import face_recognition  # type: ignore

# Project imports
from common.models import Student
from common.project import get_project
from peewee import DoesNotExist


# --------------------------------------------------------------------------- #
# Cropped Directory Management (Task 5.1)
# --------------------------------------------------------------------------- #
def ensure_cropped_dir_exists(base_dir: str | Path) -> Path:
    """
    Ensure the cropped directory structure exists under the given base directory.

    Args:
        base_dir (str | Path): The base directory where the 'cropped' subdirectory should be created.

    Returns:
        Path: The full path to the cropped directory.
    """
    base = Path(base_dir)
    cropped_dir = base / "cropped"
    cropped_dir.mkdir(parents=True, exist_ok=True)
    return cropped_dir


# --------------------------------------------------------------------------- #
# Face Detection Logic
# --------------------------------------------------------------------------- #
def detect_faces(image_path: str | Path) -> list[tuple[int, int, int, int]]:
    """
    Load an image and detect faces using the face_recognition library.

    Args:
        image_path (str | Path): Path to the image file.

    Returns:
        List of face locations, each as a tuple (top, right, bottom, left).
        Returns an empty list if no faces are detected.
    """
    image = face_recognition.load_image_file(str(image_path))
    face_locations = face_recognition.face_locations(image)
    return face_locations


# --------------------------------------------------------------------------- #
# Crop Calculation Logic
# --------------------------------------------------------------------------- #
def calculate_crop_box_for_largest_face(
    image_size: tuple[int, int],
    face_locations: list[tuple[int, int, int, int]],
    aspect_ratio: float = 0.8,
) -> tuple[int, int, int, int] | None:
    """
    Given multiple detected faces, select the largest (most prominent) face and
    calculate a crop rectangle centered on it. Validates aspect ratio and ensures
    crop boundaries fit within the image.

    This function robustly handles multiple faces by always choosing the one with
    the largest area (width * height). Uses a maximized crop approach that
    maintains aspect ratio while centering on the face.

    Args:
        image_size (tuple): (width, height) of the image.
        face_locations (list): List of face locations (top, right, bottom, left).
        aspect_ratio (float): Desired width/height ratio for the crop. Must be > 0.

    Returns:
        (left, upper, right, lower) tuple for PIL.Image.crop, or None if no faces.

    Raises:
        ValueError: If aspect_ratio is not positive.
    """
    if not face_locations:
        return None

    if not (
        isinstance(aspect_ratio, (float, int))
        and aspect_ratio > 0
        and aspect_ratio < 10
    ):
        raise ValueError(
            f"Invalid aspect_ratio: {aspect_ratio}. Must be > 0 and reasonable."
        )

    # Find the largest face by area (most prominent face)
    def area(loc):
        top, right, bottom, left = loc
        return max(0, (right - left)) * max(0, (bottom - top))

    # Select the largest face from all detected faces
    largest = max(face_locations, key=area)
    top, right, bottom, left = largest
    face_center_x = (left + right) // 2
    face_center_y = (top + bottom) // 2

    img_w, img_h = image_size
    image_aspect = img_w / img_h

    # Calculate crop dimensions based on aspect ratio comparison
    if image_aspect > aspect_ratio:
        # Image is too wide - crop width, use full height
        new_width = int(img_h * aspect_ratio)
        new_height = img_h
        left_crop = max(0, face_center_x - new_width // 2)
        right_crop = min(left_crop + new_width, img_w)
        # Adjust left if right would exceed image bounds
        if right_crop == img_w:
            left_crop = img_w - new_width
        top_crop = 0
        bottom_crop = img_h
    else:
        # Image is too tall - crop height, use full width
        new_height = int(img_w / aspect_ratio)
        new_width = img_w
        top_crop = max(0, face_center_y - new_height // 2)
        bottom_crop = min(top_crop + new_height, img_h)
        # Adjust top if bottom would exceed image bounds
        if bottom_crop == img_h:
            top_crop = img_h - new_height
        left_crop = 0
        right_crop = img_w

    # Final validation: ensure crop box is within image bounds
    if left_crop < 0 or top_crop < 0 or right_crop > img_w or bottom_crop > img_h:
        raise ValueError("Calculated crop box is out of image bounds.")

    return (left_crop, top_crop, right_crop, bottom_crop)


# --------------------------------------------------------------------------- #
# Fallback Center-Crop Logic
# --------------------------------------------------------------------------- #
def calculate_center_crop_box(
    image_size: tuple[int, int], aspect_ratio: float = 0.8
) -> tuple[int, int, int, int]:
    """
    Calculate a center crop rectangle for the given image size and aspect ratio, with validation.

    Args:
        image_size (tuple): (width, height) of the image.
        aspect_ratio (float): Desired width/height ratio for the crop. Must be > 0.

    Returns:
        (left, upper, right, lower) tuple for PIL.Image.crop.

    Raises:
        ValueError: If aspect_ratio is not positive.
    """
    img_w, img_h = image_size

    if not (
        isinstance(aspect_ratio, (float, int))
        and aspect_ratio > 0
        and aspect_ratio < 10
    ):
        raise ValueError(
            f"Invalid aspect_ratio: {aspect_ratio}. Must be > 0 and reasonable."
        )

    # Determine the largest crop that fits the aspect ratio
    crop_h = img_h
    crop_w = int(round(crop_h * aspect_ratio))
    if crop_w > img_w:
        crop_w = img_w
        crop_h = int(round(crop_w / aspect_ratio))

    left = max(0, (img_w - crop_w) // 2)
    upper = max(0, (img_h - crop_h) // 2)
    right = min(img_w, left + crop_w)
    lower = min(img_h, upper + crop_h)

    # Final validation: ensure crop box is within image
    if left < 0 or upper < 0 or right > img_w or lower > img_h:
        raise ValueError("Calculated center crop box is out of image bounds.")

    return (left, upper, right, lower)


# --------------------------------------------------------------------------- #
# Image Cropping Function (Task 2.5)
# --------------------------------------------------------------------------- #
def crop_image_with_pil(
    input_path: str | Path,
    crop_box: tuple[int, int, int, int],
    output_path: str | Path,
    image_format: str | None = None,
    quality: int = 95,
) -> None:
    """
    Crop an image using PIL and save it with maximum quality, avoiding unnecessary recompression.

    - If the crop box is the full image, copy the file directly (no recompression).
    - For JPEG, use high quality and avoid chroma subsampling.
    - For PNG, preserve lossless format.
    - Preserve EXIF data if present.

    Args:
        input_path (str | Path): Path to the input image.
        crop_box (tuple): (left, upper, right, lower) crop rectangle.
        output_path (str | Path): Path to save the cropped image.
        image_format (str | None): Format to save (e.g., 'JPEG', 'PNG'). If None, inferred from input.
        quality (int): JPEG quality (default 95).

    Returns:
        None

    Raises:
        Exception: If cropping or saving fails.
    """
    input_path = str(input_path)
    output_path = str(output_path)
    with Image.open(input_path) as img:
        img_w, img_h = img.size
        # If crop box is the full image, just copy the file to avoid recompression
        if crop_box == (0, 0, img_w, img_h):
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                # Use binary copy to preserve all data
                with open(input_path, "rb") as src, open(output_path, "wb") as dst:
                    dst.write(src.read())
            return

        cropped = img.crop(crop_box)
        save_kwargs = {}
        fmt = image_format or img.format
        if fmt and fmt.upper() == "JPEG":
            # Max quality, no chroma subsampling
            save_kwargs["quality"] = max(90, min(quality, 100))
            save_kwargs["subsampling"] = 0
            save_kwargs["optimize"] = True
        # Preserve EXIF if present
        if hasattr(img, "info") and "exif" in img.info:
            save_kwargs["exif"] = img.info["exif"]
        cropped.save(output_path, format=fmt, **save_kwargs)


# --------------------------------------------------------------------------- #
# CLI Orchestration Entry Point
# --------------------------------------------------------------------------- #
def auto_crop_command(aspect_ratio: float, force: bool) -> None:
    """
    Entry point for the auto-crop CLI command.
    Orchestrates the cropping process and provides progress reporting and user feedback.
    Implements batch processing of all eligible students with comprehensive error handling,
    logging, result reporting, graceful continuation, memory management, and validation.
    """
    import logging
    import gc
    from typing import Dict, List, Tuple

    project = get_project()

    # Set up logging for debugging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("auto_crop_debug.log"), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    # Query all students needing cropping (only validated photos)
    students = list(Student.get_students_needing_cropping(force=force))
    # Additional validation: only process students with valid images
    validated_students = [
        student
        for student in students
        if student.image_valid == "valid" and student.image_name
    ]

    total = len(validated_students)
    skipped_unvalidated = len(students) - total

    if skipped_unvalidated > 0:
        print(
            f"Skipped {skipped_unvalidated} students with unvalidated or missing images"
        )
        logger.info(
            f"Skipped {skipped_unvalidated} students: images not validated or missing"
        )

    if total == 0:
        print("No validated images found that need cropping.")
        logger.info("No validated images found that need cropping")
        return

    print(
        f"Starting auto-crop batch process for {total} validated students (aspect_ratio={aspect_ratio})"
    )
    logger.info(
        f"Starting batch process: {total} students, aspect_ratio={aspect_ratio}"
    )

    # Initialize counters and tracking
    success_count = 0
    fail_count = 0
    face_detected_count = 0
    center_crop_count = 0
    failed_students: List[Tuple[str, str, str]] = []  # (name, image_name, error)

    # Determine base directory for cropped images
    base_dir = Path(project.get_directory())
    cropped_dir = ensure_cropped_dir_exists(base_dir)

    # Define possible photo directories for input path resolution
    photo_search_dirs = [
        base_dir / "originals",  # Primary location for validated photos
        base_dir / "photos",
        base_dir / "test-data" / "washout-hs" / "photos",
    ]

    # Process each student with comprehensive error handling
    for idx, student in enumerate(validated_students, 1):
        img_name = student.image_name
        student_name = f"{student.first_name} {student.last_name}"

        print(
            f"[{idx}/{total}] Processing: {student_name} ({img_name}) ...",
            end="",
            flush=True,
        )
        logger.info(
            f"Processing student {idx}/{total}: {student_name}, image: {img_name}"
        )

        try:
            # Validate student data
            if not img_name or not img_name.strip():
                raise ValueError("Student has no image filename")

            # Find input image path
            input_path = None
            for photos_dir in photo_search_dirs:
                candidate = photos_dir / img_name
                if candidate.exists():
                    input_path = candidate
                    logger.debug(f"Found image at: {input_path}")
                    break

            if not input_path:
                searched_paths = [str(d / img_name) for d in photo_search_dirs]
                raise FileNotFoundError(f"Photo not found. Searched: {searched_paths}")

            # Validate file accessibility and basic image properties
            if not os.access(input_path, os.R_OK):
                raise PermissionError(f"Cannot read image file: {input_path}")

            # Open and validate image
            try:
                with Image.open(input_path) as img:
                    image_size = img.size
                    logger.debug(f"Image size: {image_size}")

                    # Validate image dimensions
                    if image_size[0] < 10 or image_size[1] < 10:
                        raise ValueError(f"Image too small: {image_size}")
            except Exception as img_error:
                raise ValueError(f"Invalid or corrupted image file: {img_error}")

            # Detect faces with detailed logging
            try:
                face_locations = detect_faces(input_path)
                face_count = len(face_locations)
                logger.debug(f"Detected {face_count} faces")

                if face_count > 0:
                    face_detected_count += 1
                    logger.debug(f"Face locations: {face_locations}")
            except Exception as face_error:
                logger.warning(f"Face detection failed: {face_error}")
                face_locations = []

            # Calculate crop box with fallback logic
            crop_box = None
            crop_method = ""

            if face_locations:
                try:
                    crop_box = calculate_crop_box_for_largest_face(
                        image_size, face_locations, aspect_ratio
                    )
                    if crop_box:
                        crop_method = "face-based"
                        logger.debug(f"Face-based crop box: {crop_box}")
                    else:
                        logger.warning("Face-based crop calculation returned None")
                except Exception as crop_error:
                    logger.warning(f"Face-based crop calculation failed: {crop_error}")

            # Fallback to center crop if face-based cropping failed
            if crop_box is None:
                try:
                    crop_box = calculate_center_crop_box(image_size, aspect_ratio)
                    crop_method = "center"
                    center_crop_count += 1
                    logger.debug(f"Center crop box: {crop_box}")
                except Exception as center_error:
                    raise ValueError(
                        f"Both face-based and center crop failed: {center_error}"
                    )

            # Output path in cropped directory
            output_path = cropped_dir / img_name

            # Ensure output directory is writable
            if not os.access(cropped_dir, os.W_OK):
                raise PermissionError(
                    f"Cannot write to cropped directory: {cropped_dir}"
                )

            # Crop and save image with quality preservation
            try:
                crop_image_with_pil(
                    input_path=input_path,
                    crop_box=crop_box,
                    output_path=output_path,
                    image_format=None,
                    quality=95,
                )
                logger.debug(f"Cropped image saved to: {output_path}")
            except Exception as save_error:
                raise ValueError(f"Failed to crop and save image: {save_error}")

            # Update cropping_status in database
            try:
                student.cropping_status = "cropped"
                student.save()
                logger.debug(f"Updated database: cropping_status = 'cropped'")
            except Exception as db_error:
                logger.error(f"Database update failed: {db_error}")
                # Still consider this a success since the image was processed
                print(f" done ({crop_method} crop, db warning)")
            else:
                print(f" done ({crop_method} crop)")

            success_count += 1
            logger.info(
                f"Successfully processed {student_name} using {crop_method} crop"
            )

        except Exception as e:
            # Comprehensive error handling with graceful continuation
            error_msg = str(e)
            failed_students.append((student_name, img_name, error_msg))

            # Log detailed error information
            logger.error(f"Failed to process {student_name} ({img_name}): {error_msg}")

            # Update cropping_status to "failed" in database
            try:
                student.cropping_status = "failed"
                student.save()
                logger.debug(f"Updated database: cropping_status = 'failed'")
            except Exception as db_error:
                logger.error(
                    f"Could not update cropping_status to 'failed': {db_error}"
                )
                print(" failed! (db update error)", end="")

            print(f" failed! ({error_msg})")
            fail_count += 1

        # Memory management: periodic garbage collection for large batches
        if idx % 50 == 0:
            gc.collect()
            logger.debug(f"Performed garbage collection at student {idx}")

    # Final garbage collection
    gc.collect()

    # Comprehensive result reporting
    print(f"\n{'='*60}")
    print("AUTO-CROP BATCH PROCESSING RESULTS")
    print(f"{'='*60}")
    print(f"Total students processed: {total}")
    print(f"Successful crops: {success_count}")
    print(f"Failed crops: {fail_count}")
    print(f"Success rate: {(success_count/total*100):.1f}%" if total > 0 else "N/A")

    if success_count > 0:
        print(f"\nCrop method breakdown:")
        print(f"  Face-detected crops: {face_detected_count}")
        print(f"  Center crops (fallback): {center_crop_count}")
        print(f"  Face detection rate: {(face_detected_count/success_count*100):.1f}%")

    if skipped_unvalidated > 0:
        print(f"\nSkipped unvalidated images: {skipped_unvalidated}")

    # Detailed failure reporting
    if failed_students:
        print(f"\nFailed students ({len(failed_students)}):")
        for name, img_name, error in failed_students:
            print(f"  - {name} ({img_name}): {error}")

        print(f"\nFor detailed debugging information, check: auto_crop_debug.log")

    # Final status message
    if fail_count == 0:
        print("\n✓ All images processed successfully!")
        logger.info("Batch processing completed successfully")
    elif success_count > 0:
        print(f"\n⚠ Batch completed with {fail_count} failures. Check log for details.")
        logger.warning(f"Batch completed with {fail_count} failures")
    else:
        print("\n✗ Batch processing failed completely. Check log for details.")
        logger.error("Batch processing failed completely")

    print(f"Cropped images saved to: {cropped_dir}")
    logger.info(f"Batch processing completed. Cropped images in: {cropped_dir}")
