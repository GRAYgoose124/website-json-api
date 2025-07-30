"""
Improved FastAPI implementation with proper dependency injection.

This module demonstrates how to use FastAPI's dependency injection system
for better management of global instances, API tokens, workflow contexts,
and automatic output-to-input forwarding.
"""

import asyncio
import shutil
from typing import List, Optional, Dict, Any, Annotated
from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from datetime import datetime, UTC
from pathlib import Path

from .models import (
    Notice, NoticeType, WorkflowStatus, WorkflowDefinition, 
    WorkflowInstance, StepDefinition, DependencyResolution
)
from .dependencies import (
    get_project_manager, get_notice_manager, get_step_registry, get_workflow_engine,
    verify_api_token, create_access_token, get_workflow_instance,
    get_workflow_notices, get_active_workflows, get_app_config, get_health_status,
    inject_workflow_context, inject_step_context, get_workflow_execution_context
)
from .core import initialize_core
from .step.context import StepContext
from .managers.notice import NoticeManager
from .workflow_engine import WorkflowEngine
from .step.registry import StepRegistry

# Create FastAPI app (will be redefined with lifespan)
app = FastAPI(
    title="Scientific Workflow API v2",
    description="Improved API with dependency injection and context management",
    version="2.0.0"
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_app_core():
    """Initialize the application core components."""
    print("🚀 Initializing Scientific Workflow API v2...")
    
    # Initialize core components
    init_result = initialize_core(
        userdata_root="./userdata",
        step_paths=["bundled_steps/project", "bundled_steps/test_suite"]
    )
    
    # Store initialization results in app state
    app.state.init_result = init_result
    app.state.uploads_dir = Path(init_result["uploads_dir"])
    
    # Store core instances in app state for dependency injection
    from app.core import project_manager, notice_manager, step_registry, workflow_engine, dependency_resolver
    app.state.project_manager = project_manager
    app.state.notice_manager = notice_manager
    app.state.step_registry = step_registry
    app.state.workflow_engine = workflow_engine
    app.state.dependency_resolver = dependency_resolver
    
    print(f"✅ API initialized with {init_result['total_steps']} steps")
    return init_result

# Use lifespan context manager instead of deprecated on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    # Startup
    initialize_app_core()
    yield
    # Shutdown (if needed)
    pass

# Update app to use lifespan
app = FastAPI(
    title="Scientific Workflow API v2",
    description="Improved API with dependency injection and context management",
    version="2.0.0",
    lifespan=lifespan
)


# Health and status endpoints
@app.get("/health")
async def health_check():
    """Get system health status."""
    return get_health_status()


@app.get("/config")
async def get_config():
    """Get application configuration."""
    return get_app_config()


# Authentication endpoints
@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Login endpoint for testing purposes."""
    # This is a simplified login for testing
    # In production, you'd validate against a database
    if username == "test_user" and password == "test_password":
        token = create_access_token(
            data={"sub": username, "permissions": ["read", "write", "admin"]}
        )
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


# Notice management with dependency injection
@app.get("/notices", response_model=List[Notice])
async def get_notices(
    workflow_id: Optional[str] = None,
    notice_type: Optional[NoticeType] = None,
    user_info: Dict[str, Any] = Depends(verify_api_token),
    notice_manager: NoticeManager = Depends(get_notice_manager)
):
    """Get notices with optional filtering."""
    return await get_workflow_notices(workflow_id, notice_type, notice_manager)


@app.delete("/notices/{notice_id}")
async def dismiss_notice(
    notice_id: str,
    notice_manager = Depends(get_notice_manager)
):
    """Dismiss a notice."""
    # This would need to be implemented in the notice manager
    return {"success": True, "notice_id": notice_id}


# Step management with dependency injection
@app.get("/steps", response_model=Dict[str, StepDefinition])
async def get_available_steps(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    user_info: Dict[str, Any] = Depends(verify_api_token),
    step_registry = Depends(get_step_registry)
):
    """Get available steps with optional filtering."""
    steps = step_registry.definitions
    
    # Apply filters
    if category:
        steps = {k: v for k, v in steps.items() if v.category == category}
    
    if tag:
        steps = {k: v for k, v in steps.items() if tag in v.tags}
    
    if search:
        search_lower = search.lower()
        steps = {
            k: v for k, v in steps.items() 
            if search_lower in k.lower() or search_lower in v.name.lower() or search_lower in v.description.lower()
        }
    
    return steps


@app.get("/steps/categories")
async def get_step_categories(step_registry = Depends(get_step_registry)):
    """Get all available step categories."""
    categories = set(step.category for step in step_registry.definitions.values())
    return {"categories": sorted(list(categories))}


@app.get("/steps/tags")
async def get_step_tags(step_registry = Depends(get_step_registry)):
    """Get all available step tags."""
    all_tags = set()
    for step in step_registry.definitions.values():
        all_tags.update(step.tags)
    return {"tags": sorted(list(all_tags))}


# Workflow management with improved dependency injection
@app.post("/workflows", response_model=WorkflowInstance)
async def create_workflow(
    definition: WorkflowDefinition,
    background_tasks: BackgroundTasks,
    user_info: Dict[str, Any] = Depends(verify_api_token),
    workflow_engine = Depends(get_workflow_engine),
    step_registry = Depends(get_step_registry)
):
    """Create and execute a new workflow."""
    # Validate workflow definition
    try:
        dependency_resolver = step_registry.dependency_resolver
        if not dependency_resolver:
            # Create a dependency resolver if not available
            from app.dependency_resolver import DependencyResolver
            dependency_resolver = DependencyResolver()
        
        resolution = dependency_resolver.resolve_dependencies(definition)
        
        if resolution.cycles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Workflow has circular dependencies: {resolution.cycles}"
            )
        
        if resolution.missing_dependencies:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing dependencies: {resolution.missing_dependencies}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Workflow validation failed: {str(e)}"
        )
    
    # Create workflow instance
    workflow = WorkflowInstance(
        definition=definition,
        status=WorkflowStatus.PENDING
    )
    
    # Add to workflow engine
    workflow_engine.workflows[workflow.id] = workflow
    
    # Execute workflow in background
    background_tasks.add_task(workflow_engine.execute_workflow, workflow)
    
    return workflow


@app.post("/workflows/validate")
async def validate_workflow(
    definition: WorkflowDefinition,
    step_registry = Depends(get_step_registry)
):
    """Validate a workflow definition."""
    try:
        dependency_resolver = step_registry.dependency_resolver
        if not dependency_resolver:
            # Create a dependency resolver if not available
            from app.dependency_resolver import DependencyResolver
            dependency_resolver = DependencyResolver()
        
        resolution = dependency_resolver.resolve_dependencies(definition)
        
        return {
            "valid": len(resolution.cycles) == 0 and len(resolution.missing_dependencies) == 0,
            "cycles": resolution.cycles,
            "missing_dependencies": resolution.missing_dependencies,
            "execution_order": resolution.execution_order,
            "context_flow": resolution.context_flow
        }
    except Exception as e:
        return {
            "valid": False,
            "cycles": [],
            "missing_dependencies": [str(e)],
            "execution_order": [],
            "context_flow": {}
        }


@app.post("/workflows/resolve-dependencies")
async def resolve_workflow_dependencies(
    definition: WorkflowDefinition,
    step_registry = Depends(get_step_registry)
):
    """Resolve dependencies for a workflow definition."""
    try:
        dependency_resolver = step_registry.dependency_resolver
        if not dependency_resolver:
            # Create a dependency resolver if not available
            from app.dependency_resolver import DependencyResolver
            dependency_resolver = DependencyResolver()
        
        return dependency_resolver.resolve_dependencies(definition)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to resolve dependencies: {str(e)}"
        )


@app.get("/workflows/{workflow_id}", response_model=WorkflowInstance)
async def get_workflow(
    workflow_id: str,
    workflow_engine = Depends(get_workflow_engine)
):
    """Get a specific workflow by ID."""
    return await get_workflow_instance(workflow_id, workflow_engine)


@app.get("/workflows/{workflow_id}/dependencies", response_model=DependencyResolution)
async def get_workflow_dependencies(
    workflow_id: str,
    workflow_engine = Depends(get_workflow_engine),
    step_registry = Depends(get_step_registry)
):
    """Get dependency resolution for a workflow."""
    workflow = await get_workflow_instance(workflow_id, workflow_engine)
    
    try:
        dependency_resolver = step_registry.dependency_resolver
        if not dependency_resolver:
            # Create a dependency resolver if not available
            from app.dependency_resolver import DependencyResolver
            dependency_resolver = DependencyResolver()
        
        return dependency_resolver.resolve_dependencies(workflow.definition)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to resolve dependencies: {str(e)}"
        )


@app.get("/workflows/{workflow_id}/context")
async def get_workflow_context(
    workflow_id: str,
    user_info: Dict[str, Any] = Depends(verify_api_token),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    step_registry: StepRegistry = Depends(get_step_registry)
):
    """Get complete workflow execution context."""
    return await get_workflow_execution_context(workflow_id, user_info, workflow_engine, step_registry)


@app.get("/workflows", response_model=List[WorkflowInstance])
async def list_workflows(
    status: Optional[WorkflowStatus] = None,
    user_info: Dict[str, Any] = Depends(verify_api_token),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """List all workflows with optional status filtering."""
    return await get_active_workflows(status, workflow_engine)


# Step-specific endpoints with context injection
@app.get("/workflows/{workflow_id}/steps/{step_id}/context")
async def get_step_context(
    step_id: str,
    workflow_id: str,
    step_registry: StepRegistry = Depends(get_step_registry),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get context for a specific step in a workflow."""
    from app.dependencies import get_step_context
    return await get_step_context(step_id, workflow_id, step_registry, workflow_engine)


@app.post("/workflows/{workflow_id}/steps/{step_id}/execute")
async def execute_step(
    step_id: str,
    workflow_id: str,
    params: Dict[str, Any],
    user_info: Dict[str, Any] = Depends(verify_api_token),
    workflow_engine = Depends(get_workflow_engine),
    step_registry = Depends(get_step_registry)
):
    """Execute a specific step in a workflow."""
    # Get workflow
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Check if step exists
    step_definition = step_registry.definitions.get(step_id)
    if not step_definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_id} not found"
        )
    
    # Create step context
    context = StepContext(
        workflow_id=workflow_id,
        step_id=step_id,
        notice_manager=get_notice_manager(),
        workflow_context=workflow.context
    )
    
    try:
        # Execute the step
        result = await step_registry.execute(step_id, params, context)
        
        # Update workflow context with step outputs
        for output_schema in step_definition.io.outputs:
            if output_schema.name in result:
                workflow.context[output_schema.name] = result[output_schema.name]
        
        # Store step result
        workflow.step_results[step_id] = result
        
        return {
            "step_id": step_id,
            "workflow_id": workflow_id,
            "result": result,
            "context_updated": list(workflow.context.keys())
        }
        
    except Exception as e:
        await context.error("Step Execution Failed", f"Step {step_id} failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Step execution failed: {str(e)}"
        )


