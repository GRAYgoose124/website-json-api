import argparse
import sys
from pathlib import Path
from app.api import app
from app.core import step_registry, project_manager
from app.step_loader import StepLoader
from app.dependency_resolver import DependencyResolver

def main():
    parser = argparse.ArgumentParser(description="Workflow API Server")
    parser.add_argument(
        "--userdata-root", 
        type=str, 
        default="./userdata",
        help="Path to main userdata directory (will contain uploads and projects)"
    )
    parser.add_argument(
        "--include-steps-root", 
        type=str, 
        action='append',
        default=[],
        help="Path to directory containing custom step definitions and implementations (can be specified multiple times)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8001,
        help="Port to bind the server to (default: 8001)"
    )
    
    args = parser.parse_args()
    
    # Create userdata root directory
    userdata_root = Path(args.userdata_root).resolve()
    userdata_root.mkdir(parents=True, exist_ok=True)
    
    # Set up subdirectories under userdata root
    uploads_dir = userdata_root / "uploads"
    projects_dir = userdata_root / "projects"
    uploads_dir.mkdir(exist_ok=True)
    projects_dir.mkdir(exist_ok=True)
    
    # Configure project manager with projects directory under userdata root
    project_manager.projects_root = projects_dir
    print(f"Using projects directory: {project_manager.projects_root}")
    
    # Configure uploads directory in the API
    app.state.uploads_dir = uploads_dir
    print(f"Using uploads directory: {uploads_dir}")
    
    # Load steps from all specified paths
    all_step_definitions = {}
    all_step_implementations = {}
    
    # Require at least one include-steps-root to be specified
    if not args.include_steps_root:
        print("Error: At least one --include-steps-root must be specified")
        print("Example: --include-steps-root ./bundled_steps/project --include-steps-root ./bundled_steps/custom")
        sys.exit(1)
    
    step_paths = args.include_steps_root
    
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
            sys.exit(1)
    
    # Validate that all steps have implementations
    missing_implementations = []
    for step_id in all_step_definitions:
        if step_id not in all_step_implementations:
            missing_implementations.append(step_id)
    
    if missing_implementations:
        print("Step validation errors:")
        for step_id in missing_implementations:
            print(f"  - No implementation found for step: {step_id}")
        sys.exit(1)
    
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
    
    # Start the server
    print(f"Starting server on {args.host}:{args.port}")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
