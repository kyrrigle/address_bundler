from __future__ import annotations

from .models import Student


def fix_addresses():
    # Ensure at least one student already has coordinates
    if Student.select().where(
        (Student.latitude.is_null(False)) & (Student.longitude.is_null(False))
    ).count() == 0:
        print("No students have been geocoded yet.  Perhaps you want to run geocode first?")
        return

    # Process students missing coordinates
    missing = Student.select().where(
        (Student.latitude.is_null(True)) | (Student.longitude.is_null(True))
    )

    if not missing:
        print("No students are missing geocoding.  Nothing to fix up!")
        return

    for student in missing:
        print(f"\nStudent: {student.first_name} {student.last_name}")
        print(f"Current address: {student.address}")
        new_addr = input("Enter new address (leave blank to keep): ").strip()

        changed = False
        if new_addr:
            student.address = new_addr
            changed = True

        coords = input("Enter latitude,longitude (leave blank to skip): ").strip()
        if coords:
            try:
                lat_str, lon_str = [c.strip() for c in coords.split(",")]
                student.latitude = float(lat_str)
                student.longitude = float(lon_str)
                changed = True
            except Exception:
                print("Invalid latitude/longitude input – skipping coordinate update.")

        if changed:
            student.save()
            print("Saved.")
        else:
            print("No changes made.")
    return
