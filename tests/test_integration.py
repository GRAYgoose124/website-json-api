import pytest
import tempfile
import shutil
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.api_v2 import app


class TestIntegration:
    """Integration tests for the API functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test directories
        self.uploads_dir = Path(self.temp_dir) / "uploads"
        self.projects_dir = Path(self.temp_dir) / "projects"
        self.uploads_dir.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)
        
        # Patch the app state
        app.state.uploads_dir = self.uploads_dir
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_health_check(self):
        """Test that health check endpoint works."""
        response = self.client.get("/health")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
    
    def test_config_endpoint(self):
        """Test that config endpoint works."""
        response = self.client.get("/config")
        assert response.status_code == 200
        result = response.json()
        assert "api_version" in result
        assert "features" in result
    
    def test_steps_categories_endpoint(self):
        """Test that steps categories endpoint works."""
        response = self.client.get("/steps/categories")
        assert response.status_code == 200
        result = response.json()
        assert "categories" in result
        assert isinstance(result["categories"], list)
    
    def test_steps_tags_endpoint(self):
        """Test that steps tags endpoint works."""
        response = self.client.get("/steps/tags")
        assert response.status_code == 200
        result = response.json()
        assert "tags" in result
        assert isinstance(result["tags"], list)
    
    def test_workflow_validation_endpoint(self):
        """Test that workflow validation endpoint works."""
        workflow_definition = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "create_project",
                    "params": {
                        "project_name": "Test Project",
                        "description": "Test Description"
                    }
                }
            ]
        }
        
        response = self.client.post("/workflows/validate", json=workflow_definition)
        assert response.status_code == 200
        result = response.json()
        assert "execution_order" in result
        assert "cycles" in result
        assert "missing_dependencies" in result
    
    def test_workflow_dependency_resolution(self):
        """Test that workflow dependency resolution works."""
        workflow_definition = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "create_project",
                    "params": {
                        "project_name": "Test Project",
                        "description": "Test Description"
                    }
                },
                {
                    "step_id": "upload_file_to_project",
                    "params": {
                        "project_token": "{{project_token}}",
                        "file_path": "/tmp/test.txt"
                    }
                }
            ]
        }
        
        response = self.client.post("/workflows/resolve-dependencies", json=workflow_definition)
        assert response.status_code == 200
        result = response.json()
        assert "execution_order" in result
        assert "cycles" in result
        assert "missing_dependencies" in result
        assert isinstance(result["execution_order"], list)
    
    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/steps",
            "/notices", 
            "/workflows",
            "/upload-file"
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint) if endpoint != "/upload-file" else self.client.post(endpoint)
            assert response.status_code == 401  # Unauthorized
    
    def test_project_paths_are_relative(self):
        """Test that project paths are properly handled."""
        # This test verifies the project manager functionality
        from app.managers.project import ProjectManager
        
        project_manager = ProjectManager()
        project_manager.projects_root = self.projects_dir
        
        # Create a project
        project_info = project_manager.create_project("Test Project", "Test Description")
        
        # Verify both absolute and relative paths are stored
        assert 'project_path' in project_info
        assert 'project_path_relative' in project_info
        
        # Verify the relative path is actually relative
        absolute_path = Path(project_info['project_path'])
        relative_path = Path(project_info['project_path_relative'])
        
        assert absolute_path.is_absolute()
        assert not relative_path.is_absolute()
        assert relative_path == absolute_path.relative_to(self.projects_dir)
        
        # Verify we can retrieve the relative path
        retrieved_relative = project_manager.get_project_path_relative(project_info['project_token'])
        assert retrieved_relative == project_info['project_path_relative']
    
    def test_upload_file_structure(self):
        """Test that upload file structure is correct."""
        # Create a test file
        test_file_content = b"test file content"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(test_file_content)
            temp_file_path = temp_file.name
        
        try:
            # Test that the upload endpoint exists and requires auth
            with open(temp_file_path, 'rb') as f:
                response = self.client.post(
                    "/upload-file",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            # Should require authentication
            assert response.status_code == 401
            
        finally:
            os.unlink(temp_file_path)
    
    def test_workflow_copy_endpoints_exist(self):
        """Test that workflow copy endpoints exist and require auth."""
        # Test copy endpoint
        response = self.client.post("/workflows/test-id/copy")
        assert response.status_code == 401  # Requires authentication
        
        # Test definition endpoint
        response = self.client.get("/workflows/test-id/definition")
        assert response.status_code == 401  # Requires authentication 