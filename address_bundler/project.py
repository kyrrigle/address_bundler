import os
import yaml
from .db import init_db

_projects_root = "./projects"
_project = None  # Will hold the current Project instance or None


def get_project():
    if _project is None:
        raise RuntimeError("Project has not been set")
    return _project


def initialize_projects(root_dir):
    """
    Set the global projects root directory and load the current project from
    .current-project if it exists.
    """
    global _projects_root, _project
    _projects_root = root_dir
    current_project_file = os.path.join(_projects_root, ".current-project")
    if os.path.exists(current_project_file):
        with open(current_project_file, "r") as f:
            name = f.read().strip()
        if name:
            _project = Project(name, _projects_root)
            # Initialize DB in the project directory
            db_path = os.path.join(_project.get_directory(), "students.db")
            init_db(db_path)
            from .models import Student
            Student.create_table(safe=True)
            return
    _project = None


def set_current_project(name):
    """
    Set the current project, create the directory if needed, and update
    .current-project. Also builds DB and ensures configuration.
    """
    global _project
    os.makedirs(os.path.join(_projects_root, name), exist_ok=True)
    current_project_file = os.path.join(_projects_root, ".current-project")
    with open(current_project_file, "w") as f:
        f.write(name)

    _project = Project(name, _projects_root)

    # Initialize DB in the project directory
    db_path = os.path.join(_project.get_directory(), "students.db")
    init_db(db_path)
    from .models import Student
    Student.create_table(safe=True)

    # If first-time creation, prompt for configuration
    if not os.path.exists(_project.config_path()):
        _project.prompt_for_config()


class Project:
    """
    Represents a single address-bundler project.
    Stores/loads its persistent configuration in project.yaml.
    """

    DEFAULT_CONFIG = {
        "school_name": "",
        "bundle_size": 20,
        "min_bundle_size": 5,
    }

    def __init__(self, name: str, projects_root: str):
        self.name = name
        self.projects_root = projects_root
        self.config = Project.DEFAULT_CONFIG.copy()
        self.load_config()  # Will silently ignore if file missing

    # --------------------------------------------------------------------- #
    # Paths
    # --------------------------------------------------------------------- #
    def get_directory(self) -> str:
        return os.path.abspath(os.path.join(self.projects_root, self.name))

    def config_path(self) -> str:
        return os.path.join(self.get_directory(), "project.yaml")

    # --------------------------------------------------------------------- #
    # Configuration helpers
    # --------------------------------------------------------------------- #
    def load_config(self) -> None:
        """
        Load configuration from project.yaml if present.
        """
        cfg_file = self.config_path()
        if os.path.exists(cfg_file):
            with open(cfg_file, "r") as f:
                data = yaml.safe_load(f) or {}
            # Overlay onto defaults
            self.config.update(data)

    def save_config(self) -> None:
        """
        Persist configuration to project.yaml.
        """
        with open(self.config_path(), "w") as f:
            yaml.safe_dump(self.config, f, sort_keys=False)

    def prompt_for_config(self) -> None:
        """
        Interactively ask the user for configuration values, showing current
        values as defaults. Blank input leaves the existing value unchanged.
        """
        print("\nConfigure project settings (press Enter to keep current value)")
        # School name
        current_school = self.config.get("school_name", "")
        school_prompt = f"School name [{current_school}]: " if current_school else "School name: "
        school_name = input(school_prompt).strip()
        if school_name:
            self.config["school_name"] = school_name

        # Bundle size
        current_bundle = self.config.get("bundle_size", 20)
        while True:
            bundle_input = input(f"Bundle size [{current_bundle}]: ").strip()
            if not bundle_input:
                break
            try:
                bundle_size = int(bundle_input)
                if bundle_size <= 0:
                    print("Bundle size must be greater than 0. Please try again.")
                    continue
                self.config["bundle_size"] = bundle_size
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")

        # Min bundle size
        current_min_bundle = self.config.get("min_bundle_size", 5)
        while True:
            min_bundle_input = input(f"Min bundle size [{current_min_bundle}]: ").strip()
            if not min_bundle_input:
                break
            try:
                min_bundle_size = int(min_bundle_input)
                if min_bundle_size <= 0:
                    print("Min bundle size must be greater than 0. Please try again.")
                    continue
                if min_bundle_size >= self.config["bundle_size"]:
                    print(f"Min bundle size ({min_bundle_size}) must be less than bundle size ({self.config['bundle_size']}). Please try again.")
                    continue
                self.config["min_bundle_size"] = min_bundle_size
                break
            except ValueError:
                print("Invalid number. Please enter a valid integer.")

        # Final validation to ensure min_bundle_size < bundle_size
        if self.config["min_bundle_size"] >= self.config["bundle_size"]:
            print(f"\nWarning: Min bundle size ({self.config['min_bundle_size']}) must be less than bundle size ({self.config['bundle_size']}).")
            print("Please re-enter these values:")
            
            # Re-prompt for bundle size
            while True:
                bundle_input = input(f"Bundle size [{self.config['bundle_size']}]: ").strip()
                if not bundle_input:
                    bundle_input = str(self.config['bundle_size'])
                try:
                    bundle_size = int(bundle_input)
                    if bundle_size <= 0:
                        print("Bundle size must be greater than 0. Please try again.")
                        continue
                    self.config["bundle_size"] = bundle_size
                    break
                except ValueError:
                    print("Invalid number. Please enter a valid integer.")
            
            # Re-prompt for min bundle size
            while True:
                min_bundle_input = input(f"Min bundle size [must be less than {self.config['bundle_size']}]: ").strip()
                try:
                    min_bundle_size = int(min_bundle_input)
                    if min_bundle_size <= 0:
                        print("Min bundle size must be greater than 0. Please try again.")
                        continue
                    if min_bundle_size >= self.config["bundle_size"]:
                        print(f"Min bundle size ({min_bundle_size}) must be less than bundle size ({self.config['bundle_size']}). Please try again.")
                        continue
                    self.config["min_bundle_size"] = min_bundle_size
                    break
                except ValueError:
                    print("Invalid number. Please enter a valid integer.")

        self.save_config()
        print("Configuration saved to project.yaml")