from typing import Dict, Callable, Optional, List, Any

from app.models import StepDefinition, WorkflowInstance, DependencyResolution
from app.dependency_resolver import DependencyResolver
from app.step.context import StepContext

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
