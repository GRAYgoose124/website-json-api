from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid

# Enums
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

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Models
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

class StepDefinition(BaseModel):
    id: str
    name: str
    description: str
    callback: str
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