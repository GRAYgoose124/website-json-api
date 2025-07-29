from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import asyncio
import traceback
from .models import Notice, NoticeType, NoticeSeverity, WorkflowStatus, StepDefinition, WorkflowInstance, DependencyResolution
from .dependency_resolver import DependencyResolver

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
        self.dependency_resolver: Optional[DependencyResolver] = None
    
    def register(self, definition: StepDefinition):
        def decorator(func: Callable):
            self.steps[definition.id] = func
            self.definitions[definition.id] = definition
            # Update dependency resolver if it exists
            if self.dependency_resolver:
                self.dependency_resolver.step_definitions = self.definitions
            return func
        return decorator
    
    def set_dependency_resolver(self, resolver: DependencyResolver):
        """Set the dependency resolver for this registry"""
        self.dependency_resolver = resolver
        resolver.step_definitions = self.definitions
    
    async def execute(self, step_id: str, params: Dict[str, Any], context: 'StepContext'):
        if step_id not in self.steps:
            raise ValueError(f"Step {step_id} not registered")
        
        step_func = self.steps[step_id]
        return await step_func(params, context)
    
    def get_step_definition(self, step_id: str) -> Optional[StepDefinition]:
        """Get step definition by ID"""
        return self.definitions.get(step_id)
    
    def validate_workflow(self, workflow_instance: WorkflowInstance) -> tuple[List[str], List[str]]:
        """Validate a workflow using the dependency resolver"""
        if not self.dependency_resolver:
            return [], []
        
        return self.dependency_resolver.validate_workflow(workflow_instance.definition)
    
    def resolve_dependencies(self, workflow_instance: WorkflowInstance) -> DependencyResolution:
        """Resolve dependencies for a workflow"""
        if not self.dependency_resolver:
            raise RuntimeError("Dependency resolver not initialized")
        
        return self.dependency_resolver.resolve_dependencies(workflow_instance.definition)

class StepContext:
    def __init__(self, workflow_id: str, step_id: str, notice_manager: NoticeManager, workflow_context: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.notice_manager = notice_manager
        self.workflow_context = workflow_context
        self.step_result = None
    
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
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the workflow context"""
        return self.workflow_context.get(key, default)
    
    def set_context_value(self, key: str, value: Any):
        """Set a value in the workflow context"""
        self.workflow_context[key] = value
    
    def set_result(self, result: Any):
        """Set the result of this step"""
        self.step_result = result

class WorkflowEngine:
    def __init__(self, step_registry: StepRegistry, notice_manager: NoticeManager):
        self.step_registry = step_registry
        self.notice_manager = notice_manager
        self.workflows: Dict[str, WorkflowInstance] = {}
        
        # Initialize dependency resolver
        self.dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(self.dependency_resolver)
    
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
            
            # Validate workflow before execution
            errors, warnings = self.step_registry.validate_workflow(workflow)
            
            if warnings:
                for warning in warnings:
                    await self.notice_manager.emit(Notice(
                        type=NoticeType.WARNING,
                        severity=NoticeSeverity.MEDIUM,
                        title="Workflow Warning",
                        message=warning,
                        workflow_id=workflow.id
                    ))
            
            if errors:
                error_msg = "Workflow validation failed:\n" + "\n".join(errors)
                await self.notice_manager.emit(Notice(
                    type=NoticeType.ERROR,
                    severity=NoticeSeverity.CRITICAL,
                    title="Workflow Validation Failed",
                    message=error_msg,
                    workflow_id=workflow.id,
                    dismissible=False
                ))
                raise ValueError(error_msg)
            
            # Resolve dependencies and get execution order
            resolution = self.step_registry.resolve_dependencies(workflow)
            
            await self.notice_manager.emit(Notice(
                type=NoticeType.INFO,
                severity=NoticeSeverity.LOW,
                title="Dependencies Resolved",
                message=f"Execution order: {' -> '.join(resolution.execution_order)}",
                workflow_id=workflow.id
            ))
            
            # Execute steps in dependency order
            for step_id in resolution.execution_order:
                workflow.current_step = step_id
                
                # Find the step definition
                step_def = None
                for step in workflow.definition.steps:
                    if step.step_id == step_id:
                        step_def = step
                        break
                
                if not step_def:
                    raise ValueError(f"Step {step_id} not found in workflow definition")
                
                context = StepContext(workflow.id, step_id, self.notice_manager, workflow.context)
                
                try:
                    await self.notice_manager.emit(Notice(
                        type=NoticeType.INFO,
                        severity=NoticeSeverity.LOW,
                        title="Step Started",
                        message=f"Executing step: {step_id}",
                        workflow_id=workflow.id,
                        step_id=step_id
                    ))
                    
                    # Execute the step
                    result = await self.step_registry.execute(
                        step_id, 
                        step_def.params, 
                        context
                    )
                    
                    # Store the result
                    workflow.step_results[step_id] = result
                    
                    # Add step outputs to context
                    step_definition = self.step_registry.get_step_definition(step_id)
                    if step_definition:
                        for context_key in step_definition.io.context_keys:
                            workflow.context[context_key] = result
                    
                    await self.notice_manager.emit(Notice(
                        type=NoticeType.SUCCESS,
                        severity=NoticeSeverity.LOW,
                        title="Step Completed",
                        message=f"Step {step_id} completed successfully",
                        workflow_id=workflow.id,
                        step_id=step_id,
                        auto_dismiss_seconds=5
                    ))
                    
                except Exception as e:
                    await self.notice_manager.emit(Notice(
                        type=NoticeType.ERROR,
                        severity=NoticeSeverity.CRITICAL,
                        title="Step Failed",
                        message=str(e),
                        workflow_id=workflow.id,
                        step_id=step_id,
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
    
    def get_workflow_dependencies(self, workflow_id: str) -> Optional[DependencyResolution]:
        """Get dependency resolution for a workflow"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        return self.step_registry.resolve_dependencies(workflow)

# Global instances
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager) 