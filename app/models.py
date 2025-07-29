from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
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

class DataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    FILE = "file"
    DATASET = "dataset"
    MODEL = "model"
    IMAGE = "image"
    TEXT = "text"
    JSON = "json"

# IO Schema Models
class IOSchema(BaseModel):
    """Schema for input/output parameters"""
    name: str
    type: DataType
    description: str
    required: bool = True
    default: Optional[Any] = None
    format: Optional[str] = None  # e.g., "csv", "json", "png", etc.
    constraints: Optional[Dict[str, Any]] = None  # e.g., min/max values, patterns, etc.

class StepIO(BaseModel):
    """Input/Output definition for a step"""
    inputs: List[IOSchema] = []
    outputs: List[IOSchema] = []
    context_keys: List[str] = []  # Keys this step adds to the context

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
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    io: StepIO = Field(default_factory=StepIO)
    category: Optional[str] = None  # e.g., "data_processing", "visualization", "ml"
    tags: List[str] = []

class WorkflowStep(BaseModel):
    step_id: str
    params: Dict[str, Any] = {}
    depends_on: List[str] = []
    # Auto-generated dependencies based on IO requirements
    auto_dependencies: List[str] = Field(default_factory=list)
    # Context keys this step provides
    provides: List[str] = Field(default_factory=list)
    # Context keys this step requires
    requires: List[str] = Field(default_factory=list)

class WorkflowDefinition(BaseModel):
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = {}
    # Validation results
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

class WorkflowInstance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = {}
    context: Dict[str, Any] = Field(default_factory=dict)  # Shared context between steps
    notices: List[Notice] = []

class DependencyResolution(BaseModel):
    """Result of dependency resolution for a workflow"""
    workflow_id: str
    execution_order: List[str]  # Ordered list of step IDs
    dependencies: Dict[str, List[str]]  # Step ID -> list of dependencies
    dependents: Dict[str, List[str]]  # Step ID -> list of dependents
    cycles: List[List[str]] = Field(default_factory=list)  # Circular dependencies
    missing_dependencies: List[str] = Field(default_factory=list)  # Steps that can't be resolved
    context_flow: Dict[str, Dict[str, str]] = Field(default_factory=dict)  # Step ID -> {context_key -> provider_step_id} 