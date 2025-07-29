#!/usr/bin/env python3
"""
Example usage of project management steps
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core import StepContext, notice_manager
from project_steps.steps import (
    create_project,
    upload_file_to_project,
    download_project_zip,
    validate_project_token,
    list_project_files
)


async def main():
    """Example workflow demonstrating project management steps"""
    
    print("🚀 Project Management Workflow Example")
    print("=" * 50)
    
    # Create a mock context for demonstration
    context = StepContext(
        workflow_id="example-workflow",
        step_id="example",
        notice_manager=notice_manager,
        workflow_context={}
    )
    
    # Step 1: Create a new project
    print("\n📁 Step 1: Creating a new project...")
    project_result = await create_project({
        'project_name': 'My Data Science Project',
        'description': 'A comprehensive data analysis workflow'
    }, context)
    
    print(f"✅ Project created successfully!")
    print(f"   Project ID: {project_result['project_id']}")
    print(f"   Project path: {project_result['project_path']}")
    print(f"   Project token: {project_result['project_token'][:16]}...\n")
    
    # Step 2: Upload a file to the project
    print("📤 Step 2: Uploading a file to the project...")
    
    # Create a sample file for demonstration
    sample_file_path = "/tmp/sample_data.csv"
    with open(sample_file_path, 'w') as f:
        f.write("id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300\n")
    
    upload_result = await upload_file_to_project({
        'project_token': project_result['project_token'],
        'file_path': sample_file_path,
        'destination_path': 'data/input/sample_data.csv',
        'overwrite': True
    }, context)
    
    print(f"✅ File uploaded successfully!")
    print(f"   Uploaded file: {upload_result['uploaded_file_path']}")
    print(f"   File size: {upload_result['file_size']} bytes")
    print(f"   Status: {upload_result['upload_status']}\n")
    
    # Step 3: List project files
    print("📋 Step 3: Listing project files...")
    files_result = await list_project_files({
        'project_token': project_result['project_token'],
        'recursive': True,
        'include_hidden': False
    }, context)
    
    print(f"✅ Files listed successfully!")
    print(f"   Total files: {files_result['total_files']}")
    print(f"   Total size: {files_result['total_size']} bytes")
    print("   Files:")
    for file_info in files_result['files_list']:
        print(f"     - {file_info['path']} ({file_info['size']} bytes)")
    print()
    
    # Step 4: Validate the project token
    print("🔐 Step 4: Validating project token...")
    validation_result = await validate_project_token({
        'project_token': project_result['project_token']
    }, context)
    
    print(f"✅ Token validation completed!")
    print(f"   Is valid: {validation_result['is_valid']}")
    print(f"   Project ID: {validation_result['project_id']}")
    print(f"   Message: {validation_result['validation_message']}\n")
    
    # Step 5: Create a ZIP download
    print("📥 Step 5: Creating project ZIP download...")
    zip_result = await download_project_zip({
        'project_token': project_result['project_token'],
        'include_hidden': False,
        'compression_level': 6
    }, context)
    
    print(f"✅ ZIP created successfully!")
    print(f"   ZIP file: {zip_result['zip_file_path']}")
    print(f"   ZIP size: {zip_result['zip_file_size']} bytes")
    print(f"   Files included: {zip_result['files_included']}\n")
    
    # Step 6: Test invalid token
    print("❌ Step 6: Testing invalid token...")
    invalid_result = await validate_project_token({
        'project_token': 'invalid_token_123'
    }, context)
    
    print(f"✅ Invalid token test completed!")
    print(f"   Is valid: {invalid_result['is_valid']}")
    print(f"   Message: {invalid_result['validation_message']}\n")
    
    # Cleanup
    print("🧹 Cleaning up...")
    try:
        os.remove(sample_file_path)
        print("✅ Sample file removed")
    except:
        pass
    
    print("\n🎉 Workflow completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main()) 