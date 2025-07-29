#!/usr/bin/env python3
"""
Test script for dependency resolution system
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance
from app.dependency_resolver import DependencyResolver
from app.example_steps import EXAMPLE_STEP_DEFINITIONS

def test_dependency_resolution():
    """Test the dependency resolution system"""
    print("🧪 Testing Dependency Resolution System")
    print("=" * 50)
    
    # Create dependency resolver with example steps
    resolver = DependencyResolver(EXAMPLE_STEP_DEFINITIONS)
    
    # Test 1: Simple linear workflow
    print("\n📋 Test 1: Simple Linear Workflow")
    workflow1 = WorkflowDefinition(
        name="Simple ML Pipeline",
        description="A simple machine learning pipeline",
        steps=[
            WorkflowStep(step_id="load_data", params={"file_path": "data.csv"}),
            WorkflowStep(step_id="clean_data", params={"remove_duplicates": True}),
            WorkflowStep(step_id="feature_engineering", params={}),
            WorkflowStep(step_id="train_model", params={"target_column": "target"}),
        ]
    )
    
    resolution1 = resolver.resolve_dependencies(workflow1)
    print(f"Execution order: {' -> '.join(resolution1.execution_order)}")
    print(f"Has cycles: {len(resolution1.cycles) > 0}")
    print(f"Missing dependencies: {len(resolution1.missing_dependencies)}")
    
    # Test 2: Workflow with missing dependencies
    print("\n📋 Test 2: Workflow with Missing Dependencies")
    workflow2 = WorkflowDefinition(
        name="Invalid Workflow",
        description="A workflow with missing dependencies",
        steps=[
            WorkflowStep(step_id="clean_data", params={}),  # Requires dataset but no step provides it
            WorkflowStep(step_id="train_model", params={"target_column": "target"}),  # Requires featured_dataset
        ]
    )
    
    resolution2 = resolver.resolve_dependencies(workflow2)
    print(f"Execution order: {' -> '.join(resolution2.execution_order)}")
    print(f"Missing dependencies: {resolution2.missing_dependencies}")
    
    # Test 3: Complex workflow with all dependencies
    print("\n📋 Test 3: Complex Complete Workflow")
    workflow3 = WorkflowDefinition(
        name="Complete ML Pipeline",
        description="A complete machine learning pipeline",
        steps=[
            WorkflowStep(step_id="load_data", params={"file_path": "data.csv"}),
            WorkflowStep(step_id="clean_data", params={"remove_duplicates": True}),
            WorkflowStep(step_id="feature_engineering", params={}),
            WorkflowStep(step_id="train_model", params={"target_column": "target"}),
            WorkflowStep(step_id="evaluate_model", params={}),
            WorkflowStep(step_id="generate_report", params={}),
            WorkflowStep(step_id="save_results", params={"output_path": "./output"}),
        ]
    )
    
    resolution3 = resolver.resolve_dependencies(workflow3)
    print(f"Execution order: {' -> '.join(resolution3.execution_order)}")
    print(f"Has cycles: {len(resolution3.cycles) > 0}")
    print(f"Missing dependencies: {len(resolution3.missing_dependencies)}")
    
    # Test 4: Workflow validation
    print("\n📋 Test 4: Workflow Validation")
    errors1, warnings1 = resolver.validate_workflow(workflow1)
    errors2, warnings2 = resolver.validate_workflow(workflow2)
    errors3, warnings3 = resolver.validate_workflow(workflow3)
    
    print(f"Workflow 1 - Valid: {len(errors1) == 0}, Errors: {len(errors1)}, Warnings: {len(warnings1)}")
    print(f"Workflow 2 - Valid: {len(errors2) == 0}, Errors: {len(errors2)}, Warnings: {len(warnings2)}")
    print(f"Workflow 3 - Valid: {len(errors3) == 0}, Errors: {len(errors3)}, Warnings: {len(warnings3)}")
    
    # Test 5: Context flow analysis
    print("\n📋 Test 5: Context Flow Analysis")
    print("Context flow for workflow 3:")
    for step_id, context_flow in resolution3.context_flow.items():
        if context_flow:
            print(f"  {step_id}: {context_flow}")
    
    print("\n✅ Dependency resolution tests completed!")

def test_step_definitions():
    """Test step definitions and IO schemas"""
    print("\n🔧 Testing Step Definitions")
    print("=" * 30)
    
    for step_id, definition in EXAMPLE_STEP_DEFINITIONS.items():
        print(f"\n📦 {step_id}:")
        print(f"  Name: {definition.name}")
        print(f"  Category: {definition.category}")
        print(f"  Tags: {', '.join(definition.tags)}")
        print(f"  Inputs: {len(definition.io.inputs)}")
        print(f"  Outputs: {len(definition.io.outputs)}")
        print(f"  Context keys: {definition.io.context_keys}")
        
        if definition.io.inputs:
            print("  Input schemas:")
            for input_schema in definition.io.inputs:
                print(f"    - {input_schema.name} ({input_schema.type}) {'[required]' if input_schema.required else '[optional]'}")

if __name__ == "__main__":
    test_step_definitions()
    test_dependency_resolution() 