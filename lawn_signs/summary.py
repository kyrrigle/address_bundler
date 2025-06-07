from common.models import Student
from common.project import get_project


def run_summary_command():
    get_project()  # initializes the project

    print("=" * 40)
    print("SIGNS SUMMARY")
    print("=" * 40)

    # Get all students
    all_students = list(Student.select())
    total_students = len(all_students)

    # Count students without photos
    students_without_photos = [
        student
        for student in all_students
        if not student.image_name or student.image_name.strip() == ""
    ]
    missing_photos_count = len(students_without_photos)

    # Count students with photos
    students_with_photos = [
        student
        for student in all_students
        if student.image_name and student.image_name.strip() != ""
    ]
    with_photos_count = len(students_with_photos)

    # Count photo validation status
    valid_photos_count = len(
        [student for student in students_with_photos if student.image_valid == "valid"]
    )

    invalid_photos_count = len(
        [
            student
            for student in students_with_photos
            if student.image_valid == "invalid"
        ]
    )

    unknown_photos_count = len(
        [
            student
            for student in students_with_photos
            if student.image_valid == "unknown" or student.image_valid is None
        ]
    )

    # Display summary
    print(f"Total students: {total_students}")
    print(f"Students with photos: {with_photos_count}")
    print(f"Students without photos: {missing_photos_count}")

    if with_photos_count > 0:
        print("\nPhoto validation status:")
        print(f"  Valid photos: {valid_photos_count}")
        print(f"  Invalid photos: {invalid_photos_count}")
        print(f"  Unknown/not validated: {unknown_photos_count}")

    if missing_photos_count > 0:
        print("\nStudents missing photos:")
        for student in students_without_photos:
            print(f"  - {student.first_name} {student.last_name}")

    if invalid_photos_count > 0:
        invalid_students = [
            student
            for student in students_with_photos
            if student.image_valid == "invalid"
        ]
        print("\nStudents with invalid photos:")
        for student in invalid_students:
            print(
                f"  - {student.first_name} {student.last_name} ({student.image_name})"
            )
