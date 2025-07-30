import pytest
from pathlib import Path
from app.models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStatus
from app.dependency_resolver import DependencyResolver
from app.step.loader import StepLoader
from app.managers.project import ProjectManager


class TestDependencyResolution:
    """Test cases for dependency resolution functionality"""
    
    @pytest.fixture
    def step_loader(self):
        """Create a step loader for testing"""
        return StepLoader()
    
    @pytest.fixture
    def dependency_resolver(self, step_loader):
        """Create a dependency resolver with loaded step definitions"""
        step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
        return DependencyResolver(step_definitions)
    
    def test_dependency_resolution_no_duplicates(self, dependency_resolver):
        """Test that dependency resolution doesn't create duplicate entries"""
        print("\n🔧 Testing Dependency Resolution - No Duplicates")
        print("=" * 50)
        
        # Create a workflow with multiple steps
        workflow_def = WorkflowDefinition(
            name="Test Workflow",
            description="Testing dependency resolution",
            steps=[
                WorkflowStep(
                    step_id="create_project",
                    params={"project_name": "Test Project"}
                ),
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={"file_path": "/test/file.txt"}
                ),
                WorkflowStep(
                    step_id="list_project_files",
                    params={"recursive": True}
                ),
                WorkflowStep(
                    step_id="download_project_zip",
                    params={"include_hidden": False}
                )
            ]
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
        
        # Check that step lists don't have duplicates
        for step in workflow_def.steps:
            print(f"\n📦 Step: {step.step_id}")
            print(f"  Provides: {step.provides}")
            print(f"  Requires: {step.requires}")
            print(f"  Auto Dependencies: {step.auto_dependencies}")
            
            # Check for duplicates in provides
            assert len(step.provides) == len(set(step.provides)), f"Duplicates found in provides for {step.step_id}"
            
            # Check for duplicates in requires
            assert len(step.requires) == len(set(step.requires)), f"Duplicates found in requires for {step.step_id}"
            
            # Check for duplicates in auto_dependencies
            assert len(step.auto_dependencies) == len(set(step.auto_dependencies)), f"Duplicates found in auto_dependencies for {step.step_id}"
        
        print("✅ No duplicates found in dependency resolution")
    
    def test_multiple_upload_steps(self, dependency_resolver):
        """Test that multiple upload steps can be used in the same workflow"""
        print("\n📤 Testing Multiple Upload Steps")
        print("=" * 40)
        
        # Create a workflow with multiple upload steps
        workflow_def = WorkflowDefinition(
            name="Multiple Uploads Test",
            description="Testing multiple upload steps",
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
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow_def)
        
        print(f"Execution order: {resolution.execution_order}")
        
        # Verify that create_project comes first
        assert resolution.execution_order[0] == "create_project"
        
        # Verify that list_project_files comes after uploads
        assert "list_project_files" in resolution.execution_order
        create_project_index = resolution.execution_order.index("create_project")
        list_files_index = resolution.execution_order.index("list_project_files")
        assert list_files_index > create_project_index
        
        # Check that all upload steps depend on create_project
        upload_steps = [step for step in workflow_def.steps if step.step_id == "upload_file_to_project"]
        assert len(upload_steps) == 3
        
        for upload_step in upload_steps:
            print(f"\n📤 Upload step provides: {upload_step.provides}")
            print(f"  Upload step requires: {upload_step.requires}")
            print(f"  Upload step auto_dependencies: {upload_step.auto_dependencies}")
            
            # Each upload step should require project_token
            assert "project_token" in upload_step.requires
            
            # Each upload step should depend on create_project
            assert "create_project" in upload_step.auto_dependencies
        
        print("✅ Multiple upload steps resolved correctly")
    
    def test_dependency_resolution_consistency(self, dependency_resolver):
        """Test that dependency resolution is consistent across multiple calls"""
        print("\n🔄 Testing Dependency Resolution Consistency")
        print("=" * 50)
        
        # Create a complex workflow
        workflow_def = WorkflowDefinition(
            name="Complex Workflow",
            description="Testing consistency of dependency resolution",
            steps=[
                WorkflowStep(
                    step_id="create_project",
                    params={"project_name": "Consistency Test"}
                ),
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={"file_path": "/test/data.csv"}
                ),
                WorkflowStep(
                    step_id="list_project_files",
                    params={"recursive": True}
                ),
                WorkflowStep(
                    step_id="download_project_zip",
                    params={"include_hidden": True}
                ),
                WorkflowStep(
                    step_id="validate_project_token",
                    params={}
                )
            ]
        )
        
        # Resolve dependencies multiple times
        resolutions = []
        for i in range(5):
            print(f"Resolution {i+1}...")
            resolution = dependency_resolver.resolve_dependencies(workflow_def)
            resolutions.append(resolution)
        
        # All resolutions should be identical
        for i in range(1, len(resolutions)):
            assert resolutions[i].execution_order == resolutions[0].execution_order
            assert resolutions[i].dependencies == resolutions[0].dependencies
            assert resolutions[i].dependents == resolutions[0].dependents
            assert resolutions[i].cycles == resolutions[0].cycles
            assert resolutions[i].missing_dependencies == resolutions[0].missing_dependencies
            assert resolutions[i].context_flow == resolutions[0].context_flow
        
        print("✅ Dependency resolution is consistent across multiple calls")
    
    def test_step_definition_validation(self, step_loader):
        """Test that step definitions are properly loaded and validated"""
        print("\n📋 Testing Step Definitions")
        print("=" * 30)
        
        # Load step definitions
        step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
        
        # Check that all expected steps are loaded
        expected_steps = [
            "create_project",
            "upload_file_to_project", 
            "download_project_zip",
            "validate_project_token",
            "list_project_files"
        ]
        
        for step_id in expected_steps:
            assert step_id in step_definitions, f"Step {step_id} not found in definitions"
            definition = step_definitions[step_id]
            
            print(f"\n📦 {step_id}:")
            print(f"  Name: {definition.name}")
            print(f"  Inputs: {len(definition.io.inputs)}")
            print(f"  Outputs: {len(definition.io.outputs)}")
            print(f"  Context keys: {definition.io.context_keys}")
            
            # Verify that context keys match outputs
            output_names = [output.name for output in definition.io.outputs]
            for context_key in definition.io.context_keys:
                assert context_key in output_names, f"Context key {context_key} not found in outputs for {step_id}"
        
        print("✅ All step definitions are valid")
    
    def test_workflow_with_circular_dependencies(self, dependency_resolver):
        """Test that circular dependencies are detected"""
        print("\n🔄 Testing Circular Dependency Detection")
        print("=" * 45)
        
        # Create a workflow with a circular dependency
        workflow_def = WorkflowDefinition(
            name="Circular Test",
            description="Testing circular dependency detection",
            steps=[
                WorkflowStep(
                    step_id="create_project",
                    params={"project_name": "Circular Test"},
                    depends_on=["upload_file_to_project"]  # Circular: create_project -> upload -> create_project
                ),
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={"file_path": "/test/file.txt"}
                    # This will auto-depend on create_project, creating a cycle
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow_def)
        
        print(f"Cycles detected: {resolution.cycles}")
        
        # Should detect the circular dependency
        assert len(resolution.cycles) > 0, "Circular dependency not detected"
        
        print("✅ Circular dependency correctly detected")
    
    def test_workflow_with_missing_dependencies(self, dependency_resolver):
        """Test that missing dependencies are detected"""
        print("\n❌ Testing Missing Dependency Detection")
        print("=" * 45)
        
        # Create a workflow with a missing dependency
        workflow_def = WorkflowDefinition(
            name="Missing Dep Test",
            description="Testing missing dependency detection",
            steps=[
                WorkflowStep(
                    step_id="upload_file_to_project",
                    params={"file_path": "/test/file.txt"}
                    # This requires project_token but no step provides it
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow_def)
        
        print(f"Missing dependencies: {resolution.missing_dependencies}")
        
        # Should detect the missing dependency
        assert len(resolution.missing_dependencies) > 0, "Missing dependency not detected"
        assert any("project_token" in msg for msg in resolution.missing_dependencies), "Missing project_token dependency not detected"
        
        print("✅ Missing dependency correctly detected")


def run_dependency_tests():
    """Run all dependency resolution tests"""
    print("🧪 Running Dependency Resolution Tests")
    print("=" * 50)
    
    # Create test instances
    step_loader = StepLoader()
    step_definitions, _ = step_loader.load_from_path("bundled_steps/project")
    dependency_resolver = DependencyResolver(step_definitions)
    
    # Run tests
    test_instance = TestDependencyResolution()
    
    test_instance.test_step_definition_validation(step_loader)
    test_instance.test_dependency_resolution_no_duplicates(dependency_resolver)
    test_instance.test_multiple_upload_steps(dependency_resolver)
    test_instance.test_dependency_resolution_consistency(dependency_resolver)
    test_instance.test_workflow_with_circular_dependencies(dependency_resolver)
    test_instance.test_workflow_with_missing_dependencies(dependency_resolver)
    
    print("\n🎉 All dependency resolution tests passed!")


if __name__ == "__main__":
    run_dependency_tests() 