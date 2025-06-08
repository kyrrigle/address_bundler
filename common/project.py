import os
import yaml
from datetime import datetime
from typing import Optional, Dict, Any
from .db import init_db
from .database_manager import DatabaseManager, ProjectConfig, ProjectMetadata


class Project:
    """
    Represents a single address-bundler project with unified database storage.
    """

    DEFAULT_CONFIG = {
        "school_name": "",
        "bundle_size": "20",
        "min_bundle_size": "5",
        "project_version": "2.0",
    }

    def __init__(self, name: str, projects_root: str):
        self.name = name
        self.projects_root = projects_root
        self.db_path = os.path.join(self.get_directory(), "project.db")
        self._db = None
        self._config_cache = {}

    # --------------------------------------------------------------------- #
    # Paths and Directory Management
    # --------------------------------------------------------------------- #

    def get_directory(self) -> str:
        """Get absolute path to project directory"""
        return os.path.abspath(os.path.join(self.projects_root, self.name))

    def config_path(self) -> str:
        """Get path to legacy project.yaml (for migration)"""
        return os.path.join(self.get_directory(), "project.yaml")

    # --------------------------------------------------------------------- #
    # Database Management
    # --------------------------------------------------------------------- #

    def get_db(self):
        """Get database connection, initializing if needed"""
        if self._db is None:
            self._db = init_db(self.db_path)
        return self._db

    def ensure_initialized(self):
        """Ensure project directory and database are set up"""
        os.makedirs(self.get_directory(), exist_ok=True)
        print("here")

        # Initialize database connection
        self.get_db()

        # Ensure schema is up to date
        db_manager = DatabaseManager(self)
        db_manager.ensure_schema()

        # Migrate from YAML if this is first time
        if self._is_first_time_setup():
            self._migrate_yaml_config()
            self._initialize_default_config()
            self.prompt_for_config()

        self.update_last_accessed()

    def _is_first_time_setup(self) -> bool:
        """Check if this is the first time setting up this project"""
        try:
            ProjectMetadata.get(ProjectMetadata.name == self.name)
            return False
        except ProjectMetadata.DoesNotExist:
            return True

    # --------------------------------------------------------------------- #
    # Configuration Management
    # --------------------------------------------------------------------- #

    def get_config(self, key: str, default: Any = None) -> str:
        """Get configuration value from database"""
        if key in self._config_cache:
            return self._config_cache[key]

        try:
            config = ProjectConfig.get(ProjectConfig.key == key)
            self._config_cache[key] = config.value
            return config.value
        except ProjectConfig.DoesNotExist:
            if default is not None:
                return str(default)
            return self.DEFAULT_CONFIG.get(key, "")

    def set_config(self, key: str, value: str):
        """Set configuration value in database"""
        config, created = ProjectConfig.get_or_create(
            key=key, defaults={"value": value}
        )
        if not created:
            config.value = value
            config.updated_at = datetime.now()
            config.save()

        self._config_cache[key] = value

    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration as a dictionary"""
        config_dict = self.DEFAULT_CONFIG.copy()

        # Override with database values
        for config in ProjectConfig.select():
            config_dict[config.key] = config.value

        return config_dict

    def _initialize_default_config(self):
        """Initialize default configuration values"""
        for key, value in self.DEFAULT_CONFIG.items():
            if not self._config_exists(key):
                self.set_config(key, value)

    def _config_exists(self, key: str) -> bool:
        """Check if a configuration key exists"""
        try:
            ProjectConfig.get(ProjectConfig.key == key)
            return True
        except ProjectConfig.DoesNotExist:
            return False

    def update_last_accessed(self):
        """Update project access timestamp"""
        metadata, created = ProjectMetadata.get_or_create(
            name=self.name, defaults={"created_at": datetime.now()}
        )
        metadata.last_accessed = datetime.now()
        metadata.save()

    # --------------------------------------------------------------------- #
    # Migration and Legacy Support
    # --------------------------------------------------------------------- #

    def _migrate_yaml_config(self):
        """One-time migration from project.yaml to database"""
        yaml_path = self.config_path()
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f) or {}

            for key, value in config.items():
                self.set_config(key, str(value))

            # Backup and remove yaml file
            backup_path = yaml_path + ".migrated"
            os.rename(yaml_path, backup_path)
            print(f"Migrated configuration from {yaml_path} to database")
            print(f"Backup saved as {backup_path}")

    # --------------------------------------------------------------------- #
    # Interactive Configuration
    # --------------------------------------------------------------------- #

    def prompt_for_config(self) -> None:
        """
        Interactively ask the user for configuration values, showing current
        values as defaults. Blank input leaves the existing value unchanged.
        """
        print("\nConfigure project settings (press Enter to keep current value)")

        # School name
        current_school = self.get_config("school_name")
        school_prompt = (
            f"School name [{current_school}]: " if current_school else "School name: "
        )
        school_name = input(school_prompt).strip()
        if school_name:
            self.set_config("school_name", school_name)

        # Bundle size
        current_bundle = int(self.get_config("bundle_size", "20"))
        while True:
            bundle_input = input(f"Bundle size [{current_bundle}]: ").strip()
            if not bundle_input:
                break
            try:
                bundle_size = int(bundle_input)
                if bundle_size <= 0:
                    print("Bundle size must be greater than 0. Please try again.")
                    continue
                self.set_config("bundle_size", str(bundle_size))
                current_bundle = bundle_size
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")

        # Min bundle size
        current_min_bundle = int(self.get_config("min_bundle_size", "5"))
        while True:
            min_bundle_input = input(
                f"Min bundle size [{current_min_bundle}]: "
            ).strip()
            if not min_bundle_input:
                break
            try:
                min_bundle_size = int(min_bundle_input)
                if min_bundle_size <= 0:
                    print("Min bundle size must be greater than 0. Please try again.")
                    continue
                if min_bundle_size >= current_bundle:
                    print(
                        f"Min bundle size ({min_bundle_size}) must be less than bundle size ({current_bundle}). Please try again."
                    )
                    continue
                self.set_config("min_bundle_size", str(min_bundle_size))
                current_min_bundle = min_bundle_size
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")

        # Final validation to ensure min_bundle_size < bundle_size
        if current_min_bundle >= current_bundle:
            print(
                f"\nWarning: Min bundle size ({current_min_bundle}) must be less than bundle size ({current_bundle})."
            )
            print("Please re-enter these values:")
            self._re_prompt_bundle_sizes()

        print("Configuration saved to database")

    def _re_prompt_bundle_sizes(self):
        """Re-prompt for bundle sizes when validation fails"""
        # Re-prompt for bundle size
        while True:
            current_bundle = int(self.get_config("bundle_size", "20"))
            bundle_input = input(f"Bundle size [{current_bundle}]: ").strip()
            if not bundle_input:
                bundle_input = str(current_bundle)
            try:
                bundle_size = int(bundle_input)
                if bundle_size <= 0:
                    print("Bundle size must be greater than 0. Please try again.")
                    continue
                self.set_config("bundle_size", str(bundle_size))
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")

        # Re-prompt for min bundle size
        while True:
            current_bundle = int(self.get_config("bundle_size"))
            min_bundle_input = input(
                f"Min bundle size [must be less than {current_bundle}]: "
            ).strip()
            try:
                min_bundle_size = int(min_bundle_input)
                if min_bundle_size <= 0:
                    print("Min bundle size must be greater than 0. Please try again.")
                    continue
                if min_bundle_size >= current_bundle:
                    print(
                        f"Min bundle size ({min_bundle_size}) must be less than bundle size ({current_bundle}). Please try again."
                    )
                    continue
                self.set_config("min_bundle_size", str(min_bundle_size))
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")


def get_project() -> "Project":
    """
    Retrieve the current :class:`Project` selected via the
    ``work on <project>`` command.

    This helper should be used by downstream modules that run *after*
    the application’s entry-point has already called
    :func:`common.bootstrap.bootstrap_application`.  It delegates to the
    :class:`common.project_manager.ProjectManager` singleton to obtain
    the active project.

    Returns
    -------
    Project
        The currently-active project.

    Raises
    ------
    RuntimeError
        If no project has been selected yet (i.e., the user has not run
        ``work on <project>``).
    """
    # Local import to avoid circular-import issues at module load time.
    from .project_manager import ProjectManager

    manager = ProjectManager()
    return manager.get_current_project()
