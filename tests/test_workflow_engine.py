#!/usr/bin/env python3
"""
Test suite for the workflow engine and core functionality
"""
import asyncio
import sys
import os
import pytest
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core import WorkflowEngine, StepContext, project_manager, NoticeManager, StepRegistry
from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStatus
from app.step_loader import StepLoader
from app.dependency_resolver import DependencyResolver

class TestWorkflowEngine:
    """Test cases for workflow engine functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_root = os.path.join(temp_dir, "projects")
            os.makedirs(projects_root, exist_ok=True)
            yield projects_root
    
    @pytest.fixture
    def step_loader(self):
        """Create a step loader for testing"""
        return StepLoader()
    
    @pytest.fixture
    def notice_manager(self):
        """Create a notice manager for testing"""
        return NoticeManager()
    
    @pytest.fixture
    def step_registry(self):
        """Create a step registry for testing"""
        return StepRegistry()
    
    @pytest.fixture
    def workflow_engine(self, step_loader, step_registry, notice_manager):
        """Create a workflow engine for testing"""
        # Load step definitions and implementations
        step_definitions, step_implementations = step_loader.load_from_path("bundled_steps/project")
        
        # Create dependency resolver
        dependency_resolver = DependencyResolver(step_definitions)
        
        # Register steps
        for step_id, definition in step_definitions.items():
            if step_id in step_implementations:
                step_registry.register(definition)(step_implementations[step_id])
        
        # Set dependency resolver
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow engine
        engine = WorkflowEngine(step_registry, notice_manager)
        
        return engine
    
    @pytest.mark.asyncio
    async def test_workflow_engine_initialization(self, workflow_engine):
        """Test workflow engine initialization"""
        assert workflow_engine is not None
        assert hasattr(workflow_engine, 'step_registry')
        assert hasattr(workflow_engine, 'workflows')
        
        # Check that steps are registered
        assert len(workflow_engine.step_registry.definitions) > 0
        assert len(workflow_engine.step_registry.steps) > 0
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, workflow_engine, temp_project_dir):
        """Test simple workflow execution"""
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a simple workflow
            workflow_def = WorkflowDefinition(
                name="Simple Test Workflow",
                description="A simple test workflow",
                steps=[
                    WorkflowStep(
                        step_id="create_project",
                        params={"project_name": "Test Project", "description": "A test project"}
                    )
                ]
            )
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                id="test-workflow-1",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute the workflow
            await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify the workflow was completed
            assert workflow_instance.status == WorkflowStatus.COMPLETED
            
            # Verify step results
            assert len(workflow_instance.step_results) == 1
            create_project_result = workflow_instance.step_results.get("create_project")
            assert create_project_result is not None
            assert "project_id" in create_project_result
            assert "project_token" in create_project_result
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self, workflow_engine, temp_project_dir):
        """Test workflow execution with dependencies"""
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a test file
            test_file = os.path.join(temp_project_dir, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Test content')
            
            # Create a workflow with dependencies
            workflow_def = WorkflowDefinition(
                name="Dependency Test Workflow",
                description="A workflow with dependencies",
                steps=[
                    WorkflowStep(
                        step_id="create_project",
                        params={"project_name": "Dependency Test", "description": "Testing dependencies"}
                    ),
                    WorkflowStep(
                        step_id="upload_file_to_project",
                        params={"file_path": test_file, "destination_path": "data/test.txt"}
                    ),
                    WorkflowStep(
                        step_id="list_project_files",
                        params={"recursive": True, "include_hidden": False}
                    )
                ]
            )
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                id="test-workflow-2",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute the workflow
            await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify the workflow completed
            assert workflow_instance.status == WorkflowStatus.COMPLETED
            
            # Verify all steps executed
            assert len(workflow_instance.step_results) == 3
            
            # Verify create_project step
            create_result = workflow_instance.step_results["create_project"]
            assert "project_id" in create_result
            assert "project_token" in create_result
            
            # Verify upload step
            upload_result = workflow_instance.step_results["upload_file_to_project"]
            assert upload_result["upload_status"] == "success"
            assert upload_result["file_size"] > 0
            
            # Verify list files step
            list_result = workflow_instance.step_results["list_project_files"]
            # The list step should complete successfully, even if no files are found
            assert "total_files" in list_result
            assert "total_size" in list_result
            assert "files_list" in list_result
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_context_flow(self, workflow_engine, temp_project_dir):
        """Test workflow context flow between steps"""
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a workflow that tests context flow
            workflow_def = WorkflowDefinition(
                name="Context Flow Test",
                description="Testing context flow between steps",
                steps=[
                    WorkflowStep(
                        step_id="create_project",
                        params={"project_name": "Context Test"}
                    ),
                    WorkflowStep(
                        step_id="validate_project_token",
                        params={}  # Should get project_token from context
                    )
                ]
            )
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                id="test-workflow-3",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute the workflow
            await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify the workflow completed
            assert workflow_instance.status == WorkflowStatus.COMPLETED
            
            # Verify context flow
            assert "project_token" in workflow_instance.context
            
            # Verify validate step used context
            validate_result = workflow_instance.step_results["validate_project_token"]
            assert validate_result["is_valid"] is True
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow_engine):
        """Test workflow error handling"""
        # Create a workflow with invalid parameters
        workflow_def = WorkflowDefinition(
            name="Error Test Workflow",
            description="A workflow that should fail",
            steps=[
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={"project_token": "invalid_token", "file_path": "/nonexistent/file.txt"}
                )
            ]
        )
        
        # Create workflow instance
        workflow_instance = WorkflowInstance(
            id="test-workflow-4",
            definition=workflow_def,
            status=WorkflowStatus.PENDING
        )
        
        # Execute the workflow
        await workflow_engine.execute_workflow(workflow_instance)
        
        # Verify the workflow completed (even with errors)
        assert workflow_instance.status == WorkflowStatus.COMPLETED
        
        # Verify step failed
        upload_result = workflow_instance.step_results["upload_file_to_project"]
        assert upload_result["upload_status"] == "failed - invalid token"
    
    @pytest.mark.asyncio
    async def test_step_context_functionality(self, notice_manager):
        """Test StepContext functionality"""
        context = StepContext(
            workflow_id="test-workflow",
            step_id="test-step",
            notice_manager=notice_manager,
            workflow_context={}
        )
        
        # Test info message
        await context.info("Test Info", "This is a test info message")
        assert len(notice_manager.notices) == 1
        assert notice_manager.notices[0].type.value == "info"
        
        # Test success message
        await context.success("Test Success", "This is a test success message")
        assert len(notice_manager.notices) == 2
        assert notice_manager.notices[1].type.value == "success"
        
        # Test error message
        await context.error("Test Error", "This is a test error message")
        assert len(notice_manager.notices) == 3
        assert notice_manager.notices[2].type.value == "error"
        
        # Test warning message
        await context.warning("Test Warning", "This is a test warning message")
        assert len(notice_manager.notices) == 4
        assert notice_manager.notices[3].type.value == "warning"
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self, step_loader):
        """Test dependency resolution"""
        # Load step definitions
        step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
        
        # Create dependency resolver
        resolver = DependencyResolver(step_definitions)
        
        # Create a workflow with dependencies
        workflow_def = WorkflowDefinition(
            name="Dependency Resolution Test",
            description="Testing dependency resolution",
            steps=[
                WorkflowStep(step_id="create_project", params={"project_name": "Test"}),
                WorkflowStep(step_id="upload_file_to_project", params={"file_path": "/tmp/test.txt"}),
                WorkflowStep(step_id="download_project_zip", params={})
            ]
        )
        
        # Resolve dependencies
        resolution = resolver.resolve_dependencies(workflow_def)
        
        # Verify resolution
        assert len(resolution.execution_order) == 3
        assert resolution.execution_order[0] == "create_project"
        assert len(resolution.cycles) == 0
        assert len(resolution.missing_dependencies) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 