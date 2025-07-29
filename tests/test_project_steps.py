#!/usr/bin/env python3
"""
Test suite for the project management functionality.
"""

import asyncio
import os
import tempfile
import pytest
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core import StepContext, project_manager, NoticeManager
from app.step_loader import StepLoader

class TestProjectManagement:
    """Test cases for project management functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_root = os.path.join(temp_dir, "projects")
            os.makedirs(projects_root, exist_ok=True)
            yield projects_root
    
    @pytest.fixture
    def notice_manager(self):
        """Create a notice manager for testing"""
        return NoticeManager()
    
    @pytest.fixture
    def context(self, notice_manager):
        """Create a real StepContext for testing"""
        return StepContext(
            workflow_id="test-workflow",
            step_id="test-step",
            notice_manager=notice_manager,
            workflow_context={}
        )
    
    @pytest.fixture
    def step_loader(self):
        """Create a step loader for testing"""
        return StepLoader()
    
    @pytest.mark.asyncio
    async def test_project_manager_creation(self, temp_project_dir):
        """Test project manager functionality"""
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Test project creation
            project_info = project_manager.create_project("Test Project", "A test project")
            
            assert 'project_id' in project_info
            assert 'project_path' in project_info
            assert 'project_token' in project_info
            assert os.path.exists(project_info['project_path'])
            assert len(project_info['project_token']) == 64  # SHA-256 hash length
            
            # Check that metadata file was created
            metadata_file = os.path.join(project_info['project_path'], '.project_metadata.json')
            assert os.path.exists(metadata_file)
            
            # Test token validation
            assert project_manager.validate_token(project_info['project_token']) is not None
            assert project_manager.validate_token('invalid_token') is None
            
            # Test project path retrieval
            retrieved_path = project_manager.get_project_path(project_info['project_token'])
            assert retrieved_path == project_info['project_path']
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_create_project_step(self, temp_project_dir, context, step_loader):
        """Test create_project step"""
        # Load step implementation
        _, step_implementations = step_loader.load_from_path("project_steps")
        create_project_func = step_implementations['create_project']
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            result = await create_project_func({
                'project_name': 'Test Project',
                'description': 'A test project'
            }, context)
            
            assert 'project_id' in result
            assert 'project_path' in result
            assert 'project_token' in result
            assert os.path.exists(result['project_path'])
            assert len(result['project_token']) == 64
            
            # Check that metadata file was created
            metadata_file = os.path.join(result['project_path'], '.project_metadata.json')
            assert os.path.exists(metadata_file)
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_upload_file_to_project_step(self, temp_project_dir, context, step_loader):
        """Test upload_file_to_project step"""
        # Load step implementations
        _, step_implementations = step_loader.load_from_path("project_steps")
        create_project_func = step_implementations['create_project']
        upload_file_func = step_implementations['upload_file_to_project']
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # First create a project
            project_result = await create_project_func({
                'project_name': 'Upload Test'
            }, context)
            
            # Create a test file
            test_file = os.path.join(temp_project_dir, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Test content')
            
            # Upload the file
            upload_result = await upload_file_func({
                'project_token': project_result['project_token'],
                'file_path': test_file,
                'destination_path': 'data/test_file.txt'
            }, context)
            
            assert upload_result['upload_status'] == 'success'
            assert upload_result['file_size'] > 0
            assert os.path.exists(upload_result['uploaded_file_path'])
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_upload_file_invalid_token(self, temp_project_dir, context, step_loader):
        """Test file upload with invalid token"""
        # Load step implementation
        _, step_implementations = step_loader.load_from_path("project_steps")
        upload_file_func = step_implementations['upload_file_to_project']
        
        # Create a test file
        test_file = os.path.join(temp_project_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        # Try to upload with invalid token
        upload_result = await upload_file_func({
            'project_token': 'invalid_token',
            'file_path': test_file
        }, context)
        
        assert upload_result['upload_status'] == 'failed - invalid token'
        assert upload_result['file_size'] == 0
    
    @pytest.mark.asyncio
    async def test_validate_project_token_step(self, temp_project_dir, context, step_loader):
        """Test validate_project_token step"""
        # Load step implementations
        _, step_implementations = step_loader.load_from_path("project_steps")
        create_project_func = step_implementations['create_project']
        validate_token_func = step_implementations['validate_project_token']
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a project
            project_result = await create_project_func({
                'project_name': 'Token Test'
            }, context)
            
            # Validate valid token
            valid_result = await validate_token_func({
                'project_token': project_result['project_token']
            }, context)
            
            assert valid_result['is_valid'] is True
            assert valid_result['project_id'] == project_result['project_id']
            
            # Validate invalid token
            invalid_result = await validate_token_func({
                'project_token': 'invalid_token'
            }, context)
            
            assert invalid_result['is_valid'] is False
            assert invalid_result['project_id'] is None
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_list_project_files_step(self, temp_project_dir, context, step_loader):
        """Test list_project_files step"""
        # Load step implementations
        _, step_implementations = step_loader.load_from_path("project_steps")
        create_project_func = step_implementations['create_project']
        upload_file_func = step_implementations['upload_file_to_project']
        list_files_func = step_implementations['list_project_files']
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a project
            project_result = await create_project_func({
                'project_name': 'List Test'
            }, context)
            
            # Create some test files
            test_file1 = os.path.join(temp_project_dir, 'test1.txt')
            test_file2 = os.path.join(temp_project_dir, 'test2.txt')
            
            with open(test_file1, 'w') as f:
                f.write('Test content 1')
            with open(test_file2, 'w') as f:
                f.write('Test content 2')
            
            # Upload files
            await upload_file_func({
                'project_token': project_result['project_token'],
                'file_path': test_file1,
                'destination_path': 'file1.txt'
            }, context)
            
            await upload_file_func({
                'project_token': project_result['project_token'],
                'file_path': test_file2,
                'destination_path': 'subdir/file2.txt'
            }, context)
            
            # List files
            list_result = await list_files_func({
                'project_token': project_result['project_token'],
                'recursive': True,
                'include_hidden': False
            }, context)
            
            assert list_result['total_files'] >= 2  # uploaded files (metadata is hidden)
            assert list_result['total_size'] > 0
            assert len(list_result['files_list']) >= 2
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_download_project_zip_step(self, temp_project_dir, context, step_loader):
        """Test download_project_zip step"""
        # Load step implementations
        _, step_implementations = step_loader.load_from_path("project_steps")
        create_project_func = step_implementations['create_project']
        upload_file_func = step_implementations['upload_file_to_project']
        download_zip_func = step_implementations['download_project_zip']
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a project
            project_result = await create_project_func({
                'project_name': 'ZIP Test'
            }, context)
            
            # Create and upload a test file
            test_file = os.path.join(temp_project_dir, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Test content for ZIP')
            
            await upload_file_func({
                'project_token': project_result['project_token'],
                'file_path': test_file,
                'destination_path': 'data/test.txt'
            }, context)
            
            # Create ZIP
            zip_result = await download_zip_func({
                'project_token': project_result['project_token'],
                'include_hidden': False,
                'compression_level': 6
            }, context)
            
            assert zip_result['zip_file_path'] != ''
            assert zip_result['zip_file_size'] > 0
            assert zip_result['files_included'] >= 1  # uploaded file (metadata is hidden)
            assert os.path.exists(zip_result['zip_file_path'])
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"]) 