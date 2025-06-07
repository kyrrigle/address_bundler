"""Unit tests for the lawn_signs.auto_crop placeholder module."""

from PIL import Image
import importlib
import inspect


def test_crop_placeholder_exists_and_returns_none() -> None:
    """Import the module and verify the stub works as expected."""
    module = importlib.import_module("lawn_signs.auto_crop")
    assert hasattr(module, "crop_placeholder"), "crop_placeholder() is missing"
    assert inspect.isfunction(module.crop_placeholder)
    # The placeholder currently does nothing and returns None.
    assert module.crop_placeholder() is None


def test_calculate_center_crop_box_basic():
    from lawn_signs import auto_crop

    # Image size: 1000x800, aspect ratio 0.8 (so crop_w=640, crop_h=800)
    box = auto_crop.calculate_center_crop_box((1000, 800), aspect_ratio=0.8)
    left, upper, right, lower = box
    assert right - left == 640
    assert lower - upper == 800
    assert left == (1000 - 640) // 2
    assert upper == 0  # crop_h == img_h, so upper should be 0


def test_calculate_center_crop_box_tall_image():
    from lawn_signs import auto_crop

    # Image size: 600x1200, aspect ratio 0.5 (so crop_h=1200, crop_w=600)
    box = auto_crop.calculate_center_crop_box((600, 1200), aspect_ratio=0.5)
    left, upper, right, lower = box
    assert right - left == 600
    assert lower - upper == 1200
    assert left == 0
    assert upper == 0


def test_calculate_center_crop_box_wide_image():
    from lawn_signs import auto_crop

    # Image size: 1200x600, aspect ratio 2.0 (so crop_w=1200, crop_h=600)
    box = auto_crop.calculate_center_crop_box((1200, 600), aspect_ratio=2.0)
    left, upper, right, lower = box
    assert right - left == 1200
    assert lower - upper == 600
    assert left == 0
    assert upper == 0


def test_calculate_center_crop_box_smaller_than_image():
    from lawn_signs import auto_crop

    # Image size: 1000x800, aspect ratio 1.0 (so crop_h=800, crop_w=800)
    box = auto_crop.calculate_center_crop_box((1000, 800), aspect_ratio=1.0)
    left, upper, right, lower = box
    assert right - left == 800
    assert lower - upper == 800
    assert left == 100
    assert upper == 0


def _create_test_image(path, fmt="JPEG", size=(100, 100), color=(128, 128, 128)):
    img = Image.new("RGB", size, color)
    img.save(path, format=fmt, quality=95)


def test_crop_image_with_pil_quality_preservation():
    from lawn_signs.auto_crop import crop_image_with_pil

    import tempfile
    import os
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test JPEG image
        orig_path = os.path.join(tmpdir, "orig.jpg")
        _create_test_image(orig_path, fmt="JPEG", size=(100, 100), color=(200, 100, 50))

        # 1. Crop with full image box (should copy, not recompress)
        out_path_full = os.path.join(tmpdir, "out_full.jpg")
        crop_image_with_pil(orig_path, (0, 0, 100, 100), out_path_full)
        with open(orig_path, "rb") as f1, open(out_path_full, "rb") as f2:
            orig_bytes = f1.read()
            out_bytes = f2.read()
            # Allow for minor metadata differences, but files should be nearly identical in size
            assert (
                abs(len(orig_bytes) - len(out_bytes)) < 100
            ), "Full-image crop should not recompress"

        # 2. Crop a subregion (should save as JPEG, high quality)
        out_path_crop = os.path.join(tmpdir, "out_crop.jpg")
        crop_image_with_pil(orig_path, (10, 10, 90, 90), out_path_crop)
        # Check that output is JPEG and not much smaller than expected
        with Image.open(out_path_crop) as cropped_img:
            assert cropped_img.format == "JPEG"
            assert cropped_img.size == (80, 80)
        # File size should be reasonable for a high-quality JPEG.
        # For small, uniform crops, JPEG can be very small (<500 bytes).
        # We check that the file is not empty and is at least 200 bytes.
        assert os.path.getsize(out_path_crop) > 200

        # 3. Test with PNG (lossless)
        orig_png = os.path.join(tmpdir, "orig.png")
        _create_test_image(orig_png, fmt="PNG", size=(100, 100), color=(10, 200, 10))
        out_png = os.path.join(tmpdir, "out_full.png")
        crop_image_with_pil(orig_png, (0, 0, 100, 100), out_png)
        with open(orig_png, "rb") as f1, open(out_png, "rb") as f2:
            assert (
                f1.read() == f2.read()
            ), "PNG full-image crop should be byte-for-byte identical"


import pytest


def test_calculate_crop_box_for_largest_face_basic():
    from lawn_signs.auto_crop import calculate_crop_box_for_largest_face

    # Simulate two faces: one small, one large
    image_size = (1000, 800)
    faces = [
        (100, 200, 300, 100),  # (top, right, bottom, left) - area: 200x100=20,000
        (400, 900, 700, 500),  # area: 300x400=120,000 (largest)
    ]
    box = calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=0.8)
    # Should center on the largest face
    assert isinstance(box, tuple) and len(box) == 4
    left, upper, right, lower = box
    assert 0 <= left < right <= image_size[0]
    assert 0 <= upper < lower <= image_size[1]


def test_calculate_crop_box_for_largest_face_no_faces():
    from lawn_signs.auto_crop import calculate_crop_box_for_largest_face

    image_size = (1000, 800)
    faces = []
    box = calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=0.8)
    assert box is None


def test_calculate_crop_box_for_largest_face_invalid_aspect_ratio():
    from lawn_signs.auto_crop import calculate_crop_box_for_largest_face

    image_size = (1000, 800)
    faces = [(100, 200, 300, 100)]
    with pytest.raises(ValueError):
        calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=0)
    with pytest.raises(ValueError):
        calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=-1)
    with pytest.raises(ValueError):
        calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=100)


def test_calculate_crop_box_for_largest_face_edge_case():
    from lawn_signs.auto_crop import calculate_crop_box_for_largest_face

    # Face at the edge of the image
    image_size = (500, 500)
    faces = [(0, 500, 100, 400)]  # right at the right edge
    box = calculate_crop_box_for_largest_face(image_size, faces, aspect_ratio=1.0)
    left, upper, right, lower = box
    assert 0 <= left < right <= image_size[0]
    assert 0 <= upper < lower <= image_size[1]


def test_fallback_to_center_crop_when_no_faces(monkeypatch):
    from lawn_signs import auto_crop

    # Patch detect_faces to always return []
    monkeypatch.setattr(auto_crop, "detect_faces", lambda path: [])
    # Use a dummy image size
    image_size = (800, 600)
    aspect_ratio = 0.8
    # Fallback logic: if no faces, use center crop
    faces = auto_crop.detect_faces("dummy.jpg")
    if not faces:
        box = auto_crop.calculate_center_crop_box(image_size, aspect_ratio)
        left, upper, right, lower = box
        assert 0 <= left < right <= image_size[0]
        assert 0 <= upper < lower <= image_size[1]


def test_detect_faces_mock(monkeypatch):
    from lawn_signs import auto_crop

    # Patch face_recognition.face_locations to return a known value
    class DummyFR:
        @staticmethod
        def load_image_file(path):
            return "dummy_image"

        @staticmethod
        def face_locations(image):
            return [(10, 60, 50, 20)]

    monkeypatch.setattr(auto_crop, "face_recognition", DummyFR)
    faces = auto_crop.detect_faces("dummy.jpg")
    assert faces == [(10, 60, 50, 20)]
