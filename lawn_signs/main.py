#!/usr/bin/env python

"""
Usage:
    ab-signs summary

Options:
    --help -h   Show this help message

Description:

summary
    Prints a summary of the lawn signs project.
"""

import sys
from docopt import docopt

def main():
    options = docopt(__doc__)

    if options.get('summary'):
        from .summary import run_summary_command
        run_summary_command()
        return

    print(options)

if __name__ == '__main__':
    sys.exit(main())