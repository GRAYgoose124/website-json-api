from pathlib import Path
from typing import List, Dict, Any

from .managers.project import ProjectManager
from .managers.notice import NoticeManager
from .step.registry import StepRegistry
from .step.context import StepContext
from .step.loader import StepLoader
from .workflow_engine import WorkflowEngine
from .dependency_resolver import DependencyResolver

# Global instances
project_manager = ProjectManager()
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager)

def initialize_core(userdata_root: str, step_paths: List[str]) -> Dict[str, Any]:
    """
    Initialize the application core with userdata and step configurations.
    
    Args:
        userdata_root: Path to the userdata directory
        step_paths: List of paths to step definition directories
        
    Returns:
        Dict containing initialization results and statistics
    """
    # Create userdata root directory
    userdata_root_path = Path(userdata_root).resolve()
    userdata_root_path.mkdir(parents=True, exist_ok=True)
    
    # Set up subdirectories under userdata root
    uploads_dir = userdata_root_path / "uploads"
    projects_dir = userdata_root_path / "projects"
    uploads_dir.mkdir(exist_ok=True)
    projects_dir.mkdir(exist_ok=True)
    
    # Configure project manager with projects directory
    project_manager.projects_root = projects_dir
    print(f"Using projects directory: {project_manager.projects_root}")
    
    # Load steps from all specified paths
    all_step_definitions = {}
    all_step_implementations = {}
    
    print(f"Loading steps from {len(step_paths)} path(s):")
    for step_path in step_paths:
        print(f"  - {step_path}")
        
        try:
            # Create a fresh StepLoader for each path to avoid state accumulation
            step_loader = StepLoader()
            step_definitions, step_implementations = step_loader.load_from_path(step_path)
            
            # Merge step definitions and implementations
            for step_id, definition in step_definitions.items():
                if step_id in all_step_definitions:
                    print(f"Warning: Step '{step_id}' already defined, overwriting from {step_path}")
                all_step_definitions[step_id] = definition
                
            for step_id, implementation in step_implementations.items():
                if step_id in all_step_implementations:
                    print(f"Warning: Step '{step_id}' implementation already exists, overwriting from {step_path}")
                all_step_implementations[step_id] = implementation
                
        except Exception as e:
            print(f"Error loading steps from {step_path}: {e}")
            raise
    
    # Validate that all steps have implementations
    missing_implementations = []
    for step_id in all_step_definitions:
        if step_id not in all_step_implementations:
            missing_implementations.append(step_id)
    
    if missing_implementations:
        print("Step validation errors:")
        for step_id in missing_implementations:
            print(f"  - No implementation found for step: {step_id}")
        raise ValueError(f"Missing implementations for steps: {missing_implementations}")
    
    # Register all loaded steps
    for step_id, definition in all_step_definitions.items():
        if step_id in all_step_implementations:
            step_registry.register(definition)(all_step_implementations[step_id])
            print(f"Registered step: {step_id}")
        else:
            print(f"Warning: No implementation found for step: {step_id}")
    
    # Initialize dependency resolver after steps are registered
    dependency_resolver = DependencyResolver(step_registry.definitions)
    step_registry.set_dependency_resolver(dependency_resolver)
    print("Dependency resolver initialized")
    
    print(f"Successfully loaded {len(all_step_definitions)} step definitions")
    
    return {
        'userdata_root': str(userdata_root_path),
        'uploads_dir': str(uploads_dir),
        'projects_dir': str(projects_dir),
        'step_definitions': all_step_definitions,
        'step_implementations': all_step_implementations,
        'total_steps': len(all_step_definitions)
    }

# Export classes for backward compatibility
__all__ = [
    'ProjectManager',
    'NoticeManager', 
    'StepRegistry',
    'StepContext',
    'WorkflowEngine',
    'initialize_core',
    'project_manager',
    'notice_manager',
    'step_registry',
    'workflow_engine'
] 