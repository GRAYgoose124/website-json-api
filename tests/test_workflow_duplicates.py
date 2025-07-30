import json
from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStatus
from app.dependency_resolver import DependencyResolver
from app.step.loader import StepLoader


def test_workflow_no_duplicates():
    """Test that workflow JSON doesn't have duplicate entries in arrays"""
    print("\n🔧 Testing Workflow JSON - No Duplicates")
    print("=" * 50)
    
    # Create step loader and dependency resolver
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
    dependency_resolver = DependencyResolver(step_definitions)
    
    # Create a workflow similar to the one in the user's message
    workflow_def = WorkflowDefinition(
        name="zaza",
        description="Test workflow for duplicate detection",
        steps=[
            WorkflowStep(
                step_id="create_project",
                params={}
            ),
            WorkflowStep(
                step_id="upload_file_to_project",
                params={
                    "file_path": "/home/goose/Documents/website-json-api/userdata/uploads/20250730_065845_test_gpu_integration.py"
                }
            ),
            WorkflowStep(
                step_id="download_project_zip",
                params={
                    "include_hidden": True
                }
            ),
            WorkflowStep(
                step_id="list_project_files",
                params={
                    "include_hidden": True
                }
            )
        ]
    )
    
    # Create workflow instance
    workflow_instance = WorkflowInstance(
        id="d7812e74-1f9f-4ae5-ac70-36b74c5e5463",
        definition=workflow_def,
        status=WorkflowStatus.PENDING
    )
    
    # Resolve dependencies multiple times to test for accumulation
    print("Resolving dependencies...")
    resolution1 = dependency_resolver.resolve_dependencies(workflow_def)
    
    print("Resolving dependencies again...")
    resolution2 = dependency_resolver.resolve_dependencies(workflow_def)
    
    print("Resolving dependencies a third time...")
    resolution3 = dependency_resolver.resolve_dependencies(workflow_def)
    
    # Check that all resolutions are identical
    assert resolution1.execution_order == resolution2.execution_order
    assert resolution2.execution_order == resolution3.execution_order
    
    # Check each step for duplicates
    for step in workflow_def.steps:
        print(f"\n📦 Step: {step.step_id}")
        print(f"  Provides: {step.provides}")
        print(f"  Requires: {step.requires}")
        print(f"  Auto Dependencies: {step.auto_dependencies}")
        
        # Check for duplicates in provides
        assert len(step.provides) == len(set(step.provides)), f"Duplicates found in provides for {step.step_id}: {step.provides}"
        
        # Check for duplicates in requires
        assert len(step.requires) == len(set(step.requires)), f"Duplicates found in requires for {step.step_id}: {step.requires}"
        
        # Check for duplicates in auto_dependencies
        assert len(step.auto_dependencies) == len(set(step.auto_dependencies)), f"Duplicates found in auto_dependencies for {step.step_id}: {step.auto_dependencies}"
    
    # Convert to JSON and check for duplicates in the serialized form
    workflow_dict = workflow_instance.model_dump()
    
    # Check the steps array in the JSON
    for step_dict in workflow_dict['definition']['steps']:
        step_id = step_dict['step_id']
        
        # Check provides array
        provides = step_dict['provides']
        assert len(provides) == len(set(provides)), f"Duplicates in JSON provides for {step_id}: {provides}"
        
        # Check requires array
        requires = step_dict['requires']
        assert len(requires) == len(set(requires)), f"Duplicates in JSON requires for {step_id}: {requires}"
        
        # Check auto_dependencies array
        auto_deps = step_dict['auto_dependencies']
        assert len(auto_deps) == len(set(auto_deps)), f"Duplicates in JSON auto_dependencies for {step_id}: {auto_deps}"
    
    print("✅ No duplicates found in workflow JSON")
    
    # Print the workflow JSON for inspection
    print("\n📄 Workflow JSON:")
    print(json.dumps(workflow_dict, indent=2, default=str))


def test_multiple_upload_steps_no_duplicates():
    """Test that multiple upload steps work without duplicates"""
    print("\n📤 Testing Multiple Upload Steps - No Duplicates")
    print("=" * 55)
    
    # Create step loader and dependency resolver
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
    dependency_resolver = DependencyResolver(step_definitions)
    
    # Create a workflow with multiple upload steps
    workflow_def = WorkflowDefinition(
        name="Multiple Uploads Test",
        description="Testing multiple upload steps without duplicates",
        steps=[
            WorkflowStep(
                step_id="create_project",
                params={"project_name": "Multi Upload Test"}
            ),
            WorkflowStep(
                step_id="upload_file_to_project",
                params={"file_path": "/test/file1.txt", "destination_path": "data/file1.txt"}
            ),
            WorkflowStep(
                step_id="upload_file_to_project",
                params={"file_path": "/test/file2.txt", "destination_path": "data/file2.txt"}
            ),
            WorkflowStep(
                step_id="upload_file_to_project",
                params={"file_path": "/test/file3.txt", "destination_path": "scripts/file3.txt"}
            ),
            WorkflowStep(
                step_id="list_project_files",
                params={"recursive": True}
            )
        ]
    )
    
    # Create workflow instance
    workflow_instance = WorkflowInstance(
        id="test-multiple-uploads",
        definition=workflow_def,
        status=WorkflowStatus.PENDING
    )
    
    # Resolve dependencies multiple times
    for i in range(5):
        print(f"Resolution {i+1}...")
        resolution = dependency_resolver.resolve_dependencies(workflow_def)
    
    # Check each step for duplicates
    for step in workflow_def.steps:
        print(f"\n📦 Step: {step.step_id} (instance: {step.instance_id[:8]}...)")
        print(f"  Provides: {step.provides}")
        print(f"  Requires: {step.requires}")
        print(f"  Auto Dependencies: {step.auto_dependencies}")
        
        # Check for duplicates
        assert len(step.provides) == len(set(step.provides)), f"Duplicates found in provides for {step.step_id}"
        assert len(step.requires) == len(set(step.requires)), f"Duplicates found in requires for {step.step_id}"
        assert len(step.auto_dependencies) == len(set(step.auto_dependencies)), f"Duplicates found in auto_dependencies for {step.step_id}"
    
    # Convert to JSON and verify
    workflow_dict = workflow_instance.model_dump()
    
    # Count upload steps
    upload_steps = [s for s in workflow_dict['definition']['steps'] if s['step_id'] == 'upload_file_to_project']
    assert len(upload_steps) == 3, f"Expected 3 upload steps, found {len(upload_steps)}"
    
    print(f"✅ Found {len(upload_steps)} upload steps without duplicates")


if __name__ == "__main__":
    print("🧪 Running Workflow Duplicate Tests")
    print("=" * 50)
    
    test_workflow_no_duplicates()
    test_multiple_upload_steps_no_duplicates()
    
    print("\n🎉 All workflow duplicate tests passed!") 