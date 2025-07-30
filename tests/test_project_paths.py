import pytest
import os
from pathlib import Path
from app.managers.project import ProjectManager


class TestProjectPaths:
    """Test that project paths are properly handled for security."""
    
    def test_project_paths_are_relative(self):
        """Test that project paths are stored as relative paths."""
        # Create a temporary projects root
        temp_projects_root = Path("/tmp/test_projects")
        temp_projects_root.mkdir(exist_ok=True)
        
        project_manager = ProjectManager()
        project_manager.projects_root = temp_projects_root
        
        # Create a project
        project_info = project_manager.create_project("Test Project", "Test Description")
        
        # Verify that both absolute and relative paths are stored
        assert 'project_path' in project_info
        assert 'project_path_relative' in project_info
        
        # Verify the relative path is actually relative
        absolute_path = Path(project_info['project_path'])
        relative_path = Path(project_info['project_path_relative'])
        
        assert absolute_path.is_absolute()
        assert not relative_path.is_absolute()
        assert relative_path == absolute_path.relative_to(temp_projects_root)
        
        # Verify we can retrieve the relative path
        retrieved_relative = project_manager.get_project_path_relative(project_info['project_token'])
        assert retrieved_relative == project_info['project_path_relative']
        
        # Clean up
        import shutil
        shutil.rmtree(temp_projects_root)
    
    def test_project_paths_dont_expose_filesystem(self):
        """Test that relative paths don't expose filesystem structure."""
        temp_projects_root = Path("/tmp/test_projects")
        temp_projects_root.mkdir(exist_ok=True)
        
        project_manager = ProjectManager()
        project_manager.projects_root = temp_projects_root
        
        # Create a project
        project_info = project_manager.create_project("Test Project", "Test Description")
        
        # The relative path should not contain the full filesystem path
        relative_path = project_info['project_path_relative']
        absolute_path = project_info['project_path']
        
        # Relative path should not contain the projects root
        assert str(temp_projects_root) not in relative_path
        
        # Relative path should be safe to expose via API
        assert not relative_path.startswith('/')
        assert not relative_path.startswith('..')
        
        # Clean up
        import shutil
        shutil.rmtree(temp_projects_root)
    
    def test_project_paths_consistency(self):
        """Test that project paths are consistent between creation and validation."""
        temp_projects_root = Path("/tmp/test_projects")
        temp_projects_root.mkdir(exist_ok=True)
        
        project_manager = ProjectManager()
        project_manager.projects_root = temp_projects_root
        
        # Create a project
        project_info = project_manager.create_project("Test Project", "Test Description")
        token = project_info['project_token']
        
        # Validate the token
        validated_info = project_manager.validate_token(token)
        
        # Verify paths are consistent
        assert validated_info['project_path'] == project_info['project_path']
        assert validated_info['project_path_relative'] == project_info['project_path_relative']
        
        # Clean up
        import shutil
        shutil.rmtree(temp_projects_root) 