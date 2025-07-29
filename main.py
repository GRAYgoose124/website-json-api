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
        "--config-root", 
        type=str, 
        required=True,
        help="Path to directory containing custom step definitions and implementations"
    )
    parser.add_argument(
        "--projects-root",
        type=str,
        default=None,
        help="Root directory for projects (default: ./projects)"
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
    
    # Configure project manager with custom projects root if provided
    if args.projects_root:
        project_manager.projects_root = Path(args.projects_root).resolve()
        project_manager.projects_root.mkdir(parents=True, exist_ok=True)
        print(f"Using projects directory: {project_manager.projects_root}")
    
    # Load steps from config root
    print(f"Loading steps from: {args.config_root}")
    try:
        step_loader = StepLoader(config_root=args.config_root)
        step_definitions, step_implementations = step_loader.load_from_path(args.config_root)
        
        # Validate steps
        validation_errors = step_loader.validate_steps()
        if validation_errors:
            print("Step validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            sys.exit(1)
        
        # Register all loaded steps
        for step_id, definition in step_definitions.items():
            if step_id in step_implementations:
                step_registry.register(definition)(step_implementations[step_id])
                print(f"Registered step: {step_id}")
            else:
                print(f"Warning: No implementation found for step: {step_id}")
        
        # Initialize dependency resolver after steps are registered
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        print("Dependency resolver initialized")
        
        print(f"Successfully loaded {len(step_definitions)} step definitions")
        
    except Exception as e:
        print(f"Error loading steps from {args.config_root}: {e}")
        sys.exit(1)
    
    # Start the server
    print(f"Starting server on {args.host}:{args.port}")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
