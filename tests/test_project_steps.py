#!/usr/bin/env python3
"""
Test suite for the project_steps module.
"""

import asyncio
import os
import tempfile
import pytest
from pathlib import Path

# Import the project steps
from steps import (
    create_project,
    upload_file_to_project,
    download_project_zip,
    validate_project_token,
    list_project_files
)

# Mock StepContext for testing
class MockStepContext:
    def __init__(self):
        self.messages = []
    
    async def info(self, title, message):
        self.messages.append(('info', title, message))
    
    async def success(self, title, message):
        self.messages.append(('success', title, message))
    
    async def error(self, title, message):
        self.messages.append(('error', title, message))
    
    async def warning(self, title, message):
        self.messages.append(('warning', title, message))

class TestProjectSteps:
    """Test cases for project steps functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_root = os.path.join(temp_dir, "projects")
            os.makedirs(projects_root, exist_ok=True)
            yield projects_root
    
    @pytest.fixture
    def context(self):
        """Create a mock context for testing"""
        return MockStepContext()
    
    @pytest.mark.asyncio
    async def test_create_project(self, temp_project_dir, context):
        """Test project creation"""
        result = await create_project({
            'project_name': 'Test Project',
            'projects_root': temp_project_dir,
            'description': 'A test project'
        }, context)
        
        assert 'project_id' in result
        assert 'project_path' in result
        assert 'project_token' in result
        assert os.path.exists(result['project_path'])
        assert len(result['project_token']) == 64  # SHA-256 hash length
        
        # Check that metadata file was created
        metadata_file = os.path.join(result['project_path'], '.project_metadata.json')
        assert os.path.exists(metadata_file)
    
    @pytest.mark.asyncio
    async def test_upload_file_to_project(self, temp_project_dir, context):
        """Test file upload to project"""
        # First create a project
        project_result = await create_project({
            'project_name': 'Upload Test',
            'projects_root': temp_project_dir
        }, context)
        
        # Create a test file
        test_file = os.path.join(temp_project_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        # Upload the file
        upload_result = await upload_file_to_project({
            'project_token': project_result['project_token'],
            'file_path': test_file,
            'destination_path': 'data/test_file.txt'
        }, context)
        
        assert upload_result['upload_status'] == 'success'
        assert upload_result['file_size'] > 0
        assert os.path.exists(upload_result['uploaded_file_path'])
    
    @pytest.mark.asyncio
    async def test_upload_file_invalid_token(self, temp_project_dir, context):
        """Test file upload with invalid token"""
        # Create a test file
        test_file = os.path.join(temp_project_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        # Try to upload with invalid token
        upload_result = await upload_file_to_project({
            'project_token': 'invalid_token',
            'file_path': test_file
        }, context)
        
        assert upload_result['upload_status'] == 'failed - invalid token'
        assert upload_result['file_size'] == 0
    
    @pytest.mark.asyncio
    async def test_validate_project_token(self, temp_project_dir, context):
        """Test token validation"""
        # Create a project
        project_result = await create_project({
            'project_name': 'Token Test',
            'projects_root': temp_project_dir
        }, context)
        
        # Validate valid token
        valid_result = await validate_project_token({
            'project_token': project_result['project_token']
        }, context)
        
        assert valid_result['is_valid'] is True
        assert valid_result['project_id'] == project_result['project_id']
        
        # Validate invalid token
        invalid_result = await validate_project_token({
            'project_token': 'invalid_token'
        }, context)
        
        assert invalid_result['is_valid'] is False
        assert invalid_result['project_id'] is None
    
    @pytest.mark.asyncio
    async def test_list_project_files(self, temp_project_dir, context):
        """Test listing project files"""
        # Create a project
        project_result = await create_project({
            'project_name': 'List Test',
            'projects_root': temp_project_dir
        }, context)
        
        # Create some test files
        test_file1 = os.path.join(temp_project_dir, 'test1.txt')
        test_file2 = os.path.join(temp_project_dir, 'test2.txt')
        
        with open(test_file1, 'w') as f:
            f.write('Test content 1')
        with open(test_file2, 'w') as f:
            f.write('Test content 2')
        
        # Upload files
        await upload_file_to_project({
            'project_token': project_result['project_token'],
            'file_path': test_file1,
            'destination_path': 'file1.txt'
        }, context)
        
        await upload_file_to_project({
            'project_token': project_result['project_token'],
            'file_path': test_file2,
            'destination_path': 'subdir/file2.txt'
        }, context)
        
        # List files
        list_result = await list_project_files({
            'project_token': project_result['project_token'],
            'recursive': True,
            'include_hidden': False
        }, context)
        
        assert list_result['total_files'] >= 3  # 2 uploaded files + metadata file
        assert list_result['total_size'] > 0
        assert len(list_result['files_list']) >= 3
    
    @pytest.mark.asyncio
    async def test_download_project_zip(self, temp_project_dir, context):
        """Test project ZIP download"""
        # Create a project
        project_result = await create_project({
            'project_name': 'ZIP Test',
            'projects_root': temp_project_dir
        }, context)
        
        # Create and upload a test file
        test_file = os.path.join(temp_project_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content for ZIP')
        
        await upload_file_to_project({
            'project_token': project_result['project_token'],
            'file_path': test_file,
            'destination_path': 'data/test.txt'
        }, context)
        
        # Create ZIP
        zip_result = await download_project_zip({
            'project_token': project_result['project_token'],
            'include_hidden': False,
            'compression_level': 6
        }, context)
        
        assert zip_result['zip_file_path'] != ''
        assert zip_result['zip_file_size'] > 0
        assert zip_result['files_included'] >= 2  # uploaded file + metadata
        assert os.path.exists(zip_result['zip_file_path'])

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"]) 