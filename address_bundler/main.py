#!/usr/bin/env python

"""
Usage:
    address-bundler [options] work on <project>
    address-bundler [options] configure
    address-bundler [options] import <file>
    address-bundler [options] geocode
    address-bundler [options] fix addresses
    address-bundler [options] cluster
    address-bundler [options] generate [maps|pdfs]
    address-bundler [options] summary

Options:
    --help -h             Print this message
    --debug               Debug logging

Description:

work on <project>
    Switch to or create a new project.  If creating a
    new project you will be prompted for options.

configure
    Update the project options via interactive prompting.

import <file>
    Import student names and addresses from the specified file.   Only csv files
    are supported.  We expect to find columns `First Name`, `Last Name` and 'Address`
    Multiple files can be imported to a project.

geocode
    Look up the latitude/longitude locations for all addresses that have not yet
    been geocoded.

fix addresses
    For any addresses that were not able to be automatically geocoded you will
    be prompted to optionally fix the address and to manually enter the the
    lat/lon (you can get this using Google Maps)

cluster
    Run the clustering algorithm on the geocoded addresses to create the desired
    number of clusters.  The addresses within each cluster will be assigned into bundles.
    The cluster count and bundle sizes come from the project configuration file.

generate maps
    Create a map of the clusters.  Each cluster will be in a separate color pin.

generate pdfs
    Create the pdf files.  A master list of student names to bundle letters and then
    one file for each bundle with the list of students and their addresses.  The
    maps must already be created.

generate
    The generate command by itself will first create the maps and then the pdfs
"""

import sys
import logging


from docopt import docopt
from icecream import ic
from dotenv import load_dotenv
from common.project import set_current_project, get_project

load_dotenv()


def main():
    global options
    options = docopt(__doc__)

    loglevel = "INFO"
    ic.disable()
    if options["--debug"]:
        ic.enable()
        loglevel = "DEBUG"

    logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")

    # Handle 'work on <project>' command
    if options.get("work") and options.get("on") and options.get("<project>"):
        set_current_project(options["<project>"])
        print(f"Now working on project: {options['<project>']}")
        return

    # Handle 'import <file>' command
    if options.get("import") and options.get("<file>"):
        from .import_file import import_csv_file

        project = get_project()
        file_path = options["<file>"]
        if not file_path.lower().endswith(".csv"):
            raise RuntimeError("Only CSV files are supported for import.")
        added_count, failed_rows = import_csv_file(file_path)
        print(f"Imported {added_count} students.")
        if failed_rows:
            print(
                f"Failed to import {len(failed_rows)} row(s) due to missing required values:"
            )
            for i, row in enumerate(failed_rows, 1):
                print(f"  Row {i}: {row}")
        return

    # Handle 'geocode' command
    if options.get("geocode"):
        from .geocode import geocode_missing_students

        total, succeeded = geocode_missing_students()
        print(f"Geocoded {succeeded}/{total} address(es).")
        return

    # Handle 'configure' command
    if options.get("configure"):
        project = get_project()
        project.prompt_for_config()
        print("Project configuration updated.")
        return

    # Handle 'fix addresses' command
    if options["fix"] and options["addresses"]:
        from .fix_addresses import fix_addresses

        return fix_addresses()

    # Handle 'cluster' command
    if options["cluster"]:
        from .cluster import cluster

        return cluster()

    if options["generate"] and options["maps"]:
        from .maps import generate_maps

        return generate_maps()

    if options["generate"] and options["pdfs"]:
        from .pdfs import generate_pdfs

        return generate_pdfs()

    if options["generate"]:
        from .maps import generate_maps
        from .pdfs import generate_pdfs

        generate_maps()
        generate_pdfs()
        return

    # Handle 'summary' command
    if options.get("summary"):
        from .summary import run_summary_command

        run_summary_command()
        return

    print(options)


class CommandError(Exception):
    pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CommandError as e:
        print(e, file=sys.stderr)
        exit(1)
