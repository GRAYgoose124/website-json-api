import asyncio
import shutil

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from datetime import datetime, UTC
from pathlib import Path

from .models import Notice, NoticeType, WorkflowStatus, WorkflowDefinition, WorkflowInstance, StepDefinition, DependencyResolution
from .core import notice_manager, step_registry, workflow_engine

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

# Note: Dependency resolver is now initialized in core.py during application startup

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return the file path"""
    try:
        # Get uploads directory from app state and ensure it's a Path object
        uploads_dir_raw = getattr(app.state, 'uploads_dir', "./uploads")
        uploads_dir = Path(uploads_dir_raw) if isinstance(uploads_dir_raw, str) else uploads_dir_raw
        uploads_dir.mkdir(exist_ok=True)
        
        # Create a unique filename to avoid conflicts
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
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file from the server"""
    try:
        # Security: Only allow downloads from specific directories
        uploads_dir_raw = getattr(app.state, 'uploads_dir', "./uploads")
        uploads_dir = Path(uploads_dir_raw) if isinstance(uploads_dir_raw, str) else uploads_dir_raw
        
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
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return the file for download
        return FileResponse(
            path=str(actual_file_path),
            filename=actual_file_path.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

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
    definitions = step_registry.definitions
    
    if category:
        return {k: v for k, v in definitions.items() if v.category == category}
    elif tag:
        return {k: v for k, v in definitions.items() if tag in v.tags}
    elif search:
        search_lower = search.lower()
        return {
            k: v for k, v in definitions.items() 
            if search_lower in v.name.lower() or search_lower in v.description.lower() or any(search_lower in tag.lower() for tag in v.tags)
        }
    else:
        return definitions

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
                await websocket.send_json({"type": "ping", "timestamp": datetime.now(UTC).isoformat()})
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