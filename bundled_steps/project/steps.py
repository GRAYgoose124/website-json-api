import asyncio
import os
import uuid
import hashlib
import shutil
import zipfile
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from app.core import StepContext, project_manager


async def create_project(params: Dict[str, Any], context: StepContext):
    """Creates a new project directory with UUID and generates a project token"""
    project_name = params.get('project_name', 'New Project')
    description = params.get('description', '')
    
    await context.info("Creating Project", f"Creating project: {project_name}")
    
    # Use the project manager to create the project (secure)
    project_info = project_manager.create_project(project_name, description)
    
    project_id = project_info['project_id']
    project_path = project_info['project_path']
    project_token = project_info['project_token']
    
    await context.info("Project ID Generated", f"Project ID: {project_id}")
    await context.info("Directory Created", f"Project directory created at: {project_path}")
    await context.success("Project Created", f"Project '{project_name}' created successfully")
    
    return {
        'project_id': project_id,
        'project_path': project_path,
        'project_token': project_token
    }


async def upload_file_to_project(params: Dict[str, Any], context: StepContext):
    """Uploads a local file to the specified project directory"""
    project_token = params.get('project_token')
    file_path = params.get('file_path')
    destination_path = params.get('destination_path', '')
    overwrite = params.get('overwrite', False)
    
    await context.info("Validating Token", "Validating project token...")
    
    # Validate project token using project manager
    project_info = project_manager.validate_token(project_token)
    if not project_info:
        await context.error("Invalid Token", "Project token is invalid or expired")
        return {
            'uploaded_file_path': '',
            'file_size': 0,
            'upload_status': 'failed - invalid token'
        }
    
    project_path = project_info['project_path']
    
    await context.info("Token Validated", f"Accessing project: {project_info['project_name']}")
    
    # Check if source file exists
    if not os.path.exists(file_path):
        await context.error("File Not Found", f"Source file not found: {file_path}")
        return {
            'uploaded_file_path': '',
            'file_size': 0,
            'upload_status': 'failed - source file not found'
        }
    
    # Determine destination path
    if destination_path:
        dest_path = os.path.join(project_path, destination_path)
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    else:
        # Use original filename in project root
        filename = os.path.basename(file_path)
        dest_path = os.path.join(project_path, filename)
    
    # Check if destination file exists
    if os.path.exists(dest_path) and not overwrite:
        await context.error("File Exists", f"Destination file already exists: {dest_path}")
        return {
            'uploaded_file_path': '',
            'file_size': 0,
            'upload_status': 'failed - file exists and overwrite disabled'
        }
    
    await context.info("Uploading File", f"Copying {file_path} to {dest_path}")
    
    try:
        # Copy file
        shutil.copy2(file_path, dest_path)
        file_size = os.path.getsize(dest_path)
        
        await context.success("Upload Complete", f"File uploaded successfully: {os.path.basename(file_path)}")
        
        return {
            'uploaded_file_path': dest_path,
            'file_size': file_size,
            'upload_status': 'success'
        }
        
    except Exception as e:
        await context.error("Upload Failed", f"Failed to upload file: {str(e)}")
        return {
            'uploaded_file_path': '',
            'file_size': 0,
            'upload_status': f'failed - {str(e)}'
        }


