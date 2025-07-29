from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import asyncio
import traceback
import os
import uuid
import hashlib
from pathlib import Path
from .models import Notice, NoticeType, NoticeSeverity, WorkflowStatus, StepDefinition, WorkflowInstance, DependencyResolution, WorkflowStep
from .dependency_resolver import DependencyResolver

class ProjectManager:
    """Manages project isolation and security"""
    
    def __init__(self, projects_root: str = None):
        self.projects_root = projects_root
        self.project_tokens: Dict[str, Dict[str, Any]] = {}  # token_hash -> project_info
    
    def create_project(self, project_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new isolated project"""
        # Generate project UUID
        project_id = str(uuid.uuid4())
        
        # Create project directory (isolated)
        project_path = self.projects_root / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Generate secure project token
        raw_token = f"{project_id}_{datetime.utcnow().isoformat()}_{uuid.uuid4()}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Store project info
        project_info = {
            'project_id': project_id,
            'project_path': str(project_path),
            'project_name': project_name,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'raw_token': raw_token
        }
        self.project_tokens[token_hash] = project_info
        
        # Create project metadata file
        metadata = {
            'project_id': project_id,
            'project_name': project_name,
            'description': description,
            'created_at': project_info['created_at'],
            'token_hash': token_hash
        }
        
        metadata_path = project_path / '.project_metadata.json'
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'project_id': project_id,
            'project_path': str(project_path),
            'project_token': token_hash
        }
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a project token and return project info"""
        return self.project_tokens.get(token)
    
    def get_project_path(self, token: str) -> Optional[str]:
        """Get project path for a valid token"""
        project_info = self.validate_token(token)
        return project_info['project_path'] if project_info else None


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

class WorkflowEngine:
    def __init__(self, step_registry: StepRegistry, notice_manager: NoticeManager):
        self.step_registry = step_registry
        self.notice_manager = notice_manager
        self.workflows: Dict[str, WorkflowInstance] = {}
    
    async def execute_workflow(self, workflow: WorkflowInstance):
        """Execute a workflow with proper project isolation"""
        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.utcnow()
            
            # Initialize workflow context
            workflow.context = {}
            
            # Store workflow in the engine's workflow list
            self.workflows[workflow.id] = workflow
            
            # Resolve dependencies
            dependency_resolution = self.step_registry.resolve_dependencies(workflow)
            
            # Execute steps in dependency order
            for step_id in dependency_resolution.execution_order:
                workflow.current_step = step_id
                
                # Find the step in the workflow
                step = next((s for s in workflow.definition.steps if s.step_id == step_id), None)
                if not step:
                    continue
                
                # Prepare step parameters with context values
                params = self._prepare_step_params(step, workflow.context)
                
                # Create step context
                context = StepContext(
                    workflow_id=workflow.id,
                    step_id=step_id,
                    notice_manager=self.notice_manager,
                    workflow_context=workflow.context
                )
                
                try:
                    # Execute the step
                    result = await self.step_registry.execute(step_id, params, context)
                    
                    # Store result
                    workflow.step_results[step_id] = result
                    
                    # Update workflow context with step outputs
                    self._update_workflow_context(workflow, step_id, result)
                    
                except Exception as e:
                    await context.error("Step Failed", f"Step {step_id} failed: {str(e)}")
                    workflow.status = WorkflowStatus.FAILED
                    workflow.completed_at = datetime.utcnow()
                    return
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            await self.notice_manager.emit(Notice(
                type=NoticeType.ERROR,
                severity=NoticeSeverity.HIGH,
                title="Workflow Failed",
                message=f"Workflow execution failed: {str(e)}",
                workflow_id=workflow.id
            ))
    
    def _prepare_step_params(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare step parameters, filling in context values where needed"""
        params = step.params.copy()
        
        # For project steps, handle special cases
        if step.step_id == "create_project":
            # Remove projects_root from user parameters for security
            params.pop('projects_root', None)
        elif step.step_id in ["upload_file_to_project", "download_project_zip", "validate_project_token", "list_project_files"]:
            # Auto-fill project_token from context if not provided or empty
            if not params.get('project_token') and 'project_token' in context:
                params['project_token'] = context['project_token']
        
        # Fill in any other context values that match parameter names
        for param_name in params.keys():
            if param_name in context and not params.get(param_name):
                params[param_name] = context[param_name]
        
        return params
    
    def _update_workflow_context(self, workflow: WorkflowInstance, step_id: str, result: Dict[str, Any]):
        """Update workflow context with step results"""
        step_def = self.step_registry.get_step_definition(step_id)
        if not step_def:
            return
        
        # Add context keys defined by the step
        for context_key in step_def.io.context_keys:
            if context_key in result:
                workflow.context[context_key] = result[context_key]
        
        # Also add all outputs to context for convenience
        for output_schema in step_def.io.outputs:
            if output_schema.name in result:
                workflow.context[output_schema.name] = result[output_schema.name]
    
    def get_workflow_dependencies(self, workflow_id: str) -> Optional[DependencyResolution]:
        """Get dependency resolution for a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        return self.step_registry.resolve_dependencies(workflow)

# Global instances
project_manager = ProjectManager()
notice_manager = NoticeManager()
step_registry = StepRegistry()
workflow_engine = WorkflowEngine(step_registry, notice_manager) 