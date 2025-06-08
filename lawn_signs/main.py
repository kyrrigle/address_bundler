#!/usr/bin/env python

"""
Usage:
    ab-signs import <csv-file> <photos-directory> [--name-column NAME] [--filename-column NAME]  [--fuzzy-threshold SCORE]
    ab-signs summary
    ab-signs validate [--min-resolution PIXELS]
    ab-signs auto-crop [--aspect-ratio RATIO] [--force]

IMPORTANT: Before running any commands, you must first select a project with: work on <project>

Options:
    --help -h                Show this help message
    --name-column NAME       Column to use for student name when importing [default: Name]
    --filename-column NAME   Column to use for filename when importing [default: Filename]
    --fuzzy-threshold SCORE  How close of a match to determine fuzzy name matching [default: 80]
    --min-resolution PIXELS  Minimum total pixels required for valid images [default: 1000000]
    --aspect-ratio RATIO     Aspect ratio for cropping photos [default: 0.8]
    --force                  Force the command to run again (re-do work)

Description:

import
    Import students and their photos from the csv file and directory.   Can be run multiple
    times.  If a new photo is included it will replace the existing

summary
    Prints a summary of the lawn signs project.

validate
    Validate original photos to meet specific constraints (readable image file, minimum resolution).
    Updates student records with validation status.

auto-crop
    Automatically crop student photos using face detection and fallback logic.
    Cropped images are saved to the cropped directory. Supports aspect ratio selection.
"""

import sys
from docopt import docopt
from dotenv import load_dotenv
from common.bootstrap import bootstrap_application

load_dotenv()


def main():
    options = docopt(__doc__)

    # All lawn_signs commands require a project
    try:
        bootstrap_application(require_project=True)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if options["summary"]:
        from .summary import run_summary_command

        run_summary_command()
        return

    if options["validate"]:
        min_resolution = int(options["--min-resolution"])
        from .validate import validate_student_images

        validate_student_images(min_resolution)
        return

    if options["import"] and options["<csv-file>"] and options["<photos-directory>"]:
        csv_file = options["<csv-file>"]
        photos_directory = options["<photos-directory>"]
        name_column = options["--name-column"]
        filename_column = options["--filename-column"]
        fuzzy_threshold = int(options["--fuzzy-threshold"])

        from .import_photos import import_photos

        import_photos(
            csv_file, photos_directory, name_column, filename_column, fuzzy_threshold
        )
        return

    # Handle auto-crop command and parse --aspect-ratio parameter
    if options.get("auto-crop"):
        aspect_ratio = float(options["--aspect-ratio"])
        force = options["--force"]
        from .auto_crop import auto_crop_command

        auto_crop_command(aspect_ratio, force)
        return

    print("Command not handled")
    print(options)
    return 1


if __name__ == "__main__":
    sys.exit(main())
