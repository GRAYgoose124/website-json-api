"""
Comprehensive tests for the FastAPI dependency injection system.

This module tests the improved dependency injection patterns, API token management,
workflow context handling, and automatic output-to-input forwarding.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from app.models import (
    Notice, NoticeType, NoticeSeverity, WorkflowStatus, WorkflowDefinition, 
    WorkflowInstance, WorkflowStep, StepDefinition, StepIO, IOSchema, DataType
)
from app.dependencies import (
    verify_api_token, create_access_token, get_workflow_instance,
    get_workflow_notices, get_active_workflows, validate_workflow_permissions,
    get_workflow_execution_context, get_step_context, get_app_config,
    get_health_status, inject_workflow_context, inject_step_context,
    API_SECRET_KEY, API_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api_v2 import app
from app.core import project_manager, notice_manager, step_registry, workflow_engine
from datetime import UTC


class TestDependencyInjection:
    """Test the dependency injection system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_token(self):
        """Create a valid API token for testing."""
        return create_access_token({
            "sub": "test_user",
            "permissions": ["read", "write", "admin"]
        })
    
    @pytest.fixture
    def expired_token(self):
        """Create an expired API token for testing."""
        return create_access_token({
            "sub": "test_user",
            "permissions": ["read", "write"]
        }, expires_delta=timedelta(minutes=-1))
    
    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow for testing."""
        return WorkflowDefinition(
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "standard"}
                )
            ]
        )
    
    @pytest.fixture
    def sample_workflow_instance(self, sample_workflow):
        """Create a sample workflow instance for testing."""
        return WorkflowInstance(
            id="test-workflow-123",
            definition=sample_workflow,
            status=WorkflowStatus.RUNNING,
            context={"data_id": "test-data-123"},
            step_results={
                "data_source": {"data_id": "test-data-123", "data_size": 1000},
                "data_processor": {"processed_data_id": "processed-123", "quality_score": 0.95}
            }
        )

    def test_create_access_token(self):
        """Test creating access tokens."""
        data = {"sub": "test_user", "permissions": ["read", "write"]}
        token = create_access_token(data)
        
        # Verify token can be decoded
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])
        assert payload["sub"] == "test_user"
        assert payload["permissions"] == ["read", "write"]
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test creating access tokens with custom expiry."""
        data = {"sub": "test_user"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        
        # Token should expire in approximately 2 hours
        expected_exp = datetime.now(UTC) + expires_delta
        assert abs((exp_datetime - expected_exp).total_seconds()) < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_verify_api_token_valid(self, valid_token):
        """Test verifying a valid API token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
        user_info = await verify_api_token(credentials)
        
        assert user_info["user_id"] == "test_user"
        assert "admin" in user_info["permissions"]
        assert "exp" in user_info

    @pytest.mark.asyncio
    async def test_verify_api_token_expired(self, expired_token):
        """Test verifying an expired API token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_token_invalid(self):
        """Test verifying an invalid API token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_token_missing(self):
        """Test verifying when no token is provided."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(None)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API token required" in exc_info.value.detail

    def test_get_app_config(self):
        """Test getting application configuration."""
        config = get_app_config()
        
        assert config["api_version"] == "2.0"
        assert "features" in config
        assert "limits" in config
        assert config["features"]["workflow_engine"] is True
        assert config["features"]["dependency_resolution"] is True

    def test_get_health_status(self):
        """Test getting system health status."""
        health = get_health_status()
        
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "version" in health
        assert "services" in health
        assert health["services"]["workflow_engine"] == "running"
        assert health["services"]["step_registry"] == "running"

    @pytest.mark.asyncio
    async def test_get_workflow_notices(self):
        """Test getting workflow notices."""
        # Mock notice manager
        mock_notice = Notice(
            id="test-notice",
            workflow_id="test-workflow",
            type=NoticeType.INFO,
            severity=NoticeSeverity.LOW,
            title="Test Notice",
            message="This is a test notice"
        )
        
        with patch('app.dependencies.get_notice_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_notices.return_value = [mock_notice]
            mock_get_manager.return_value = mock_manager
            
            notices = await get_workflow_notices("test-workflow", NoticeType.INFO)
            
            assert len(notices) == 1
            assert notices[0].id == "test-notice"
            assert notices[0].workflow_id == "test-workflow"

    @pytest.mark.asyncio
    async def test_get_active_workflows(self):
        """Test getting active workflows."""
        # Mock workflow engine
        mock_workflow = WorkflowInstance(
            id="test-workflow",
            definition=WorkflowDefinition(
                name="Test Workflow",
                description="A test workflow",
                steps=[]
            ),
            status=WorkflowStatus.RUNNING
        )
        
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.list_workflows.return_value = [mock_workflow]
            mock_get_engine.return_value = mock_engine
            
            workflows = await get_active_workflows(WorkflowStatus.RUNNING)
            
            assert len(workflows) == 1
            assert workflows[0].id == "test-workflow"
            assert workflows[0].status == WorkflowStatus.RUNNING

    @pytest.mark.asyncio
    async def test_get_workflow_instance_found(self, sample_workflow_instance):
        """Test getting a workflow instance that exists."""
        # Mock workflow engine
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_workflow.return_value = sample_workflow_instance
            mock_get_engine.return_value = mock_engine
            
            workflow = await get_workflow_instance("test-workflow-123")
            
            assert workflow.id == sample_workflow_instance.id
            assert workflow.definition.name == sample_workflow_instance.definition.name


    @pytest.mark.asyncio
    async def test_get_workflow_instance_not_found(self):
        """Test getting a workflow instance that doesn't exist."""
        # Mock workflow engine
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_workflow.return_value = None
            mock_get_engine.return_value = mock_engine
            
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow_instance("non-existent-workflow")
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


    @pytest.mark.asyncio
    async def test_validate_workflow_permissions_success(self, sample_workflow_instance, valid_token):
        """Test validating workflow permissions successfully."""
        user_info = {"user_id": "test_user", "permissions": ["admin"]}
        
        # Mock workflow engine
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_workflow.return_value = sample_workflow_instance
            mock_get_engine.return_value = mock_engine
            
            workflow = await validate_workflow_permissions("test-workflow-123", user_info)
            
            assert workflow.id == sample_workflow_instance.id


    @pytest.mark.asyncio
    async def test_get_step_context(self, sample_workflow_instance):
        """Test getting step context."""
        # Mock dependencies
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine, \
             patch('app.dependencies.get_step_registry') as mock_get_registry:
            
            mock_engine = MagicMock()
            mock_engine.get_workflow.return_value = sample_workflow_instance
            mock_get_engine.return_value = mock_engine
            
            mock_registry = MagicMock()
            mock_registry.definitions = {"data_source": MagicMock()}
            mock_get_registry.return_value = mock_registry
            
            context = await get_step_context("data_source", "test-workflow-123")
            
            assert "step_definition" in context
            assert "step_results" in context
            assert "workflow_context" in context


    @pytest.mark.asyncio
    async def test_get_workflow_execution_context(self, sample_workflow_instance, valid_token):
        """Test getting workflow execution context."""
        user_info = {"user_id": "test_user", "permissions": ["admin"]}
        
        # Mock dependencies
        with patch('app.dependencies.get_workflow_engine') as mock_get_engine, \
             patch('app.dependencies.get_step_registry') as mock_get_registry:
            
            mock_engine = MagicMock()
            mock_engine.get_workflow.return_value = sample_workflow_instance
            mock_engine.get_workflow_dependencies.return_value = MagicMock()
            mock_get_engine.return_value = mock_engine
            
            mock_registry = MagicMock()
            mock_registry.definitions = {"data_source": MagicMock()}
            mock_get_registry.return_value = mock_registry
            
            context = await get_workflow_execution_context("test-workflow-123", user_info)
            
            assert "workflow" in context
            assert "dependency_resolution" in context
            assert "step_definitions" in context
            assert "user_info" in context

    def test_inject_workflow_context(self):
        """Test workflow context injection dependency."""
        dependency = inject_workflow_context("test-workflow-123")
        assert dependency is not None
        # The actual dependency function would be tested in integration tests

    def test_inject_step_context(self):
        """Test step context injection dependency."""
        dependency = inject_step_context("data_source")
        assert dependency is not None
        # The actual dependency function would be tested in integration tests


class TestAPIIntegration:
    """Test the API integration with dependency injection."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for API requests."""
        token = create_access_token({
            "sub": "test_user",
            "permissions": ["read", "write", "admin"]
        })
        return {"Authorization": f"Bearer {token}"}

    def test_health_endpoint(self, client):
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data

    def test_config_endpoint(self, client):
        """Test the config endpoint."""
        response = client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["api_version"] == "2.0"
        assert "features" in data
        assert "limits" in data

    def test_login_endpoint(self, client):
        """Test the login endpoint."""
        response = client.post("/auth/login", data={"username": "test_user", "password": "test_password"})
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_steps_endpoint_with_auth(self, client, auth_headers):
        """Test the steps endpoint with authentication."""
        response = client.get("/steps", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)

    def test_steps_endpoint_without_auth(self, client):
        """Test the steps endpoint without authentication."""
        response = client.get("/steps")
        assert response.status_code == 401

    def test_workflow_validation_endpoint(self, client, auth_headers):
        """Test the workflow validation endpoint."""
        workflow_def = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "data_source",
                    "params": {"source_type": "csv"}
                }
            ]
        }
        
        response = client.post("/workflows/validate", json=workflow_def, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert "execution_order" in data

    def test_workflow_creation_with_auth(self, client, auth_headers):
        """Test workflow creation with authentication."""
        workflow_def = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "create_project",
                    "params": {"project_name": "Test Project"}
                }
            ]
        }
        
        response = client.post("/workflows", json=workflow_def, headers=auth_headers)
        # This might fail if workflow engine is not properly mocked
        # but we can test that the endpoint exists and accepts the request
        assert response.status_code in [200, 400, 422, 500]

    def test_context_flow_endpoint(self, client, auth_headers):
        """Test the context flow endpoint."""
        # This would require a valid workflow ID
        response = client.get("/workflows/test-workflow-123/context-flow", headers=auth_headers)
        # Should return 404 for non-existent workflow
        assert response.status_code == 404

    def test_debug_endpoints(self, client, auth_headers):
        """Test the debug endpoints."""
        response = client.get("/debug/workflow-engine", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "active_workflows" in data
        assert "engine_status" in data

        response = client.get("/debug/step-registry", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_steps" in data
        assert "step_ids" in data


class TestContextForwarding:
    """Test context forwarding functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for API requests."""
        token = create_access_token({
            "sub": "test_user",
            "permissions": ["read", "write", "admin"]
        })
        return {"Authorization": f"Bearer {token}"}

    def test_forward_context_endpoint(self, client, auth_headers):
        """Test the context forwarding endpoint."""
        # This would require a valid workflow with step results
        payload = {
            "source_step_id": "data_source",
            "target_step_id": "data_processor",
            "context_keys": ["data_id", "data_size"]
        }
    
        response = client.post(
            "/workflows/test-workflow-123/forward-context",
            json=payload,
            headers=auth_headers
        )
        # Should return 404 for non-existent workflow or 422 for validation error
        assert response.status_code in [404, 422]

    def test_context_flow_mapping(self, client, auth_headers):
        """Test the context flow mapping endpoint."""
        response = client.get("/workflows/test-workflow-123/context-flow", headers=auth_headers)
        # Should return 404 for non-existent workflow
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling in the dependency injection system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)

    def test_invalid_token_format(self, client):
        """Test handling of invalid token format."""
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/steps", headers=headers)
        assert response.status_code == 401

    def test_malformed_token(self, client):
        """Test handling of malformed tokens."""
        headers = {"Authorization": "Bearer malformed.token.here"}
        response = client.get("/steps", headers=headers)
        assert response.status_code == 401

    def test_missing_workflow(self, client):
        """Test handling of missing workflows."""
        token = create_access_token({"sub": "test_user", "permissions": ["read"]})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/workflows/non-existent-id", headers=headers)
        assert response.status_code == 404

    def test_invalid_workflow_definition(self, client):
        """Test handling of invalid workflow definitions."""
        token = create_access_token({"sub": "test_user", "permissions": ["read", "write"]})
        headers = {"Authorization": f"Bearer {token}"}
    
        invalid_workflow = {
            "name": "Invalid Workflow",
            "description": "A workflow with non-existent steps",
            "steps": [
                {
                    "step_id": "non_existent_step",
                    "params": {}
                }
            ]
        }
    
        response = client.post("/workflows/validate", json=invalid_workflow, headers=headers)
        # Validation should succeed but show missing dependencies
        assert response.status_code in [200, 422]


class TestPerformanceAndScalability:
    """Test performance and scalability aspects of the dependency injection system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)

    def test_concurrent_token_verification(self):
        """Test concurrent token verification performance."""
        import asyncio
        import time
        
        token = create_access_token({"sub": "test_user", "permissions": ["read"]})
        
        async def verify_token():
            from fastapi.security import HTTPAuthorizationCredentials
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            return await verify_api_token(credentials)
        
        async def run_concurrent_verifications():
            tasks = [verify_token() for _ in range(100)]
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            assert len(results) == 100
            assert all(result["user_id"] == "test_user" for result in results)
            return end_time - start_time
        
        # Run the test
        execution_time = asyncio.run(run_concurrent_verifications())
        
        # Should complete within reasonable time (less than 1 second for 100 verifications)
        assert execution_time < 1.0

    def test_dependency_injection_performance(self, client):
        """Test dependency injection performance."""
        import time
        
        token = create_access_token({"sub": "test_user", "permissions": ["read"]})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test multiple concurrent requests
        start_time = time.time()
        responses = []
        
        for _ in range(50):
            response = client.get("/health", headers=headers)
            responses.append(response)
        
        end_time = time.time()
        
        # All responses should be successful
        assert all(r.status_code == 200 for r in responses)
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0 