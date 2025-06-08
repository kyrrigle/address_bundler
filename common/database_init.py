from .bootstrap import bootstrap_application


class InitializationError(Exception):
    """Raised when database initialization fails"""
    pass


def initialize_database():
    """
    Initialize the database for the current project.
    This function ensures the project is set and database is ready.
    """
    try:
        project_manager, project = bootstrap_application(require_project=True)
        project.ensure_initialized()
    except RuntimeError as e:
        raise InitializationError(f"Cannot initialize database: {e}") from e
    except Exception as e:
        raise InitializationError(f"Database initialization failed: {e}") from e