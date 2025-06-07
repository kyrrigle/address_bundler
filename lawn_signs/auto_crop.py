"""Auto-crop utilities for the lawn-signs project.

Current status
--------------

The module presently only exposes :func:`crop_placeholder` as a stub so the
test suite passes.  In later tasks it will grow full face-detection and
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

# --------------------------------------------------------------------------- #
# Temporary stub
# --------------------------------------------------------------------------- #
def crop_placeholder() -> None:
    """Temporary stub to satisfy linters until real implementation arrives."""
    # This function will be replaced in task 2.x.
    return None
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
    aspect_ratio: float = 0.8
) -> tuple[int, int, int, int] | None:
    """
    Given multiple detected faces, select the largest (most prominent) face and
    calculate a crop rectangle centered on it. Validates aspect ratio and ensures
    crop boundaries fit within the image.

    This function robustly handles multiple faces by always choosing the one with
    the largest area (width * height).


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

    if not (isinstance(aspect_ratio, (float, int)) and aspect_ratio > 0 and aspect_ratio < 10):
        raise ValueError(f"Invalid aspect_ratio: {aspect_ratio}. Must be > 0 and reasonable.")

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

    # Calculate crop size: maximize area around face, maintain aspect ratio, fit in image
    face_w = right - left
    face_h = bottom - top

    # Target crop height: expand to include some margin (e.g., 1.5x face height)
    margin = 0.75
    crop_h = int(face_h * (1 + margin))
    crop_w = int(round(crop_h * aspect_ratio))

    # Adjust crop size to fit within image boundaries
    if crop_w > img_w:
        crop_w = img_w
        crop_h = int(round(crop_w / aspect_ratio))

    if crop_h > img_h:
        crop_h = img_h
        crop_w = int(round(crop_h * aspect_ratio))

    # Center crop on face, clamp to image boundaries
    left_crop = max(0, min(img_w - crop_w, face_center_x - crop_w // 2))
    upper_crop = max(0, min(img_h - crop_h, face_center_y - crop_h // 2))
    right_crop = min(img_w, left_crop + crop_w)
    lower_crop = min(img_h, upper_crop + crop_h)

    # Final validation: ensure crop box is within image
    if left_crop < 0 or upper_crop < 0 or right_crop > img_w or lower_crop > img_h:
        raise ValueError("Calculated crop box is out of image bounds.")

    return (left_crop, upper_crop, right_crop, lower_crop)

# --------------------------------------------------------------------------- #
# Fallback Center-Crop Logic
# --------------------------------------------------------------------------- #
def calculate_center_crop_box(
    image_size: tuple[int, int],
    aspect_ratio: float = 0.8
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

    if not (isinstance(aspect_ratio, (float, int)) and aspect_ratio > 0 and aspect_ratio < 10):
        raise ValueError(f"Invalid aspect_ratio: {aspect_ratio}. Must be > 0 and reasonable.")

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
    quality: int = 95
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
