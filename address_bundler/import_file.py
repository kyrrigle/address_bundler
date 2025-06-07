import csv
from common.models import Student

REQUIRED_COLUMNS = ["First Name", "Last Name", "Address"]

def import_csv_file(filepath):
    """
    Import students from a CSV file.
    Returns (added_count, failed_rows)
    """
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        if not headers:
            raise RuntimeError("CSV file is missing headers")
        for col in REQUIRED_COLUMNS:
            if col not in headers:
                raise RuntimeError(f"Missing required column: {col}")

        added_count = 0
        failed_rows = []

        for row in reader:
            # Ignore empty rows (all required columns empty)
            if all(not (row.get(col) or "").strip() for col in REQUIRED_COLUMNS):
                continue

            # Check for missing required values
            if any(not (row.get(col) or "").strip() for col in REQUIRED_COLUMNS):
                failed_rows.append(row)
                continue

            first_name = row["First Name"].strip()
            last_name = row["Last Name"].strip()
            address = row["Address"].strip()

            # Check for existing record
            exists = Student.select().where(
                (Student.first_name == first_name) &
                (Student.last_name == last_name)
            ).exists()
            if exists:
                continue

            try:
                Student.create(
                    first_name=first_name,
                    last_name=last_name,
                    address=address
                )
                added_count += 1
            except Exception:
                failed_rows.append(row)

    return added_count, failed_rows
