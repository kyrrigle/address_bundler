` command structure.

## Goals

1. Eliminate the need for scattered `get_project()` calls throughout the codebase for database initialization
2. Provide explicit, predictable database initialization that happens once per application run
3. Fail fast with clear error messages when projects are not configured
4. Simplify the developer experience when working with the database
5. Make the codebase more maintainable by centralizing initialization logic
6. Build on the existing `work on <project>` command structure

## User Stories

1. **As a developer**, I want to explicitly initialize the database in my main.py file so that I know exactly when and how the database is set up.

2. **As a developer**, I want clear error messages when no project is configured so that I know to use the `work on <project>` command to set up a project.

3. **As a developer**, I want to use database models anywhere in my code without worrying about initialization so that I can focus on business logic rather than infrastructure concerns.

4. **As a developer**, I want the system to fail fast if there are configuration issues so that I can catch problems early in development.

5. **As a user**, I want to use the existing `work on <project>` command to initialize projects so that the interface remains consistent.

## Functional Requirements

1. **R1**: The system must provide a single `initialize_database()` function that handles all database setup logic.

2. **R2**: The `initialize_database()` function must read the current project from the `.current-project` file in the projects directory, leveraging the existing `initialize_projects()` logic.

3. **R3**: If no `.current-project` file exists or is empty, the system must raise a clear exception telling the user to run `<command> work on <project_name>` to initialize a project first.

4. **R4**: If the `.current-project` file contains an invalid project name or the project directory doesn't exist, the system must raise a clear exception.

5. **R5**: The system must create the database file in the correct project directory and initialize all required tables.

6. **R6**: Each main.py file must call `initialize_database()` at startup before any database operations (except for the `work on <project>` command itself).

7. **R7**: The system must ensure the database is only initialized once per application run (subsequent calls should be no-ops).

8. **R8**: All existing model classes must work without modification after initialization.

9. **R9**: The `work on <project>` command must continue to work as it currently does, handling project creation and database setup.

10. **R10**: Database initialization must fail immediately if the project directory is not writable.

11. **R11**: The `initialize_database()` function must be a no-op when called during `work on <project>` command execution to avoid conflicts.

## Non-Goals (Out of Scope)

1. Automatic database initialization on first model access
2. Support for multiple databases or projects in a single application run
3. Database migration or schema versioning
4. Testing utilities or in-memory database support
5. Thread-safety considerations
6. Modifying the existing `work on <project>` command interface
7. Configuration validation beyond basic project existence
8. Removing the existing project management system in `common/project.py`

## Design Considerations

### Proposed API

```python
# In each main.py file:
from common.db import initialize_database

if __name__ == "__main__":
    # Skip database initialization for project management commands
    if not (options.get("work") and options.get("on")):
        initialize_database()  # Must be called before any database operations
    
    # Handle 'work on <project>' command
    if options.get("work") and options.get("on") and options.get("<project>"):
        set_current_project(options["<project>"])
        print(f"Now working on project: {options['<project>']}")
        return
    
    # ... rest of application logic