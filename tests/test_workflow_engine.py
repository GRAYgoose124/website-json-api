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

from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStatus
from app.step.context import StepContext

class TestWorkflowEngine:
    """Test cases for workflow engine functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_root = os.path.join(temp_dir, "projects")
            os.makedirs(projects_root, exist_ok=True)
            yield projects_root
    
    @pytest.mark.asyncio
    async def test_workflow_engine_initialization(self, workflow_engine_fixture):
        """Test workflow engine initialization"""
        workflow_engine = workflow_engine_fixture
        assert workflow_engine is not None
        assert hasattr(workflow_engine, 'step_registry')
        assert hasattr(workflow_engine, 'workflows')
        
        # Check that steps are registered
        assert len(workflow_engine.step_registry.definitions) > 0
        assert len(workflow_engine.step_registry.steps) > 0
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, workflow_engine_fixture, project_manager_fixture, temp_project_dir):
        """Test simple workflow execution"""
        workflow_engine = workflow_engine_fixture
        project_manager = project_manager_fixture
        
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
                id="test_instance_1",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute workflow
            result = await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify results
            assert result.status == WorkflowStatus.COMPLETED
            assert len(result.step_results) == 1
            
            # Get the step result (it's stored by step_id)
            step_result = result.step_results["create_project"]
            assert "project_id" in step_result
            assert "project_token" in step_result
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self, workflow_engine_fixture, project_manager_fixture, temp_project_dir):
        """Test workflow execution with step dependencies"""
        workflow_engine = workflow_engine_fixture
        project_manager = project_manager_fixture
        
        # Temporarily set the projects root
        original_root = project_manager.projects_root
        project_manager.projects_root = Path(temp_project_dir)
        
        try:
            # Create a test file for upload
            test_file_path = os.path.join(temp_project_dir, 'test.txt')
            with open(test_file_path, 'w') as f:
                f.write('Test content for upload')
            
            # Create a workflow with dependencies
            workflow_def = WorkflowDefinition(
                name="Dependency Test Workflow",
                description="A workflow with step dependencies",
                steps=[
                    WorkflowStep(
                        step_id="create_project",
                        params={"project_name": "Dependency Test", "description": "Testing dependencies"}
                    ),
                    WorkflowStep(
                        step_id="upload_file_to_project",
                        params={
                            "project_token": "{{create_project.project_token}}",
                            "file_path": test_file_path,
                            "destination_path": "test.txt"
                        }
                    )
                ]
            )
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                id="test_instance_2",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute workflow
            result = await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify results
            assert result.status == WorkflowStatus.COMPLETED
            assert len(result.step_results) == 2
            
            # Check first step
            create_project_result = result.step_results["create_project"]
            assert "project_id" in create_project_result
            assert "project_token" in create_project_result
            
            # Check second step
            upload_result = result.step_results["upload_file_to_project"]
            assert "upload_status" in upload_result
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_context_flow(self, workflow_engine_fixture, project_manager_fixture, temp_project_dir):
        """Test workflow context flow between steps"""
        workflow_engine = workflow_engine_fixture
        project_manager = project_manager_fixture
        
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
                        params={"project_name": "Context Test", "description": "Testing context flow"}
                    ),
                    WorkflowStep(
                        step_id="list_project_files",
                        params={"project_token": "{{create_project.project_token}}"}
                    )
                ]
            )
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                id="test_instance_3",
                definition=workflow_def,
                status=WorkflowStatus.PENDING
            )
            
            # Execute workflow
            result = await workflow_engine.execute_workflow(workflow_instance)
            
            # Verify results
            assert result.status == WorkflowStatus.COMPLETED
            assert len(result.step_results) == 2
            
            # Check that context was properly forwarded
            list_files_result = result.step_results["list_project_files"]
            assert "total_files" in list_files_result
            
        finally:
            # Restore original projects root
            project_manager.projects_root = original_root
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow_engine_fixture):
        """Test workflow error handling"""
        workflow_engine = workflow_engine_fixture
        
        # Create a workflow with invalid step
        workflow_def = WorkflowDefinition(
            name="Error Test Workflow",
            description="A workflow that should fail",
            steps=[
                WorkflowStep(
                    step_id="nonexistent_step",
                    params={"param1": "value1"}
                )
            ]
        )
        
        # Create workflow instance
        workflow_instance = WorkflowInstance(
            id="test_instance_4",
            definition=workflow_def,
            status=WorkflowStatus.PENDING
        )
        
        # Execute workflow
        result = await workflow_engine.execute_workflow(workflow_instance)
        
        # Verify error handling
        assert result.status == WorkflowStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_step_context_functionality(self, notice_manager_fixture):
        """Test step context functionality"""
        notice_manager = notice_manager_fixture
        
        # Create a step context
        context = StepContext("test_workflow", "test_step", notice_manager, {})
        
        # Test context methods
        await context.info("Test Info", "This is a test info message")
        await context.success("Test Success", "This is a test success message")
        await context.error("Test Error", "This is a test error message")
        await context.warning("Test Warning", "This is a test warning message")
        
        # Verify that notices were created
        notices = notice_manager.get_notices()
        assert len(notices) >= 4
        
        # Check that notices have correct workflow and step IDs
        for notice in notices:
            assert notice.workflow_id == "test_workflow"
            assert notice.step_id == "test_step"
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self, step_loader_fixture, dependency_resolver_fixture):
        """Test dependency resolution functionality"""
        step_loader = step_loader_fixture
        dependency_resolver = dependency_resolver_fixture
        
        # Load step definitions
        step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
        
        # Create a workflow definition with dependencies
        workflow_def = WorkflowDefinition(
            name="Dependency Resolution Test",
            description="Testing dependency resolution",
            steps=[
                WorkflowStep(
                    step_id="create_project",
                    params={"project_name": "Test", "description": "Test project"}
                ),
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={
                        "project_token": "{{create_project.project_token}}",
                        "file_path": "/tmp/test.txt"
                    }
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow_def)
        
        # Verify resolution
        assert resolution.is_valid
        assert len(resolution.execution_order) == 2
        assert resolution.execution_order[0] == "create_project"
        assert resolution.execution_order[1] == "upload_file_to_project" 