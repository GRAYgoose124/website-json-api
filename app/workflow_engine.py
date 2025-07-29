from typing import Dict, Any, Optional
from datetime import datetime, UTC
from app.models import WorkflowInstance, WorkflowStatus, WorkflowStep, DependencyResolution, Notice, NoticeType, NoticeSeverity
from app.step.registry import StepRegistry
from app.managers.notice import NoticeManager
from app.step.context import StepContext

    
class WorkflowEngine:
    def __init__(self, step_registry: StepRegistry, notice_manager: NoticeManager):
        self.step_registry = step_registry
        self.notice_manager = notice_manager
        self.workflows: Dict[str, WorkflowInstance] = {}
    
    async def execute_workflow(self, workflow: WorkflowInstance):
        """Execute a workflow with proper project isolation"""
        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now(UTC)
            
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
                    workflow.completed_at = datetime.now(UTC)
                    return
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(UTC)
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now(UTC)
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
