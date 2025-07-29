from .managers.project import ProjectManager
from .managers.notice import NoticeManager
from .step.registry import StepRegistry
from .step.context import StepContext
from .workflow_engine import WorkflowEngine

# Global instances
project_manager = ProjectManager()
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager)

# Export classes for backward compatibility
__all__ = [
    'ProjectManager',
    'NoticeManager', 
    'StepRegistry',
    'StepContext',
    'WorkflowEngine',
    'project_manager',
    'notice_manager',
    'step_registry',
    'workflow_engine'
] 