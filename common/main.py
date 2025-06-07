#!/usr/bin/env python

"""
Usage:
    ab-project [options] work on <project>
    ab-project [options] configure
    ab-project [options] summary

Options:
    --help -h             Print this message
    --debug               Debug logging

Description:

work on <project>
    Switch to or create a new project. If creating a
    new project you will be prompted for options.

configure
    Update the project options via interactive prompting.

summary
    Prints summaries for both lawn_signs and address_bundler projects.
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

    loglevel = 'INFO'
    ic.disable()
    if options['--debug']:
        ic.enable()
        loglevel = 'DEBUG'

    logging.basicConfig(
        level=loglevel,
        format='%(levelname)s: %(message)s'
    )

    # Handle 'work on <project>' command
    if options.get('work') and options.get('on') and options.get('<project>'):
        set_current_project(options['<project>'])
        print(f"Now working on project: {options['<project>']}")
        return

    # Handle 'configure' command
    if options.get('configure'):
        project = get_project()
        project.prompt_for_config()
        print("Project configuration updated.")
        return

    # Handle 'summary' command
    if options.get('summary'):
        from common.summary import run_summary_command
        run_summary_command()
        return

    print(options)


class CommandError(Exception): pass

if __name__ == '__main__':
    try:
        sys.exit(main())
    except CommandError as e:
        print(e, file=sys.stderr)
        exit(1)