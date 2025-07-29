from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import asyncio
import traceback
from .models import Notice, NoticeType, NoticeSeverity, WorkflowStatus, StepDefinition

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
        self.workflows: Dict[str, 'WorkflowInstance'] = {}
    
    async def execute_workflow(self, workflow: 'WorkflowInstance'):
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

# Global instances
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager) 