async def download_project_zip(params: Dict[str, Any], context: StepContext):
    """Creates a ZIP archive of the project and provides download path"""
    project_token = params.get('project_token')
    include_hidden = params.get('include_hidden', False)
    compression_level = params.get('compression_level', 6)
    
    await context.info("Validating Token", "Validating project token...")
    
    # Validate project token using project manager
    project_info = project_manager.validate_token(project_token)
    if not project_info:
        await context.error("Invalid Token", "Project token is invalid or expired")
        return {
            'zip_file_path': '',
            'zip_file_size': 0,
            'files_included': 0
        }
    
    project_path = project_info['project_path']
    project_name = project_info['project_name']
    
    await context.info("Token Validated", f"Preparing ZIP for project: {project_name}")
    
    # Create downloads directory if it doesn't exist
    downloads_dir = os.path.join(os.path.dirname(project_path), 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Generate ZIP filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{project_name}_{timestamp}.zip"
    zip_path = os.path.join(downloads_dir, zip_filename)
    
    await context.info("Creating ZIP", f"Creating ZIP archive: {zip_filename}")
    
    try:
        files_included = 0
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
            for root, dirs, files in os.walk(project_path):
                # Filter hidden files/directories if not included
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path for ZIP
                    arcname = os.path.relpath(file_path, project_path)
                    zipf.write(file_path, arcname)
                    files_included += 1
                    
                    if files_included % 10 == 0:
                        await context.info("ZIP Progress", f"Added {files_included} files to ZIP")
        
        zip_file_size = os.path.getsize(zip_path)
        
        await context.success("ZIP Created", f"ZIP archive created successfully with {files_included} files")
        
        # Emit download notification
        await context.info("Download Ready", f"ZIP file ready for download: {zip_filename}")
        
        # Create a download URL for the browser - use just the filename
        # The download endpoint will search for the file in allowed directories
        download_url = f"/download/{zip_filename}"
        
        return {
            'zip_file_path': zip_path,
            'zip_file_size': zip_file_size,
            'files_included': files_included,
            'download_url': download_url,
            'download_filename': zip_filename
        }
        
    except Exception as e:
        await context.error("ZIP Creation Failed", f"Failed to create ZIP: {str(e)}")
        return {
            'zip_file_path': '',
            'zip_file_size': 0,
            'files_included': 0
        }


async def validate_project_token(params: Dict[str, Any], context: StepContext):
    """Validates a project token and returns project information"""
    project_token = params.get('project_token')
    
    await context.info("Validating Token", "Checking project token validity...")
    
    project_info = project_manager.validate_token(project_token)
    if project_info:
        await context.success("Token Valid", f"Token validated for project: {project_info['project_name']}")
        
        return {
            'is_valid': True,
            'project_id': project_info['project_id'],
            'project_path': project_info['project_path'],
            'validation_message': f"Token is valid for project: {project_info['project_name']}"
        }
    else:
        await context.error("Token Invalid", "Project token is invalid or expired")
        
        return {
            'is_valid': False,
            'project_id': None,
            'project_path': None,
            'validation_message': "Project token is invalid or expired"
        }


async def list_project_files(params: Dict[str, Any], context: StepContext):
    """Lists all files in the project directory"""
    project_token = params.get('project_token')
    recursive = params.get('recursive', True)
    include_hidden = params.get('include_hidden', False)
    
    await context.info("Validating Token", "Validating project token...")
    
    # Validate project token using project manager
    project_info = project_manager.validate_token(project_token)
    if not project_info:
        await context.error("Invalid Token", "Project token is invalid or expired")
        return {
            'files_list': [],
            'total_files': 0,
            'total_size': 0
        }
    
    project_path = project_info['project_path']
    project_name = project_info['project_name']
    
    await context.info("Token Validated", f"Listing files for project: {project_name}")
    
    try:
        files_list = []
        total_size = 0
        
        if recursive:
            # Walk through all subdirectories
            for root, dirs, files in os.walk(project_path):
                # Filter hidden files/directories if not included
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    file_size = os.path.getsize(file_path)
                    file_stat = os.stat(file_path)
                    
                    file_info = {
                        'name': file,
                        'path': relative_path,
                        'full_path': file_path,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'is_file': True
                    }
                    
                    files_list.append(file_info)
                    total_size += file_size
        else:
            # Only list files in project root
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                
                # Skip hidden items if not included
                if not include_hidden and item.startswith('.'):
                    continue
                
                if os.path.isfile(item_path):
                    file_size = os.path.getsize(item_path)
                    file_stat = os.stat(item_path)
                    
                    file_info = {
                        'name': item,
                        'path': item,
                        'full_path': item_path,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'is_file': True
                    }
                    
                    files_list.append(file_info)
                    total_size += file_size
        
        total_files = len(files_list)
        
        await context.success("Files Listed", f"Found {total_files} files in project")
        
        return {
            'files_list': files_list,
            'total_files': total_files,
            'total_size': total_size
        }
        
    except Exception as e:
        await context.error("Listing Failed", f"Failed to list project files: {str(e)}")
        return {
            'files_list': [],
            'total_files': 0,
            'total_size': 0
        } 