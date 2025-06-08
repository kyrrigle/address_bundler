"""common.summary

Provides a top-level summary that combines generic project information with
sub-summaries from the lawn_signs and address_bundler packages.

Invoked indirectly via:  ab-project summary
"""

SECTION_DIVIDER = "-" * 40


def _print_project_information() -> None:
    """Print directory and configuration for the currently selected project."""
    try:
        from common.project import get_project  # pylint: disable=import-error
    except Exception:
        print("Project information unavailable (unable to import common.project).")
        print()
        return

    try:
        project = get_project()
    except Exception:
        project = None

    print(SECTION_DIVIDER)
    print("PROJECT INFORMATION")
    print(SECTION_DIVIDER)

    if project is None:
        print("No project selected.")
        print()
        return

    # Project directory (if available)
    if hasattr(project, "get_directory"):
        try:
            print(f"Directory: {project.get_directory()}")
        except Exception:
            pass  # Ignore unexpected errors while printing directory

    print("Configuration:")
    config = project.get_all_config()
    for key, value in config.items():
        print(f" - {key}: {value}")

    print()  # Spacer


def run_summary_command() -> None:
    """Entry point used by the `ab-project summary` CLI command."""
    # 1. Project-level details
    _print_project_information()

    # 2-3. Package-specific summaries (lazy imports avoid circular deps)
    from lawn_signs.summary import run_summary_command as run_lawn_signs_summary
    from address_bundler.summary import (
        run_summary_command as run_address_bundler_summary,
    )

    # Lawn-signs summary
    run_lawn_signs_summary()
    print()  # Spacer

    # Address-bundler summary
    run_address_bundler_summary()
