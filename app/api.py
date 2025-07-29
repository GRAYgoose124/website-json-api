from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from typing import List, Optional, Dict
from datetime import datetime
import asyncio
import os
import shutil
from pathlib import Path

from .models import Notice, NoticeType, WorkflowStatus, WorkflowDefinition, WorkflowInstance, StepDefinition, DependencyResolution
from .core import notice_manager, step_registry, workflow_engine
from .step_loader import StepLoader
from .dependency_resolver import DependencyResolver

# Create FastAPI app
app = FastAPI(title="Scientific Workflow API")

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "ws://localhost:5173", "ws://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize step loader
step_loader = StepLoader()

# Create uploads directory
UPLOADS_DIR = Path("./uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Initialize dependency resolver
@app.on_event("startup")
async def startup_event():
    """Initialize the dependency resolver after steps are loaded"""
    dependency_resolver = DependencyResolver(step_registry.definitions)
    step_registry.set_dependency_resolver(dependency_resolver)

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return the file path"""
    try:
        # Create a unique filename to avoid conflicts
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = UPLOADS_DIR / filename
        
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
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# API Endpoints
@app.get("/notices", response_model=List[Notice])
async def get_notices(
    workflow_id: Optional[str] = None,
    notice_type: Optional[NoticeType] = None,
    since: Optional[datetime] = None
):
    return notice_manager.get_notices(workflow_id, notice_type, since)

@app.get("/steps", response_model=Dict[str, StepDefinition])
async def get_available_steps(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in name, description, or tags")
):
    """Get available steps with optional filtering"""
    if category:
        return step_loader.get_steps_by_category(category)
    elif tag:
        return step_loader.get_steps_by_tag(tag)
    elif search:
        return step_loader.search_steps(search)
    else:
        return step_registry.definitions

@app.get("/steps/categories")
async def get_step_categories():
    """Get all available step categories"""
    categories = set()
    for definition in step_registry.definitions.values():
        if definition.category:
            categories.add(definition.category)
    return list(categories)

@app.get("/steps/tags")
async def get_step_tags():
    """Get all available step tags"""
    tags = set()
    for definition in step_registry.definitions.values():
        tags.update(definition.tags)
    return list(tags)

@app.post("/workflows", response_model=WorkflowInstance)
async def create_workflow(definition: WorkflowDefinition, background_tasks: BackgroundTasks):
    # Validate workflow before creating
    errors, warnings = step_registry.validate_workflow(WorkflowInstance(definition=definition))
    
    if errors:
        raise HTTPException(status_code=400, detail={
            "message": "Workflow validation failed",
            "errors": errors,
            "warnings": warnings
        })
    
    workflow = WorkflowInstance(definition=definition)
    workflow_engine.workflows[workflow.id] = workflow
    
    # Add validation results to workflow
    workflow.definition.validation_errors = errors
    workflow.definition.validation_warnings = warnings
    
    background_tasks.add_task(workflow_engine.execute_workflow, workflow)
    
    return workflow

@app.post("/workflows/validate")
async def validate_workflow(definition: WorkflowDefinition):
    """Validate a workflow definition without creating it"""
    errors, warnings = step_registry.validate_workflow(WorkflowInstance(definition=definition))
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

@app.post("/workflows/resolve-dependencies")
async def resolve_workflow_dependencies(definition: WorkflowDefinition):
    """Resolve dependencies for a workflow definition"""
    workflow = WorkflowInstance(definition=definition)
    resolution = step_registry.resolve_dependencies(workflow)
    
    return resolution

@app.get("/workflows/{workflow_id}", response_model=WorkflowInstance)
async def get_workflow(workflow_id: str):
    if workflow_id not in workflow_engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_engine.workflows[workflow_id]

@app.get("/workflows/{workflow_id}/dependencies", response_model=DependencyResolution)
async def get_workflow_dependencies(workflow_id: str):
    """Get dependency resolution for a workflow"""
    if workflow_id not in workflow_engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    resolution = workflow_engine.get_workflow_dependencies(workflow_id)
    if not resolution:
        raise HTTPException(status_code=404, detail="Dependency resolution not found")
    
    return resolution

@app.get("/workflows", response_model=List[WorkflowInstance])
async def list_workflows(status: Optional[WorkflowStatus] = None):
    workflows = list(workflow_engine.workflows.values())
    if status:
        workflows = [w for w in workflows if w.status == status]
    return workflows

@app.delete("/notices/{notice_id}")
async def dismiss_notice(notice_id: str):
    notice_manager.notices = [n for n in notice_manager.notices if n.id != notice_id]
    return {"status": "dismissed"}

# WebSocket endpoint for real-time notices
@app.websocket("/ws/notices")
async def websocket_notices(websocket: WebSocket):
    await websocket.accept()
    connection_closed = [False]  # Use list to make it mutable in nested function
    
    async def send_notice(notice: Notice):
        if connection_closed[0]:
            return
        try:
            # Convert notice to dict and handle datetime serialization
            notice_dict = notice.dict()
            # Convert datetime to ISO string - handle naive datetime
            if notice_dict.get('timestamp'):
                timestamp = notice_dict['timestamp']
                if hasattr(timestamp, 'isoformat'):
                    notice_dict['timestamp'] = timestamp.isoformat()
                else:
                    notice_dict['timestamp'] = str(timestamp)
            await websocket.send_json(notice_dict)
        except (WebSocketDisconnect, RuntimeError) as e:
            # Connection is closed or broken
            connection_closed[0] = True
            notice_manager.unsubscribe(send_notice)
            print(f"WebSocket send error (connection closed): {e}")
        except Exception as e:
            # Other errors
            notice_manager.unsubscribe(send_notice)
            print(f"WebSocket send error: {e}")
    
    notice_manager.subscribe(send_notice)
    
    try:
        # Keep connection alive and handle disconnection
        while not connection_closed[0]:
            try:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                await asyncio.sleep(30)  # Ping every 30 seconds
            except WebSocketDisconnect:
                connection_closed[0] = True
                break
            except Exception as e:
                print(f"WebSocket ping error: {e}")
                connection_closed[0] = True
                break
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        connection_closed[0] = True
    finally:
        # Clean up subscriber when connection closes
        notice_manager.unsubscribe(send_notice) 