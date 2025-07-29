#!/usr/bin/env python3
"""
Test script for dependency resolution system
"""
import asyncio
import sys
import os
import pytest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance
from app.dependency_resolver import DependencyResolver
from app.step_loader import StepLoader

def test_dependency_resolution():
    """Test the dependency resolution system with actual step definitions"""
    print("🧪 Testing Dependency Resolution System")
    print("=" * 50)
    
    # Load actual step definitions from project_steps
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
    
    # Create dependency resolver with actual steps
    resolver = DependencyResolver(step_definitions)
    
    # Test 1: Simple project workflow
    print("\n📋 Test 1: Simple Project Workflow")
    workflow1 = WorkflowDefinition(
        name="Simple Project Pipeline",
        description="A simple project management pipeline",
        steps=[
            WorkflowStep(step_id="create_project", params={"project_name": "Test Project"}),
            WorkflowStep(step_id="upload_file_to_project", params={"file_path": "/tmp/test.txt", "destination_path": "data/test.txt"}),
            WorkflowStep(step_id="download_project_zip", params={"include_hidden": False}),
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
            WorkflowStep(step_id="upload_file_to_project", params={"file_path": "/tmp/test.txt"}),  # Requires project_token
            WorkflowStep(step_id="download_project_zip", params={}),  # Requires project_token
        ]
    )
    
    resolution2 = resolver.resolve_dependencies(workflow2)
    print(f"Execution order: {' -> '.join(resolution2.execution_order)}")
    print(f"Missing dependencies: {resolution2.missing_dependencies}")
    
    # Test 3: Complex workflow with all dependencies
    print("\n📋 Test 3: Complex Complete Workflow")
    workflow3 = WorkflowDefinition(
        name="Complete Project Pipeline",
        description="A complete project management pipeline",
        steps=[
            WorkflowStep(step_id="create_project", params={"project_name": "Complete Test", "description": "A complete test"}),
            WorkflowStep(step_id="upload_file_to_project", params={"file_path": "/tmp/test1.txt", "destination_path": "data/file1.txt"}),
            WorkflowStep(step_id="upload_file_to_project", params={"file_path": "/tmp/test2.txt", "destination_path": "data/file2.txt"}),
            WorkflowStep(step_id="list_project_files", params={"recursive": True, "include_hidden": False}),
            WorkflowStep(step_id="download_project_zip", params={"include_hidden": False, "compression_level": 6}),
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
    
    # Load actual step definitions
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
    
    for step_id, definition in step_definitions.items():
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

def test_custom_steps_dependencies():
    """Test dependency resolution with custom steps"""
    print("\n🔧 Testing Custom Steps Dependencies")
    print("=" * 40)
    
    # Load custom step definitions
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/custom")
    
    resolver = DependencyResolver(step_definitions)
    
    # Test ML pipeline workflow
    workflow = WorkflowDefinition(
        name="ML Pipeline",
        description="A machine learning pipeline",
        steps=[
            WorkflowStep(step_id="data_validation", params={"data_path": "/data/input.csv"}),
            WorkflowStep(step_id="data_processing", params={"algorithm": "standard"}),
            WorkflowStep(step_id="model_training", params={"model_type": "neural_network"}),
            WorkflowStep(step_id="result_analysis", params={"analysis_type": "comprehensive"}),
        ]
    )
    
    resolution = resolver.resolve_dependencies(workflow)
    print(f"Execution order: {' -> '.join(resolution.execution_order)}")
    print(f"Has cycles: {len(resolution.cycles) > 0}")
    print(f"Missing dependencies: {len(resolution.missing_dependencies)}")
    
    # Test validation
    errors, warnings = resolver.validate_workflow(workflow)
    print(f"ML Pipeline - Valid: {len(errors) == 0}, Errors: {len(errors)}, Warnings: {len(warnings)}")

if __name__ == "__main__":
    test_step_definitions()
    test_dependency_resolution()
    test_custom_steps_dependencies() 