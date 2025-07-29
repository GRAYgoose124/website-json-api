import argparse
import sys
from app.api import app
from app.core import initialize_core

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
    
    # Require at least one include-steps-root to be specified
    if not args.include_steps_root:
        print("Error: At least one --include-steps-root must be specified")
        print("Example: --include-steps-root ./bundled_steps/project --include-steps-root ./bundled_steps/custom")
        sys.exit(1)
    
    try:
        # Initialize the application core
        init_result = initialize_core(args.userdata_root, args.include_steps_root)
        
        # Configure uploads directory in the API
        app.state.uploads_dir = init_result['uploads_dir']
        print(f"Using uploads directory: {init_result['uploads_dir']}")
        
        # Start the server
        print(f"Starting server on {args.host}:{args.port}")
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
        
    except Exception as e:
        print(f"Failed to initialize application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
