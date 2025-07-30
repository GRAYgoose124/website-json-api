 #!/usr/bin/env python3
"""
Pytest configuration for the test suite
"""
import sys
import os
import pytest
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core import initialize_core
import app.core
from app.step.registry import StepRegistry
from app.step.loader import StepLoader
from app.workflow_engine import WorkflowEngine
from app.managers.notice import NoticeManager
from app.managers.project import ProjectManager
from app.dependency_resolver import DependencyResolver
from app.models import StepDefinition, WorkflowDefinition, WorkflowInstance

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_userdata_dir():
    """Create a temporary userdata directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="session")
def initialized_core(test_userdata_dir):
    """Initialize the application core with bundled_steps for testing."""
    # Use bundled_steps for testing
    step_paths = [
        str(project_root / "bundled_steps" / "project"),
        str(project_root / "bundled_steps" / "test_suite")
    ]
    
    # Initialize core
    init_result = initialize_core(test_userdata_dir, step_paths)
    
    yield init_result

@pytest.fixture
def step_registry_fixture(initialized_core):
    """Get the step registry instance."""
    return app.core.step_registry

@pytest.fixture
def step_loader_fixture(initialized_core):
    """Get the step loader instance."""
    return app.core.step_loader

@pytest.fixture
def workflow_engine_fixture(initialized_core):
    """Get the workflow engine instance."""
    return app.core.workflow_engine

@pytest.fixture
def notice_manager_fixture(initialized_core):
    """Get the notice manager instance."""
    return app.core.notice_manager

@pytest.fixture
def project_manager_fixture(initialized_core):
    """Get the project manager instance."""
    return app.core.project_manager

@pytest.fixture
def dependency_resolver_fixture(initialized_core):
    """Get the dependency resolver instance."""
    return app.core.dependency_resolver

@pytest.fixture
def sample_workflow_definition():
    """Provide a sample workflow definition for testing."""
    return WorkflowDefinition(
        id="test_workflow",
        name="Test Workflow",
        description="A test workflow",
        steps=[
            {
                "id": "create_project",
                "name": "Create Project",
                "params": {
                    "project_name": "Test Project",
                    "description": "A test project"
                }
            },
            {
                "id": "upload_file_to_project",
                "name": "Upload File",
                "params": {
                    "project_token": "{{create_project.project_token}}",
                    "file_path": "/tmp/test.txt",
                    "destination_path": "test.txt"
                }
            }
        ]
    )

@pytest.fixture
def sample_workflow_instance(sample_workflow_definition):
    """Provide a sample workflow instance for testing."""
    return WorkflowInstance(
        id="test_instance_123",
        definition=sample_workflow_definition,
        status="pending",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    return {
        "test_string": "Hello, World!",
        "test_number": 42,
        "test_list": [1, 2, 3, 4, 5],
        "test_dict": {"key": "value", "nested": {"deep": "data"}}
    }

@pytest.fixture
def mock_step_context():
    """Provide a mock step context for testing."""
    class MockStepContext:
        def __init__(self):
            self.messages = []
        
        async def info(self, title: str, message: str):
            self.messages.append({"type": "info", "title": title, "message": message})
        
        async def success(self, title: str, message: str):
            self.messages.append({"type": "success", "title": title, "message": message})
        
        async def error(self, title: str, message: str):
            self.messages.append({"type": "error", "title": title, "message": message})
        
        async def warning(self, title: str, message: str):
            self.messages.append({"type": "warning", "title": title, "message": message})
    
    return MockStepContext()

@pytest.fixture(autouse=True)
def clear_notices(notice_manager_fixture):
    """Clear notices before each test to ensure isolation."""
    notice_manager_fixture.clear_notices()
    yield 