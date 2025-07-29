#!/usr/bin/env python3
"""
Setup script for the project_steps module.

This script helps set up the project_steps module for use with the workflow API.
"""

import os
import sys
import shutil
from pathlib import Path

def create_projects_directory(projects_root: str = "/projects"):
    """Create the projects root directory if it doesn't exist"""
    try:
        os.makedirs(projects_root, exist_ok=True)
        print(f"✓ Projects directory created/verified: {projects_root}")
        return True
    except Exception as e:
        print(f"✗ Failed to create projects directory: {e}")
        return False

def check_permissions(directory: str):
    """Check if the directory is writable"""
    try:
        test_file = os.path.join(directory, ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✓ Directory is writable: {directory}")
        return True
    except Exception as e:
        print(f"✗ Directory is not writable: {directory} - {e}")
        return False

def setup_project_steps():
    """Set up the project_steps module"""
    print("=== Project Steps Setup ===\n")
    
    # Get current directory
    current_dir = Path(__file__).parent.absolute()
    print(f"Project steps directory: {current_dir}")
    
    # Check if all required files exist
    required_files = [
        "definitions.py",
        "steps.py", 
        "__init__.py",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = current_dir / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            print(f"✓ Found: {file}")
    
    if missing_files:
        print(f"\n✗ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("\n✓ All required files found!")
    
    # Create projects directory
    projects_root = input("\nEnter projects root directory (default: /projects): ").strip()
    if not projects_root:
        projects_root = "/projects"
    
    if not create_projects_directory(projects_root):
        return False
    
    if not check_permissions(projects_root):
        return False
    
    # Create a sample configuration
    config_example = f"""
# Example configuration for using project_steps
PROJECTS_ROOT = "{projects_root}"

# Example workflow using project_steps:
# 1. create_project - Create a new project
# 2. upload_file_to_project - Upload files to the project  
# 3. list_project_files - List project contents
# 4. download_project_zip - Download project as ZIP
"""
    
    config_file = current_dir / "config_example.txt"
    with open(config_file, 'w') as f:
        f.write(config_example)
    
    print(f"\n✓ Configuration example saved: {config_file}")
    
    print("\n=== Setup Complete! ===")
    print("\nTo use project_steps with the workflow API:")
    print(f"1. Start the server: python main.py --config-root {current_dir}")
    print("2. The project_steps will be automatically loaded")
    print("3. Use the steps in your workflows:")
    print("   - create_project")
    print("   - upload_file_to_project") 
    print("   - download_project_zip")
    print("   - validate_project_token")
    print("   - list_project_files")
    
    print(f"\nProjects will be stored in: {projects_root}")
    print("See README.md for detailed usage instructions.")
    
    return True

def run_example():
    """Run the example usage script"""
    print("\n=== Running Example ===")
    
    try:
        import subprocess
        example_script = Path(__file__).parent / "example_usage.py"
        
        if example_script.exists():
            print("Running example usage script...")
            result = subprocess.run([sys.executable, str(example_script)], 
                                capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Example completed successfully!")
                print("\nExample output:")
                print(result.stdout)
            else:
                print("✗ Example failed:")
                print(result.stderr)
        else:
            print("✗ Example script not found")
            
    except Exception as e:
        print(f"✗ Failed to run example: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        run_example()
    else:
        setup_project_steps() 