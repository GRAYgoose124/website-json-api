from typing import Dict, Any

from app.models import Notice, NoticeType, NoticeSeverity
from app.managers.notice import NoticeManager

class StepContext:
    def __init__(self, workflow_id: str, step_id: str, notice_manager: NoticeManager, workflow_context: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.notice_manager = notice_manager
        self.workflow_context = workflow_context
        self._result = None
    
    async def info(self, title: str, message: str, **kwargs):
        notice = Notice(
            type=NoticeType.INFO,
            severity=NoticeSeverity.LOW,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            metadata=kwargs
        )
        await self.notice_manager.emit(notice)
    
    async def warning(self, title: str, message: str, **kwargs):
        notice = Notice(
            type=NoticeType.WARNING,
            severity=NoticeSeverity.MEDIUM,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            metadata=kwargs
        )
        await self.notice_manager.emit(notice)
    
    async def error(self, title: str, message: str, **kwargs):
        notice = Notice(
            type=NoticeType.ERROR,
            severity=NoticeSeverity.HIGH,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            metadata=kwargs
        )
        await self.notice_manager.emit(notice)
    
    async def success(self, title: str, message: str, **kwargs):
        notice = Notice(
            type=NoticeType.SUCCESS,
            severity=NoticeSeverity.LOW,
            title=title,
            message=message,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
            metadata=kwargs
        )
        await self.notice_manager.emit(notice)
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the workflow context"""
        return self.workflow_context.get(key, default)
    
    def set_context_value(self, key: str, value: Any):
        """Set a value in the workflow context"""
        self.workflow_context[key] = value
    
    def set_result(self, result: Any):
        """Set the result for this step"""
        self._result = result
    
    def get_result(self) -> Any:
        """Get the result for this step"""
        return self._result

