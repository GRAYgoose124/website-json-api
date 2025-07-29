from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from .models import WorkflowDefinition, WorkflowStep, StepDefinition, DependencyResolution, StepIO
import logging

logger = logging.getLogger(__name__)

class DependencyResolver:
    """Handles dependency resolution for workflow steps based on IO requirements"""
    
    def __init__(self, step_definitions: Dict[str, StepDefinition]):
        self.step_definitions = step_definitions
    
    def resolve_dependencies(self, workflow: WorkflowDefinition) -> DependencyResolution:
        """
        Resolve dependencies for a workflow based on step IO requirements
        
        Args:
            workflow: The workflow definition to resolve
            
        Returns:
            DependencyResolution object with execution order and dependency information
        """
        # Build step lookup
        step_lookup = {step.step_id: step for step in workflow.steps}
        
        # Analyze IO requirements and build context flow
        context_providers = {}  # context_key -> step_id
        context_consumers = defaultdict(list)  # context_key -> [step_ids]
        
        # First pass: identify what each step provides
        for step in workflow.steps:
            step_def = self.step_definitions.get(step.step_id)
            if not step_def:
                continue
            
            # What this step provides
            for context_key in step_def.io.context_keys:
                if context_key in context_providers:
                    logger.warning(f"Multiple steps provide context key '{context_key}': "
                                f"{context_providers[context_key]} and {step.step_id}")
                context_providers[context_key] = step.step_id
                step.provides.append(context_key)
        
        # Second pass: identify what each step requires
        for step in workflow.steps:
            step_def = self.step_definitions.get(step.step_id)
            if not step_def:
                continue
            
            # What this step requires
            for input_schema in step_def.io.inputs:
                # Consider both required and optional inputs that have context providers
                # This ensures proper dependency ordering even for optional inputs
                if input_schema.name in context_providers:
                    provider_step = context_providers[input_schema.name]
                    if provider_step != step.step_id:
                        step.requires.append(input_schema.name)
                        context_consumers[input_schema.name].append(step.step_id)
        
        # Build dependency graph
        dependencies = defaultdict(list)
        dependents = defaultdict(list)
        
        for step in workflow.steps:
            # Manual dependencies
            for dep in step.depends_on:
                if dep in step_lookup:
                    dependencies[step.step_id].append(dep)
                    dependents[dep].append(step.step_id)
            
            # Auto-generated dependencies based on context requirements
            for context_key in step.requires:
                if context_key in context_providers:
                    provider_step = context_providers[context_key]
                    if provider_step != step.step_id and provider_step not in dependencies[step.step_id]:
                        dependencies[step.step_id].append(provider_step)
                        dependents[provider_step].append(step.step_id)
                        step.auto_dependencies.append(provider_step)
        
        # Detect cycles
        cycles = self._detect_cycles(dependencies)
        
        # Find execution order (topological sort)
        execution_order = self._topological_sort(dependencies, workflow)
        
        # Find missing dependencies
        missing_dependencies = []
        for step in workflow.steps:
            for context_key in step.requires:
                if context_key not in context_providers:
                    missing_dependencies.append(f"Step '{step.step_id}' requires '{context_key}' but no step provides it")
        
        # Build context flow mapping
        context_flow = {}
        for step in workflow.steps:
            context_flow[step.step_id] = {}
            for context_key in step.requires:
                if context_key in context_providers:
                    context_flow[step.step_id][context_key] = context_providers[context_key]
        
        return DependencyResolution(
            workflow_id=workflow.name,
            execution_order=execution_order,
            dependencies=dict(dependencies),
            dependents=dict(dependents),
            cycles=cycles,
            missing_dependencies=missing_dependencies,
            context_flow=context_flow
        )
    
    def _detect_cycles(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, []):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for node in dependencies:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _topological_sort(self, dependencies: Dict[str, List[str]], workflow: WorkflowDefinition) -> List[str]:
        """Perform topological sort to determine execution order"""
        # Build dependents dictionary (reverse of dependencies)
        dependents = defaultdict(list)
        for node, deps in dependencies.items():
            for dep in deps:
                dependents[dep].append(node)
        
        # Calculate in-degrees for all steps in the workflow
        in_degree = defaultdict(int)
        
        # Initialize in-degree for all steps (including those without dependencies)
        for step in workflow.steps:
            in_degree[step.step_id] = 0
        
        # Add dependencies to in-degree calculation
        for node, deps in dependencies.items():
            for dep in deps:
                in_degree[node] += 1
        
        # Kahn's algorithm
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for dependents
            for dependent in dependents[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles (if not all nodes are in result)
        if len(result) != len(in_degree):
            # Find nodes not in result (part of cycles)
            remaining = set(in_degree.keys()) - set(result)
            result.extend(list(remaining))
        
        return result
    
    def validate_workflow(self, workflow: WorkflowDefinition) -> Tuple[List[str], List[str]]:
        """
        Validate a workflow definition
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check if all steps exist
        for step in workflow.steps:
            if step.step_id not in self.step_definitions:
                errors.append(f"Step '{step.step_id}' is not defined")
        
        # Resolve dependencies to get validation info
        resolution = self.resolve_dependencies(workflow)
        
        # Check for cycles
        if resolution.cycles:
            for cycle in resolution.cycles:
                errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        # Check for missing dependencies
        errors.extend(resolution.missing_dependencies)
        
        # Check for unused context keys
        all_provided_keys = set()
        all_required_keys = set()
        
        for step in workflow.steps:
            step_def = self.step_definitions.get(step.step_id)
            if step_def:
                all_provided_keys.update(step_def.io.context_keys)
                all_required_keys.update([input_schema.name for input_schema in step_def.io.inputs])
        
        unused_keys = all_provided_keys - all_required_keys
        if unused_keys:
            warnings.append(f"Unused context keys: {', '.join(unused_keys)}")
        
        return errors, warnings
    
    def get_step_dependencies(self, step_id: str, workflow: WorkflowDefinition) -> Dict[str, List[str]]:
        """Get all dependencies for a specific step"""
        resolution = self.resolve_dependencies(workflow)
        return {
            'manual': [dep for dep in workflow.steps if dep.step_id == step_id][0].depends_on,
            'auto': resolution.dependencies.get(step_id, []),
            'all': resolution.dependencies.get(step_id, [])
        }
    
    def get_step_dependents(self, step_id: str, workflow: WorkflowDefinition) -> List[str]:
        """Get all steps that depend on a specific step"""
        resolution = self.resolve_dependencies(workflow)
        return resolution.dependents.get(step_id, [])
    
    def get_context_flow(self, workflow: WorkflowDefinition) -> Dict[str, Dict[str, str]]:
        """Get the context flow for a workflow"""
        resolution = self.resolve_dependencies(workflow)
        return resolution.context_flow 