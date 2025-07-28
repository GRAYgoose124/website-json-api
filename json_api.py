from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Callable, Union
from enum import Enum
from datetime import datetime
import asyncio
import uuid
from contextlib import asynccontextmanager
import traceback
from fastapi.middleware.cors import CORSMiddleware

# Models
class NoticeType(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    DEBUG = "debug"

class NoticeSeverity(int, Enum):
    CRITICAL = 50
    HIGH = 40
    MEDIUM = 30
    LOW = 20
    DEBUG = 10

class Notice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NoticeType
    severity: NoticeSeverity
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None
    dismissible: bool = True
    auto_dismiss_seconds: Optional[int] = None

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepDefinition(BaseModel):
    id: str
    name: str
    description: str
    params_schema: Dict[str, Any] = {}
    timeout_seconds: Optional[int] = None
    retry_count: int = 0

class WorkflowStep(BaseModel):
    step_id: str
    params: Dict[str, Any] = {}
    depends_on: List[str] = []

class WorkflowDefinition(BaseModel):
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = {}

class WorkflowInstance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = {}
    notices: List[Notice] = []

# Core System
class NoticeManager:
    def __init__(self):
        self.notices: List[Notice] = []
        self.subscribers: List[Callable] = []
    
    async def emit(self, notice: Notice):
        self.notices.append(notice)
        # Create a copy of subscribers to avoid modification during iteration
        subscribers_copy = self.subscribers.copy()
        for subscriber in subscribers_copy:
            try:
                await subscriber(notice)
            except Exception as e:
                # Remove broken subscribers
                if subscriber in self.subscribers:
                    self.subscribers.remove(subscriber)
                print(f"Error sending notice to subscriber: {e}")
    
    def subscribe(self, callback: Callable):
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_notices(self, 
                    workflow_id: Optional[str] = None,
                    notice_type: Optional[NoticeType] = None,
                    since: Optional[datetime] = None) -> List[Notice]:
        filtered = self.notices
        
        if workflow_id:
            filtered = [n for n in filtered if n.workflow_id == workflow_id]
        if notice_type:
            filtered = [n for n in filtered if n.type == notice_type]
        if since:
            filtered = [n for n in filtered if n.timestamp > since]
        
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)

class StepRegistry:
    def __init__(self):
        self.steps: Dict[str, Callable] = {}
        self.definitions: Dict[str, StepDefinition] = {}
    
    def register(self, definition: StepDefinition):
        def decorator(func: Callable):
            self.steps[definition.id] = func
            self.definitions[definition.id] = definition
            return func
        return decorator
    
    async def execute(self, step_id: str, params: Dict[str, Any], context: 'StepContext'):
        if step_id not in self.steps:
            raise ValueError(f"Step {step_id} not registered")
        
        step_func = self.steps[step_id]
        return await step_func(params, context)

class StepContext:
    def __init__(self, workflow_id: str, step_id: str, notice_manager: NoticeManager):
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.notice_manager = notice_manager
    
    async def info(self, title: str, message: str, **kwargs):
        await self.notice_manager.emit(Notice(
            type=NoticeType.INFO,
            severity=NoticeSeverity.LOW,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            **kwargs
        ))
    
    async def warning(self, title: str, message: str, **kwargs):
        await self.notice_manager.emit(Notice(
            type=NoticeType.WARNING,
            severity=NoticeSeverity.MEDIUM,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            **kwargs
        ))
    
    async def error(self, title: str, message: str, **kwargs):
        await self.notice_manager.emit(Notice(
            type=NoticeType.ERROR,
            severity=NoticeSeverity.HIGH,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            **kwargs
        ))
    
    async def success(self, title: str, message: str, **kwargs):
        await self.notice_manager.emit(Notice(
            type=NoticeType.SUCCESS,
            severity=NoticeSeverity.MEDIUM,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            **kwargs
        ))

