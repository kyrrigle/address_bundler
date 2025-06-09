#!/usr/bin/env python

"""
Usage:
    ab-signs import <csv-file> <photos-directory> [--name-column NAME] [--filename-column NAME]  [--fuzzy-threshold SCORE]
    ab-signs summary
    ab-signs validate [--min-resolution PIXELS]
    ab-signs auto-crop [--aspect-ratio RATIO] [--force]
    ab-signs render templates [--force]
    ab-signs render template <template-path> <photo-path> <name> [<output-path>]
    ab-signs render contact-sheet <source-directory> [<output-path>]

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
import os
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

    if options["render"] and options["template"]:
        # <template-file> <photo-path> <name>
        template_path = options["<template-path>"]
        photo_path = options["<photo-path>"]
        student_name = options["<name>"]

        from .template import Template, render_template

        output_path = options["<output-path>"] or "output.pdf"
        print(f"Creating {output_path}")
        template = Template(template_path)
        slot_values = {"photo": photo_path, "name": student_name}
        render_template(template, slot_values, output_path)
        return

    if options["render"] and options["templates"]:
        from .template import render_templates_command

        render_templates_command(options["--force"])
        return

    #   ab-signs render contact-sheet <source-directory> [<output-path>]
    if options["render"] and options["contact-sheet"]:
        source_directory = options["<source-directory>"]
        output_path = options["<output-path>"] or "contact-sheet.pdf"
        from .template import build_contact_sheet

        file_pdf_list = []
        for name in os.listdir(source_directory):
            file_pdf_list.append(os.path.join(source_directory, name))

        build_contact_sheet(file_pdf_list, output_path)
        return

    print("Command not handled")
    print(options)
    return 1


if __name__ == "__main__":
    sys.exit(main())
