#!/usr/bin/env python

"""
Usage:
    import.py [options] <file>

Options:
    --help -h             Print this message
    --debug               Debug logging
"""

# /// script
# dependencies = [
#   "docopt",
#   "icecream",
#   "python-dotenv"
# ]
# ///

import os
import sys

from docopt import docopt
from icecream import ic
from dotenv import load_dotenv
import pdfplumber
import csv

load_dotenv()


def main():
    global options
    options = docopt(__doc__)

    ic.disable()
    if options["--debug"]:
        ic.enable()

    filename = options["<file>"]
    basename = os.path.splitext(os.path.basename(filename))[0]

    with (
        pdfplumber.open(filename) as pdf,
        open(f"{basename}.csv", "w", newline="") as f,
    ):
        writer = csv.writer(f)
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    writer.writerow(row)


class CommandError(Exception):
    pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CommandError as e:
        print(e, file=sys.stderr)
        exit(1)