class WorkflowEngine:
    def __init__(self, step_registry: StepRegistry, notice_manager: NoticeManager):
        self.step_registry = step_registry
        self.notice_manager = notice_manager
        self.workflows: Dict[str, WorkflowInstance] = {}
    
    async def execute_workflow(self, workflow: WorkflowInstance):
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        try:
            await self.notice_manager.emit(Notice(
                type=NoticeType.INFO,
                severity=NoticeSeverity.LOW,
                title="Workflow Started",
                message=f"Starting workflow: {workflow.definition.name}",
                workflow_id=workflow.id
            ))
            
            # Execute steps in dependency order
            executed = set()
            while len(executed) < len(workflow.definition.steps):
                for step in workflow.definition.steps:
                    if step.step_id in executed:
                        continue
                    
                    if all(dep in executed for dep in step.depends_on):
                        workflow.current_step = step.step_id
                        context = StepContext(workflow.id, step.step_id, self.notice_manager)
                        
                        try:
                            result = await self.step_registry.execute(
                                step.step_id, 
                                step.params, 
                                context
                            )
                            workflow.step_results[step.step_id] = result
                            executed.add(step.step_id)
                            
                            await self.notice_manager.emit(Notice(
                                type=NoticeType.SUCCESS,
                                severity=NoticeSeverity.LOW,
                                title="Step Completed",
                                message=f"Step {step.step_id} completed successfully",
                                workflow_id=workflow.id,
                                step_id=step.step_id,
                                auto_dismiss_seconds=5
                            ))
                        except Exception as e:
                            await self.notice_manager.emit(Notice(
                                type=NoticeType.ERROR,
                                severity=NoticeSeverity.CRITICAL,
                                title="Step Failed",
                                message=str(e),
                                workflow_id=workflow.id,
                                step_id=step.step_id,
                                metadata={"traceback": traceback.format_exc()}
                            ))
                            raise
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            
            await self.notice_manager.emit(Notice(
                type=NoticeType.SUCCESS,
                severity=NoticeSeverity.MEDIUM,
                title="Workflow Completed",
                message=f"Workflow {workflow.definition.name} completed successfully",
                workflow_id=workflow.id,
                auto_dismiss_seconds=10
            ))
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            
            await self.notice_manager.emit(Notice(
                type=NoticeType.ERROR,
                severity=NoticeSeverity.CRITICAL,
                title="Workflow Failed",
                message=str(e),
                workflow_id=workflow.id,
                dismissible=False
            ))

# API Setup
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager)

