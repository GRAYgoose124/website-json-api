from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict
from datetime import datetime
import asyncio

from .models import Notice, NoticeType, WorkflowStatus, WorkflowDefinition, WorkflowInstance, StepDefinition
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

# API Endpoints
@app.get("/notices", response_model=List[Notice])
async def get_notices(
    workflow_id: Optional[str] = None,
    notice_type: Optional[NoticeType] = None,
    since: Optional[datetime] = None
):
    return notice_manager.get_notices(workflow_id, notice_type, since)

@app.get("/steps", response_model=Dict[str, StepDefinition])
async def get_available_steps():
    return step_registry.definitions

@app.post("/workflows", response_model=WorkflowInstance)
async def create_workflow(definition: WorkflowDefinition, background_tasks: BackgroundTasks):
    workflow = WorkflowInstance(definition=definition)
    workflow_engine.workflows[workflow.id] = workflow
    
    background_tasks.add_task(workflow_engine.execute_workflow, workflow)
    
    return workflow

@app.get("/workflows/{workflow_id}", response_model=WorkflowInstance)
async def get_workflow(workflow_id: str):
    if workflow_id not in workflow_engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_engine.workflows[workflow_id]

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