import os
import yaml
from typing import Optional, Tuple
from .project import Project


class ProjectManager:
    """Centralized project management singleton"""

    _instance = None
    _current_project = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self.projects_root = os.environ.get("AB_PROJECTS_FOLDER", "./projects")
        self._initialized = True

    def get_current_project(self) -> Project:
        """Get current project, loading from .current-project if needed"""
        if self._current_project is None:
            self._load_current_project()
        if self._current_project is None:
            raise RuntimeError("No current project set. Use 'work on <project>' first.")
        return self._current_project

    def set_current_project(self, name: str) -> Project:
        """Set current project and persist choice"""
        project = Project(name, self.projects_root)
        project.ensure_initialized()  # Create DB, run setup if needed

        self._current_project = project
        self._save_current_project_choice(name)
        return project

    def has_current_project(self) -> bool:
        """Check if a current project is set without raising errors"""
        try:
            self.get_current_project()
            return True
        except RuntimeError:
            return False

    def _load_current_project(self):
        """Load current project from .current-project file"""
        current_project_file = os.path.join(self.projects_root, ".current-project")
        if os.path.exists(current_project_file):
            with open(current_project_file, "r") as f:
                name = f.read().strip()
            if name:
                self._current_project = Project(name, self.projects_root)
                self._current_project.ensure_initialized()  # Create DB, run setup if needed

    def _save_current_project_choice(self, name: str):
        """Save current project choice to .current-project file"""
        os.makedirs(self.projects_root, exist_ok=True)
        current_project_file = os.path.join(self.projects_root, ".current-project")
        with open(current_project_file, "w") as f:
            f.write(name)