app = FastAPI(title="Scientific Workflow API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example Step Registration
@step_registry.register(StepDefinition(
    id="data_validation",
    name="Data Validation",
    description="Validates input data format and constraints",
    params_schema={
        "type": "object",
        "properties": {
            "data_path": {"type": "string"},
            "schema": {"type": "object"}
        }
    }
))
async def validate_data(params: Dict[str, Any], context: StepContext):
    await context.info("Starting Validation", f"Validating data at {params.get('data_path', 'default path')}")
    # Simulate validation
    await asyncio.sleep(1)
    await context.info("Validation Progress", "Schema validation passed")
    await asyncio.sleep(0.5)
    await context.success("Validation Complete", "Data validation completed successfully")
    return {"valid": True, "records": 1000}

@step_registry.register(StepDefinition(
    id="data_processing",
    name="Data Processing",
    description="Processes validated data",
    params_schema={
        "type": "object",
        "properties": {
            "algorithm": {"type": "string"},
            "parameters": {"type": "object"}
        }
    }
))
async def process_data(params: Dict[str, Any], context: StepContext):
    await context.info("Processing Started", f"Using algorithm: {params.get('algorithm', 'default')}")
    # Simulate processing
    for i in range(5):
        await asyncio.sleep(0.5)
        await context.info("Processing Progress", f"Processed {(i+1)*20}% of data")
    await context.success("Processing Complete", "Data processing completed successfully")
    return {"processed_records": 1000, "output_path": "/results/processed.csv"}

@step_registry.register(StepDefinition(
    id="model_training",
    name="Model Training",
    description="Trains machine learning models on processed data",
    params_schema={
        "type": "object",
        "properties": {
            "model_type": {"type": "string"},
            "hyperparameters": {"type": "object"}
        }
    }
))
async def train_model(params: Dict[str, Any], context: StepContext):
    await context.info("Training Started", f"Training {params.get('model_type', 'neural network')} model")
    
    # Simulate training phases
    phases = ["Data preprocessing", "Feature engineering", "Model initialization", "Training", "Validation"]
    for i, phase in enumerate(phases):
        await asyncio.sleep(1)
        await context.info(f"Training Phase {i+1}", f"Completed: {phase}")
    
    await context.success("Training Complete", "Model trained successfully with 95% accuracy")
    return {"model_path": "/models/trained_model.pkl", "accuracy": 0.95}

@step_registry.register(StepDefinition(
    id="result_analysis",
    name="Result Analysis",
    description="Analyzes model results and generates reports",
    params_schema={
        "type": "object",
        "properties": {
            "analysis_type": {"type": "string"},
            "output_format": {"type": "string"}
        }
    }
))
async def analyze_results(params: Dict[str, Any], context: StepContext):
    await context.info("Analysis Started", f"Performing {params.get('analysis_type', 'comprehensive')} analysis")
    
    # Simulate analysis steps
    analysis_steps = ["Loading results", "Statistical analysis", "Visualization", "Report generation"]
    for step in analysis_steps:
        await asyncio.sleep(0.8)
        await context.info("Analysis Progress", f"Completed: {step}")
    
    await context.success("Analysis Complete", "Results analyzed and report generated")
    return {"report_path": "/reports/analysis_report.pdf", "charts": 5}

@step_registry.register(StepDefinition(
    id="data_cleaning",
    name="Data Cleaning",
    description="Cleans and preprocesses raw data",
    params_schema={
        "type": "object",
        "properties": {
            "cleaning_method": {"type": "string"},
            "remove_duplicates": {"type": "boolean"}
        }
    }
))
async def clean_data(params: Dict[str, Any], context: StepContext):
    await context.info("Cleaning Started", f"Using {params.get('cleaning_method', 'standard')} cleaning method")
    
    # Simulate cleaning steps
    cleaning_steps = ["Removing duplicates", "Handling missing values", "Outlier detection", "Data normalization"]
    for i, step in enumerate(cleaning_steps):
        await asyncio.sleep(0.7)
        await context.info(f"Cleaning Step {i+1}", f"Completed: {step}")
    
    await context.success("Cleaning Complete", "Data cleaned and ready for processing")
    return {"cleaned_records": 950, "removed_duplicates": 50}

@step_registry.register(StepDefinition(
    id="feature_engineering",
    name="Feature Engineering",
    description="Creates and selects features for machine learning",
    params_schema={
        "type": "object",
        "properties": {
            "feature_selection": {"type": "string"},
            "create_interactions": {"type": "boolean"}
        }
    }
))
async def engineer_features(params: Dict[str, Any], context: StepContext):
    await context.info("Feature Engineering Started", f"Using {params.get('feature_selection', 'correlation-based')} selection")
    
    # Simulate feature engineering
    feature_steps = ["Feature extraction", "Feature selection", "Feature scaling", "Interaction creation"]
    for i, step in enumerate(feature_steps):
        await asyncio.sleep(0.6)
        await context.info(f"Feature Step {i+1}", f"Completed: {step}")
    
    await context.success("Feature Engineering Complete", "Features engineered successfully")
    return {"features_created": 25, "selected_features": 15}

@step_registry.register(StepDefinition(
    id="model_evaluation",
    name="Model Evaluation",
    description="Evaluates model performance using various metrics",
    params_schema={
        "type": "object",
        "properties": {
            "metrics": {"type": "array"},
            "cross_validation": {"type": "boolean"}
        }
    }
))
async def evaluate_model(params: Dict[str, Any], context: StepContext):
    await context.info("Evaluation Started", "Evaluating model performance")
    
    # Simulate evaluation
    eval_steps = ["Accuracy calculation", "Precision/Recall", "F1 Score", "Cross-validation"]
    for i, step in enumerate(eval_steps):
        await asyncio.sleep(0.8)
        await context.info(f"Evaluation Step {i+1}", f"Completed: {step}")
    
    await context.success("Evaluation Complete", "Model evaluation completed with high performance")
    return {"accuracy": 0.92, "precision": 0.89, "recall": 0.91, "f1_score": 0.90}

@step_registry.register(StepDefinition(
    id="deployment_prep",
    name="Deployment Preparation",
    description="Prepares model for production deployment",
    params_schema={
        "type": "object",
        "properties": {
            "deployment_type": {"type": "string"},
            "api_format": {"type": "string"}
        }
    }
))
async def prepare_deployment(params: Dict[str, Any], context: StepContext):
    await context.info("Deployment Prep Started", f"Preparing for {params.get('deployment_type', 'REST API')} deployment")
    
    # Simulate deployment preparation
    prep_steps = ["Model serialization", "API wrapper creation", "Docker containerization", "Health checks"]
    for i, step in enumerate(prep_steps):
        await asyncio.sleep(0.9)
        await context.info(f"Prep Step {i+1}", f"Completed: {step}")
    
    await context.success("Deployment Ready", "Model ready for production deployment")
    return {"docker_image": "model:v1.0", "api_endpoint": "/predict", "health_check": "ready"}

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
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/notices")
async def websocket_notices(websocket: WebSocket):
    await websocket.accept()
    
    async def send_notice(notice: Notice):
        try:
            await websocket.send_json(notice.dict())
        except Exception as e:
            # Remove subscriber if connection is broken
            notice_manager.unsubscribe(send_notice)
            print(f"WebSocket send error: {e}")
    
    notice_manager.subscribe(send_notice)
    
    try:
        # Keep connection alive and handle disconnection
        while True:
            try:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                await asyncio.sleep(30)  # Ping every 30 seconds
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # Clean up subscriber when connection closes
        notice_manager.unsubscribe(send_notice)