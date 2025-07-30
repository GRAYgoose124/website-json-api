"""
FastAPI dependency injection system for the workflow API.

This module provides dependency injection functions that can be used with FastAPI's
Depends() function to manage global instances, API tokens, workflow contexts,
and other shared resources.
"""

import os
import jwt
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import WorkflowInstance, WorkflowStatus, Notice, NoticeType
from app.workflow_engine import WorkflowEngine
from app.step.registry import StepRegistry
from app.managers.notice import NoticeManager
from app.managers.project import ProjectManager
from app.dependency_resolver import DependencyResolver
from app.core import (
    project_manager, notice_manager, step_registry, 
    workflow_engine, dependency_resolver
)

# Configuration
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-here")
API_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security scheme
security = HTTPBearer(auto_error=False)

# Dependency injection functions - use singleton instances
def get_project_manager() -> ProjectManager:
    """Get project manager instance."""
    # Re-import to get the latest state
    from app.core import project_manager as current_project_manager
    if current_project_manager is None:
        raise RuntimeError("Application not initialized. Call initialize_core() first.")
    return current_project_manager

def get_notice_manager() -> NoticeManager:
    """Get notice manager instance."""
    # Re-import to get the latest state
    from app.core import notice_manager as current_notice_manager
    if current_notice_manager is None:
        raise RuntimeError("Application not initialized. Call initialize_core() first.")
    return current_notice_manager

def get_step_registry() -> StepRegistry:
    """Get step registry instance."""
    # Re-import to get the latest state
    from app.core import step_registry as current_step_registry
    if current_step_registry is None:
        raise RuntimeError("Application not initialized. Call initialize_core() first.")
    return current_step_registry

