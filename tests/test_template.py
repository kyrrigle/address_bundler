import os
import tempfile
import json
import pytest

from lawn_signs.template import Template, Slot, ImageSlot, TextSlot

SAMPLE_TEMPLATE = {
    "slots": {
        "photo": {
            "type": "image",
            "box": {"x": 1.25, "y": 1.25, "w": 10.50, "h": 13.125},
        },
        "name": {
            "type": "text",
            "font_name": "Helvetica-Bold",
            "font_size": 64,
            "box": {"x": 1.25, "y": 14.56, "w": 10.50, "h": 2.27},
        },
    }
}


@pytest.fixture
def temp_template_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "template.json")
        pdf_path = os.path.join(tmpdir, "template.pdf")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_TEMPLATE, f)
        # Create a dummy PDF file
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF\n")
        yield json_path


def test_template_paths(temp_template_file):
    tpl = Template(temp_template_file)
    assert tpl.template_json == temp_template_file
    assert tpl.template_pdf.endswith(".pdf")


def test_template_data(temp_template_file):
    tpl = Template(temp_template_file)
    assert "slots" in tpl.template_data
    assert tpl.template_data["slots"]["photo"]["type"] == "image"


def test_slots_access(temp_template_file):
    tpl = Template(temp_template_file)
    slots = tpl.slots
    assert "photo" in slots
    assert "name" in slots
    assert isinstance(slots["photo"], ImageSlot)
    assert isinstance(slots["name"], TextSlot)


def test_image_and_text_slots(temp_template_file):
    tpl = Template(temp_template_file)
    image_slots = tpl.image_slots
    text_slots = tpl.text_slots
    assert list(image_slots.keys()) == ["photo"]
    assert list(text_slots.keys()) == ["name"]
    assert isinstance(image_slots["photo"], ImageSlot)
    assert isinstance(text_slots["name"], TextSlot)


def test_get_slot(temp_template_file):
    tpl = Template(temp_template_file)
    photo_slot = tpl.get_slot("photo")
    name_slot = tpl.get_slot("name")
    assert isinstance(photo_slot, ImageSlot)
    assert isinstance(name_slot, TextSlot)
    assert photo_slot.box.w == 10.50
    assert name_slot.font_name == "Helvetica-Bold"
    assert name_slot.font_size == 64


def test_iter_slots(temp_template_file):
    tpl = Template(temp_template_file)
    slot_names = {slot.name for slot in tpl.iter_slots()}
    assert slot_names == {"photo", "name"}


def test_get_slot_requirements(temp_template_file):
    tpl = Template(temp_template_file)
    reqs = tpl.get_slot_requirements()
    assert reqs == {
        "photo": {
            "type": "image",
            "required": True,
            "description": "Path to image file required",
        },
        "name": {
            "type": "text",
            "required": True,
            "description": "Text value required",
        },
    }


def test_validate_slot_values_success(temp_template_file):
    tpl = Template(temp_template_file)
    # Create a dummy image file for the photo slot
    img_path = os.path.join(os.path.dirname(temp_template_file), "dummy.jpg")
    with open(img_path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # minimal JPEG header
    slot_values = {"photo": img_path, "name": "Test Name"}
    tpl.validate_slot_values(slot_values)  # Should not raise


def test_validate_slot_values_missing(temp_template_file):
    tpl = Template(temp_template_file)
    # Only provide one slot value
    slot_values = {"name": "Test Name"}
    with pytest.raises(ValueError) as excinfo:
        tpl.validate_slot_values(slot_values)
    assert "Missing required slot values" in str(excinfo.value)


def test_validate_slot_values_wrong_type(temp_template_file):
    tpl = Template(temp_template_file)
    # Create a dummy image file for the photo slot
    img_path = os.path.join(os.path.dirname(temp_template_file), "dummy.jpg")
    with open(img_path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    # Provide wrong type for name
    slot_values = {"photo": img_path, "name": 12345}
    with pytest.raises(ValueError) as excinfo:
        tpl.validate_slot_values(slot_values)
    assert "expects a string value" in str(excinfo.value)


def test_validate_slot_values_image_path_not_exist(temp_template_file):
    tpl = Template(temp_template_file)
    slot_values = {"photo": "/nonexistent/path/to/image.jpg", "name": "Test Name"}
    with pytest.raises(ValueError) as excinfo:
        tpl.validate_slot_values(slot_values)
    assert "does not exist" in str(excinfo.value)
