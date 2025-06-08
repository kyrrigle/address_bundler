import os
from importlib import reload

import pytest


# --------------------------------------------------------------------------- #
# Helper fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def clean_env(tmp_path, monkeypatch):
    """
    Provide a fresh projects folder with the ProjectManager singleton reset.
    Does NOT create a project – useful for tests that expect no project.
    """
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("AB_PROJECTS_FOLDER", str(projects_root))

    # Reload modules that cache state so they pick up the new env var
    import common.project_manager as pm_module
    reload(pm_module)
    import common.bootstrap as bootstrap_module
    reload(bootstrap_module)

    yield  # Nothing to return – caller decides what to do next


@pytest.fixture
def project_setup(tmp_path, monkeypatch):
    """
    Create a fully-initialised test project and return it.
    Interactive prompts are patched out.
    """
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("AB_PROJECTS_FOLDER", str(projects_root))

    # Reload modules that cache state so they pick up the new env var
    import common.project_manager as pm_module
    reload(pm_module)
    import common.bootstrap as bootstrap_module
    reload(bootstrap_module)

    # Patch out interactive prompt
    from common.project import Project
    monkeypatch.setattr(Project, "prompt_for_config", lambda self: None, raising=False)

    from common.project_manager import ProjectManager
    pm = ProjectManager()
    project = pm.set_current_project("testproj")

    return project


# --------------------------------------------------------------------------- #
# Tests for common.database_init.initialize_database
# --------------------------------------------------------------------------- #
def test_initialize_database_requires_project(clean_env):
    """Calling initialize_database with no selected project should fail."""
    from common.database_init import initialize_database, InitializationError

    with pytest.raises(InitializationError):
        initialize_database()


def test_initialize_database_success(project_setup, monkeypatch):
    """initialize_database creates the expected tables when a project exists."""
    # Patch prompt again in case initialize_database triggers ensure_initialized
    from common.project import Project
    monkeypatch.setattr(Project, "prompt_for_config", lambda self: None, raising=False)

    from common.database_init import initialize_database

    # Should not raise
    initialize_database()

    db = project_setup.get_db()
    for table in ("student", "project_config", "project_metadata"):
        assert db.table_exists(table), f"Expected table '{table}' to exist"


# --------------------------------------------------------------------------- #
# Tests for common.database_manager.DatabaseManager
# --------------------------------------------------------------------------- #
def test_database_manager_schema_and_version(project_setup):
    """DatabaseManager.ensure_schema creates tables and manages schema_version."""
    from common.database_manager import DatabaseManager

    db_manager = DatabaseManager(project_setup)
    db_manager.ensure_schema()

    db = project_setup.get_db()
    for table in ("student", "project_config", "project_metadata"):
        assert db.table_exists(table), f"Expected table '{table}' to exist"

    # Default schema version should be 1
    assert db_manager.get_schema_version() == 1

    # Update schema_version and read it back
    db_manager.set_schema_version(2)
    assert db_manager.get_schema_version() == 2