# WebSocket endpoint for real-time updates
@app.websocket("/ws/notices")
async def websocket_notices(
    websocket: WebSocket,
    notice_manager = Depends(get_notice_manager)
):
    """WebSocket endpoint for real-time notice updates."""
    await websocket.accept()
    
    try:
        # Send initial notices
        notices = notice_manager.get_notices()
        await websocket.send_json({"type": "notices", "data": [n.model_dump(mode='json') for n in notices]})
        
        # Keep connection alive and send updates
        while True:
            await asyncio.sleep(1)
            # In a real implementation, you'd check for new notices
            # and send them to the client
    except WebSocketDisconnect:
        print("WebSocket client disconnected")


# File upload/download endpoints
@app.post("/upload-file")
async def upload_file(
    file: UploadFile,
    user_info: Dict[str, Any] = Depends(verify_api_token)
):
    """Upload a file and return the file path."""
    try:
        uploads_dir = app.state.uploads_dir
        uploads_dir.mkdir(exist_ok=True)
        
        # Create a unique filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = uploads_dir / filename
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "size": file_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@app.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    user_info: Dict[str, Any] = Depends(verify_api_token)
):
    """Download a file from the server."""
    try:
        # Security: Only allow downloads from specific directories
        uploads_dir = app.state.uploads_dir
        allowed_dirs = [
            uploads_dir,
            Path("./userdata/projects/downloads"),
            Path("./test-userdata/projects/downloads")
        ]
        
        # Convert file_path to Path (it's the filename)
        filename = Path(file_path).name
        
        # Search for the file in allowed directories
        actual_file_path = None
        for allowed_dir in allowed_dirs:
            if allowed_dir.exists():
                potential_path = allowed_dir / filename
                if potential_path.exists() and potential_path.is_file():
                    actual_file_path = potential_path
                    break
        
        if not actual_file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Return the file for download
        return FileResponse(
            path=str(actual_file_path),
            filename=actual_file_path.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


# Advanced workflow operations with context forwarding
@app.post("/workflows/{workflow_id}/forward-context")
async def forward_workflow_context(
    workflow_id: str,
    source_step_id: str,
    target_step_id: str,
    context_keys: List[str],
    user_info: Dict[str, Any] = Depends(verify_api_token),
    workflow_engine = Depends(get_workflow_engine),
    step_registry = Depends(get_step_registry)
):
    """
    Forward context from one step to another.
    
    This demonstrates how to manually forward outputs from one step
    to inputs of another step, bypassing automatic dependency resolution.
    """
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    # Get source step results
    source_results = workflow.step_results.get(source_step_id, {})
    
    # Forward specified context keys
    forwarded_context = {}
    for key in context_keys:
        if key in source_results:
            forwarded_context[key] = source_results[key]
    
    # Update workflow context
    workflow.context.update(forwarded_context)
    
    return {
        "success": True,
        "forwarded_keys": list(forwarded_context.keys()),
        "target_step": target_step_id
    }


@app.get("/workflows/{workflow_id}/context-flow")
async def get_context_flow(
    workflow_id: str,
    workflow_engine = Depends(get_workflow_engine),
    step_registry = Depends(get_step_registry)
):
    """Get the context flow mapping for a workflow."""
    workflow = await get_workflow_instance(workflow_id, workflow_engine)
    
    try:
        dependency_resolver = step_registry.dependency_resolver
        if not dependency_resolver:
            # Create a dependency resolver if not available
            from app.dependency_resolver import DependencyResolver
            dependency_resolver = DependencyResolver()
        
        resolution = dependency_resolver.resolve_dependencies(workflow.definition)
        
        return {
            "workflow_id": workflow.id,
            "context_flow": resolution.context_flow,
            "execution_order": resolution.execution_order,
            "dependencies": resolution.dependencies,
            "dependents": resolution.dependents
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to get context flow: {str(e)}"
        )


# Utility endpoints for debugging and development
@app.get("/debug/workflow-engine")
async def debug_workflow_engine(
    workflow_engine = Depends(get_workflow_engine)
):
    """Debug information about the workflow engine."""
    return {
        "active_workflows": len(workflow_engine.active_workflows),
        "completed_workflows": len(workflow_engine.completed_workflows),
        "engine_status": "running"
    }


@app.get("/debug/step-registry")
async def debug_step_registry(
    step_registry = Depends(get_step_registry)
):
    """Debug information about the step registry."""
    return {
        "total_steps": len(step_registry.definitions),
        "step_ids": list(step_registry.definitions.keys()),
        "categories": list(set(s.category for s in step_registry.definitions.values() if s.category)),
        "has_dependency_resolver": step_registry.dependency_resolver is not None
    } 