def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance."""
    # Re-import to get the latest state
    from app.core import workflow_engine as current_workflow_engine
    if current_workflow_engine is None:
        raise RuntimeError("Application not initialized. Call initialize_core() first.")
    return current_workflow_engine

def get_dependency_resolver() -> DependencyResolver:
    """Get dependency resolver instance."""
    # Re-import to get the latest state
    from app.core import dependency_resolver as current_dependency_resolver
    if current_dependency_resolver is None:
        raise RuntimeError("Application not initialized. Call initialize_core() first.")
    return current_dependency_resolver

async def verify_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Verify API token and return user information.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dict containing user information and permissions
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            API_SECRET_KEY, 
            algorithms=[API_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return {
            "user_id": user_id,
            "permissions": payload.get("permissions", []),
            "exp": payload.get("exp")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_ALGORITHM)
    return encoded_jwt


async def get_workflow_instance(
    workflow_id: str,
    workflow_engine: WorkflowEngine = None
) -> WorkflowInstance:
    """
    Get a workflow instance by ID.
    
    Args:
        workflow_id: The workflow instance ID
        workflow_engine: Workflow engine dependency
        
    Returns:
        WorkflowInstance object
        
    Raises:
        HTTPException: If workflow not found
    """
    if workflow_engine is None:
        workflow_engine = get_workflow_engine()
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return workflow


async def get_active_workflows(
    status_filter: Optional[WorkflowStatus] = None,
    workflow_engine: WorkflowEngine = None
) -> List[WorkflowInstance]:
    """
    Get active workflows with optional status filtering.
    
    Args:
        status_filter: Optional status to filter by
        workflow_engine: Workflow engine dependency
        
    Returns:
        List of workflow instances
    """
    if workflow_engine is None:
        workflow_engine = get_workflow_engine()
    workflows = workflow_engine.list_workflows(status_filter)
    return workflows


async def get_workflow_notices(
    workflow_id: Optional[str] = None,
    notice_type: Optional[NoticeType] = None,
    notice_manager: NoticeManager = None
) -> List[Notice]:
    """
    Get notices with optional filtering.
    
    Args:
        workflow_id: Optional workflow ID to filter by
        notice_type: Optional notice type to filter by
        notice_manager: Notice manager dependency
        
    Returns:
        List of notices
    """
    if notice_manager is None:
        notice_manager = get_notice_manager()
    notices = notice_manager.get_notices(workflow_id, notice_type)
    return notices


async def get_step_context(
    step_id: str,
    workflow_id: str,
    step_registry: StepRegistry = None,
    workflow_engine: WorkflowEngine = None
) -> Dict[str, Any]:
    """
    Get the context for a specific step in a workflow.
    
    Args:
        step_id: The step ID
        workflow_id: The workflow ID
        step_registry: Step registry dependency
        workflow_engine: Workflow engine dependency
        
    Returns:
        Step context dictionary
    """
    if step_registry is None:
        step_registry = get_step_registry()
    if workflow_engine is None:
        workflow_engine = get_workflow_engine()
    
    workflow = await get_workflow_instance(workflow_id, workflow_engine)
    
    # Get step definition
    step_definition = step_registry.definitions.get(step_id)
    if not step_definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_id} not found"
        )
    
    # Get step results from workflow
    step_results = workflow.step_results.get(step_id, {})
    
    # Get workflow context
    workflow_context = workflow.context
    
    return {
        "step_definition": step_definition,
        "step_results": step_results,
        "workflow_context": workflow_context
    }


async def validate_workflow_permissions(
    workflow_id: str,
    user_info: Dict[str, Any],
    workflow_engine: WorkflowEngine = None
) -> WorkflowInstance:
    """
    Validate user permissions for a workflow.
    
    Args:
        workflow_id: The workflow ID
        user_info: User information from token
        workflow_engine: Workflow engine dependency
        
    Returns:
        WorkflowInstance object
        
    Raises:
        HTTPException: If user lacks permissions
    """
    if workflow_engine is None:
        workflow_engine = get_workflow_engine()
    
    workflow = await get_workflow_instance(workflow_id, workflow_engine)
    
    # Check if user has required permissions
    permissions = user_info.get("permissions", [])
    if "admin" not in permissions and "write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return workflow


async def get_workflow_execution_context(
    workflow_id: str,
    user_info: Dict[str, Any],
    workflow_engine: WorkflowEngine = None,
    step_registry: StepRegistry = None
) -> Dict[str, Any]:
    """
    Get the execution context for a workflow.
    
    Args:
        workflow_id: The workflow ID
        user_info: User information from token
        workflow_engine: Workflow engine dependency
        step_registry: Step registry dependency
        
    Returns:
        Execution context dictionary
    """
    if workflow_engine is None:
        workflow_engine = get_workflow_engine()
    if step_registry is None:
        step_registry = get_step_registry()
    
    workflow = await validate_workflow_permissions(workflow_id, user_info, workflow_engine)
    
    # Get dependency resolution
    dependency_resolution = workflow_engine.get_workflow_dependencies(workflow_id)
    
    # Get step definitions
    step_definitions = {}
    for step in workflow.definition.steps:
        step_def = step_registry.definitions.get(step.step_id)
        if step_def:
            step_definitions[step.step_id] = step_def
    
    return {
        "workflow": workflow,
        "dependency_resolution": dependency_resolution,
        "step_definitions": step_definitions,
        "user_info": user_info
    }


# Type aliases for dependency injection
UserInfo = Dict[str, Any]
WorkflowEngineDep = WorkflowEngine
StepRegistryDep = StepRegistry

def inject_workflow_context(workflow_id: str) -> Dict[str, Any]:
    """
    Inject workflow context into a dependency.
    
    Args:
        workflow_id: The workflow ID
        
    Returns:
        Workflow context dictionary
    """
    async def _get_workflow_context(
        user_info: UserInfo,
        workflow_engine: WorkflowEngineDep,
        step_registry: StepRegistryDep
    ) -> Dict[str, Any]:
        workflow = await get_workflow_instance(workflow_id, workflow_engine)
        return {
            "workflow": workflow,
            "user_info": user_info,
            "step_registry": step_registry
        }
    
    return _get_workflow_context


def inject_step_context(step_id: str) -> Dict[str, Any]:
    """
    Inject step context into a dependency.
    
    Args:
        step_id: The step ID
        
    Returns:
        Step context dictionary
    """
    async def _get_step_context(
        workflow_id: str,
        step_registry: StepRegistryDep,
        workflow_engine: WorkflowEngineDep
    ) -> Dict[str, Any]:
        return await get_step_context(step_id, workflow_id, step_registry, workflow_engine)
    
    return _get_step_context


def get_app_config() -> Dict[str, Any]:
    """Get application configuration."""
    return {
        "api_version": "2.0",
        "features": {
            "workflow_engine": True,
            "dependency_resolution": True,
            "context_forwarding": True,
            "project_management": True
        },
        "limits": {
            "max_workflow_steps": 50,
            "max_file_size": "100MB",
            "max_concurrent_workflows": 10
        }
    }


def get_health_status() -> Dict[str, Any]:
    """Get application health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "2.0.0",
        "services": {
            "workflow_engine": "running",
            "step_registry": "running",
            "notice_manager": "running",
            "project_manager": "running"
        }
    } 