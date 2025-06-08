from typing import Optional, Tuple
from .project_manager import ProjectManager
from .project import Project


def bootstrap_application(require_project: bool = True) -> Tuple[ProjectManager, Optional[Project]]:
    """
    Standard application bootstrap for all entry points
    
    Args:
        require_project: If True, raises error if no current project set
        
    Returns:
        (project_manager, current_project_or_none)
    """
    project_manager = ProjectManager()
    
    try:
        current_project = project_manager.get_current_project()
        return project_manager, current_project
    except RuntimeError as e:
        if require_project:
            raise RuntimeError(
                "No current project set. Run 'work on <project>' first to select a project."
            ) from e
        return project_manager, None