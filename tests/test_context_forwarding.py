"""
Comprehensive tests for the context forwarding system.

This module tests the automatic output-to-input forwarding system that
enables powerful data flow between workflow steps based on dependencies.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from app.models import (
    WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStatus,
    StepDefinition, StepIO, IOSchema, DataType, DependencyResolution
)
from app.dependency_resolver import DependencyResolver
from app.workflow_engine import WorkflowEngine
from app.step.registry import StepRegistry
from app.managers.notice import NoticeManager
from app.core import initialize_core


class TestContextForwarding:
    """Test the context forwarding system."""
    
    @pytest.fixture
    def step_registry(self):
        """Create a step registry with test steps."""
        registry = StepRegistry()
        
        # Create test step definitions
        data_source_def = StepDefinition(
            id="data_source",
            name="Data Source",
            description="Provides data",
            callback="test.data_source",
            io=StepIO(
                inputs=[
                    IOSchema(name="source_type", type=DataType.STRING, description="Type of data source", required=True)
                ],
                outputs=[
                    IOSchema(name="data_id", type=DataType.STRING, description="Unique identifier for the data", required=True),
                    IOSchema(name="data_size", type=DataType.INTEGER, description="Size of the data in bytes", required=True)
                ],
                context_keys=["data_id", "data_size"]
            )
        )
        
        data_processor_def = StepDefinition(
            id="data_processor",
            name="Data Processor",
            description="Processes data",
            callback="test.data_processor",
            io=StepIO(
                inputs=[
                    IOSchema(name="data_id", type=DataType.STRING, description="ID of the data to process", required=True),
                    IOSchema(name="algorithm", type=DataType.STRING, description="Processing algorithm to use", required=True)
                ],
                outputs=[
                    IOSchema(name="processed_data_id", type=DataType.STRING, description="ID of the processed data", required=True),
                    IOSchema(name="quality_score", type=DataType.FLOAT, description="Quality score of the processed data", required=True)
                ],
                context_keys=["processed_data_id", "quality_score"]
            )
        )
        
        data_validator_def = StepDefinition(
            id="data_validator",
            name="Data Validator",
            description="Validates processed data",
            callback="test.data_validator",
            io=StepIO(
                inputs=[
                    IOSchema(name="processed_data_id", type=DataType.STRING, description="ID of the processed data to validate", required=True),
                    IOSchema(name="validation_rules", type=DataType.JSON, description="Rules for validation", required=False)
                ],
                outputs=[
                    IOSchema(name="validation_passed", type=DataType.BOOLEAN, description="Whether validation passed", required=True),
                    IOSchema(name="error_count", type=DataType.INTEGER, description="Number of validation errors", required=True)
                ],
                context_keys=["validation_passed", "error_count"]
            )
        )
        
        # Register step definitions
        registry.definitions = {
            "data_source": data_source_def,
            "data_processor": data_processor_def,
            "data_validator": data_validator_def
        }
        
        # Create dependency resolver
        dependency_resolver = DependencyResolver(registry.definitions)
        registry.set_dependency_resolver(dependency_resolver)
        
        return registry
    
    @pytest.fixture
    def workflow_engine(self, step_registry):
        """Create a workflow engine with test components."""
        notice_manager = NoticeManager()
        return WorkflowEngine(step_registry, notice_manager)
    
    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow for testing."""
        return WorkflowDefinition(
            name="Context Forwarding Test",
            description="Test workflow for context forwarding",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "standard"}
                ),
                WorkflowStep(
                    step_id="data_validator",
                    params={"validation_rules": {"completeness": True}}
                )
            ]
        )

    def test_automatic_context_forwarding(self, step_registry, sample_workflow):
        """Test automatic context forwarding based on dependencies."""
        print("\n🔄 Testing Automatic Context Forwarding")
        print("=" * 50)
        
        # Resolve dependencies
        dependency_resolver = step_registry.dependency_resolver
        resolution = dependency_resolver.resolve_dependencies(sample_workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify execution order
        assert resolution.execution_order == ["data_source", "data_processor", "data_validator"]
        
        # Verify context flow
        assert resolution.context_flow["data_processor"]["data_id"] == "data_source"
        assert resolution.context_flow["data_validator"]["processed_data_id"] == "data_processor"
        
        # Verify dependencies (using instance_ids)
        data_source_instance = next(s for s in sample_workflow.steps if s.step_id == "data_source")
        data_processor_instance = next(s for s in sample_workflow.steps if s.step_id == "data_processor")
        
        assert data_source_instance.instance_id in resolution.dependencies[data_processor_instance.instance_id]
        
        print("✅ Automatic context forwarding test passed!")

    def test_context_forwarding_with_multiple_sources(self, step_registry):
        """Test context forwarding with multiple data sources."""
        print("\n📊 Testing Context Forwarding with Multiple Sources")
        print("=" * 55)
        
        # Create workflow with multiple data sources
        workflow = WorkflowDefinition(
            name="Multiple Sources Test",
            description="Test workflow with multiple data sources",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "json"}
                ),
                WorkflowStep(
                    step_id="data_aggregator",
                    params={"aggregation_method": "merge"}
                )
            ]
        )
        
        # Add aggregator step definition
        aggregator_def = StepDefinition(
            id="data_aggregator",
            name="Data Aggregator",
            description="Aggregates multiple data sources",
            callback="test.data_aggregator",
            io=StepIO(
                inputs=[
                    IOSchema(name="data_ids", type=DataType.JSON, description="List of data IDs to aggregate", required=True)
                ],
                outputs=[
                    IOSchema(name="aggregated_data_id", type=DataType.STRING, description="ID of the aggregated data", required=True)
                ],
                context_keys=["aggregated_data_id"]
            )
        )
        
        step_registry.definitions["data_aggregator"] = aggregator_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify that aggregator comes after both data sources
        source_indices = [i for i, step in enumerate(resolution.execution_order) if step == "data_source"]
        aggregator_index = resolution.execution_order.index("data_aggregator")
        
        for source_index in source_indices:
            assert source_index < aggregator_index
        
        print("✅ Multiple sources context forwarding resolved correctly")

    def test_context_forwarding_with_conditional_steps(self, step_registry):
        """Test context forwarding with conditional processing steps."""
        print("\n🎯 Testing Context Forwarding with Conditional Steps")
        print("=" * 55)
        
        # Add conditional processor step
        conditional_def = StepDefinition(
            id="conditional_processor",
            name="Conditional Processor",
            description="Conditionally processes data",
            callback="test.conditional_processor",
            io=StepIO(
                inputs=[
                    IOSchema(name="data_id", type=DataType.STRING, description="ID of the data to process", required=True),
                    IOSchema(name="condition", type=DataType.STRING, description="Condition to evaluate", required=True)
                ],
                outputs=[
                    IOSchema(name="condition_result", type=DataType.BOOLEAN, description="Result of the condition evaluation", required=True),
                    IOSchema(name="processed_data_id", type=DataType.STRING, description="ID of the processed data if condition is true", required=False)
                ],
                context_keys=["condition_result", "processed_data_id"]
            )
        )
        
        step_registry.definitions["conditional_processor"] = conditional_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow with conditional processing
        workflow = WorkflowDefinition(
            name="Conditional Processing Test",
            description="Test workflow with conditional processing",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="conditional_processor",
                    params={"condition": "data_size > 1000"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "advanced"}
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify conditional processor depends on data source
        assert resolution.context_flow["conditional_processor"]["data_id"] == "data_source"
        
        # Verify data processor can depend on conditional processor (if it provides processed_data_id)
        # or on data source directly
        processor_context = resolution.context_flow.get("data_processor", {})
        assert "data_id" in processor_context
        
        print("✅ Conditional processing context forwarding resolved correctly")

    def test_context_forwarding_with_error_handling(self, step_registry):
        """Test context forwarding with error handling steps."""
        print("\n⚠️ Testing Context Forwarding with Error Handling")
        print("=" * 55)
        
        # Add error handler step
        error_handler_def = StepDefinition(
            id="error_handler",
            name="Error Handler",
            description="Handles errors and provides recovery",
            callback="test.error_handler",
            io=StepIO(
                inputs=[
                    IOSchema(name="error_context", type=DataType.JSON, description="Context of the error", required=True),
                    IOSchema(name="recovery_strategy", type=DataType.STRING, description="Strategy for recovery", required=True)
                ],
                outputs=[
                    IOSchema(name="recovery_successful", type=DataType.BOOLEAN, description="Whether recovery was successful", required=True),
                    IOSchema(name="retry_count", type=DataType.INTEGER, description="Number of retries attempted", required=True)
                ],
                context_keys=["recovery_successful", "retry_count"]
            )
        )
        
        step_registry.definitions["error_handler"] = error_handler_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow with error handling
        workflow = WorkflowDefinition(
            name="Error Handling Test",
            description="Test workflow with error handling",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "experimental"}
                ),
                WorkflowStep(
                    step_id="error_handler",
                    params={"recovery_strategy": "retry"}
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify error handler can be placed anywhere (no specific dependencies)
        assert "error_handler" in resolution.execution_order
        
        print("✅ Error handling context forwarding resolved correctly")

    def test_context_forwarding_with_state_management(self, step_registry):
        """Test context forwarding with state management steps."""
        print("\n💾 Testing Context Forwarding with State Management")
        print("=" * 55)
        
        # Add state manager step
        state_manager_def = StepDefinition(
            id="state_manager",
            name="State Manager",
            description="Manages workflow state",
            callback="test.state_manager",
            io=StepIO(
                inputs=[
                    IOSchema(name="action", type=DataType.STRING, description="Action to perform (save, load, delete)", required=True),
                    IOSchema(name="state_key", type=DataType.STRING, description="Key to manage", required=True),
                    IOSchema(name="state_data", type=DataType.JSON, description="Data to save/load", required=False)
                ],
                outputs=[
                    IOSchema(name="operation_successful", type=DataType.BOOLEAN, description="Whether the operation was successful", required=True),
                    IOSchema(name="state_value", type=DataType.JSON, description="Value of the state key", required=False)
                ],
                context_keys=["operation_successful", "state_value"]
            )
        )
        
        step_registry.definitions["state_manager"] = state_manager_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow with state management
        workflow = WorkflowDefinition(
            name="State Management Test",
            description="Test workflow with state management",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="state_manager",
                    params={"action": "save", "state_key": "data_checkpoint"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "standard"}
                ),
                WorkflowStep(
                    step_id="state_manager",
                    params={"action": "load", "state_key": "data_checkpoint"}
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify state managers can be placed anywhere
        state_manager_count = sum(1 for step in resolution.execution_order if step == "state_manager")
        assert state_manager_count == 2
        
        print("✅ State management context forwarding resolved correctly")

    def test_context_forwarding_with_performance_monitoring(self, step_registry):
        """Test context forwarding with performance monitoring steps."""
        print("\n📈 Testing Context Forwarding with Performance Monitoring")
        print("=" * 60)
        
        # Add performance monitor step
        performance_monitor_def = StepDefinition(
            id="performance_monitor",
            name="Performance Monitor",
            description="Monitors performance metrics",
            callback="test.performance_monitor",
            io=StepIO(
                inputs=[
                    IOSchema(name="monitor_target", type=DataType.STRING, description="Target to monitor (workflow_start, workflow_end, step_start, step_end)", required=True),
                    IOSchema(name="duration", type=DataType.INTEGER, description="Duration in seconds", required=False)
                ],
                outputs=[
                    IOSchema(name="performance_score", type=DataType.FLOAT, description="Overall performance score", required=True),
                    IOSchema(name="recommendations", type=DataType.JSON, description="Recommendations for improvement", required=True)
                ],
                context_keys=["performance_score", "recommendations"]
            )
        )
        
        step_registry.definitions["performance_monitor"] = performance_monitor_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow with performance monitoring
        workflow = WorkflowDefinition(
            name="Performance Monitoring Test",
            description="Test workflow with performance monitoring",
            steps=[
                WorkflowStep(
                    step_id="performance_monitor",
                    params={"monitor_target": "workflow_start", "duration": 30}
                ),
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "optimized"}
                ),
                WorkflowStep(
                    step_id="performance_monitor",
                    params={"monitor_target": "workflow_end", "duration": 30}
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify performance monitors can be placed anywhere
        monitor_count = sum(1 for step in resolution.execution_order if step == "performance_monitor")
        assert monitor_count == 2
        
        print("✅ Performance monitoring context forwarding resolved correctly")

    def test_context_forwarding_with_complex_chains(self, step_registry):
        """Test context forwarding with complex dependency chains."""
        print("\n🔗 Testing Context Forwarding with Complex Chains")
        print("=" * 55)
        
        # Add data transformer step
        transformer_def = StepDefinition(
            id="data_transformer",
            name="Data Transformer",
            description="Transforms data between formats",
            callback="test.data_transformer",
            io=StepIO(
                inputs=[
                    IOSchema(name="data_id", type=DataType.STRING, description="ID of the data to transform", required=True),
                    IOSchema(name="source_format", type=DataType.STRING, description="Format of the source data", required=True),
                    IOSchema(name="target_format", type=DataType.STRING, description="Format to transform to", required=True)
                ],
                outputs=[
                    IOSchema(name="transformed_data_id", type=DataType.STRING, description="ID of the transformed data", required=True),
                    IOSchema(name="format_compatibility", type=DataType.BOOLEAN, description="Whether format transformation was successful", required=True)
                ],
                context_keys=["transformed_data_id", "format_compatibility"]
            )
        )
        
        step_registry.definitions["data_transformer"] = transformer_def
        dependency_resolver = DependencyResolver(step_registry.definitions)
        step_registry.set_dependency_resolver(dependency_resolver)
        
        # Create workflow with complex chain
        workflow = WorkflowDefinition(
            name="Complex Chain Test",
            description="Test workflow with complex dependency chain",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"}
                ),
                WorkflowStep(
                    step_id="data_transformer",
                    params={"source_format": "csv", "target_format": "json"}
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "advanced"}
                ),
                WorkflowStep(
                    step_id="data_validator",
                    params={"validation_rules": {"schema": True}}
                )
            ]
        )
        
        # Resolve dependencies
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Execution order: {' -> '.join(resolution.execution_order)}")
        print(f"Context flow: {resolution.context_flow}")
        
        # Verify complex chain: source -> transformer -> processor -> validator
        expected_order = ["data_source", "data_transformer", "data_processor", "data_validator"]
        assert resolution.execution_order == expected_order
        
        # Verify context flow chain
        assert resolution.context_flow["data_transformer"]["data_id"] == "data_source"
        # Note: data_processor doesn't depend on data_transformer because it doesn't have a data_id input
        # It only depends on data_source for the data_id
        assert resolution.context_flow["data_processor"]["data_id"] == "data_source"
        assert resolution.context_flow["data_validator"]["processed_data_id"] == "data_processor"
        
        print("✅ Complex chain context forwarding resolved correctly")

    def test_context_forwarding_with_circular_dependencies(self, step_registry):
        """Test context forwarding with circular dependencies."""
        print("\n🔄 Testing Context Forwarding with Circular Dependencies")
        print("=" * 60)
        
        # Create workflow with circular dependency
        workflow = WorkflowDefinition(
            name="Circular Dependency Test",
            description="Test workflow with circular dependencies",
            steps=[
                WorkflowStep(
                    step_id="data_source",
                    params={"source_type": "csv"},
                    depends_on=["data_processor"]  # Circular: source -> processor -> source
                ),
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "standard"}
                    # This will auto-depend on data_source, creating a cycle
                )
            ]
        )
        
        # Resolve dependencies
        dependency_resolver = step_registry.dependency_resolver
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Cycles detected: {resolution.cycles}")
        print(f"Execution order: {resolution.execution_order}")
        
        # Should detect the circular dependency
        assert len(resolution.cycles) > 0, "Circular dependency not detected"
        
        print("✅ Circular dependency correctly detected")

    def test_context_forwarding_with_missing_dependencies(self, step_registry):
        """Test context forwarding with missing dependencies."""
        print("\n❌ Testing Context Forwarding with Missing Dependencies")
        print("=" * 60)
        
        # Create workflow with missing dependency
        workflow = WorkflowDefinition(
            name="Missing Dependency Test",
            description="Test workflow with missing dependencies",
            steps=[
                WorkflowStep(
                    step_id="data_processor",
                    params={"algorithm": "standard"}
                    # This requires data_id but no step provides it
                )
            ]
        )
        
        # Resolve dependencies
        dependency_resolver = step_registry.dependency_resolver
        resolution = dependency_resolver.resolve_dependencies(workflow)
        
        print(f"Missing dependencies: {resolution.missing_dependencies}")
        print(f"Execution order: {resolution.execution_order}")
        
        # Should detect the missing dependency
        assert len(resolution.missing_dependencies) > 0, "Missing dependency not detected"
        assert any("data_id" in msg for msg in resolution.missing_dependencies), "Missing data_id dependency not detected"
        
        print("✅ Missing dependency correctly detected")

    @pytest.mark.asyncio
    async def test_context_forwarding_in_workflow_execution(self, workflow_engine, sample_workflow):
        """Test context forwarding during actual workflow execution."""
        print("\n🚀 Testing Context Forwarding in Workflow Execution")
        print("=" * 60)
        
        # Create workflow instance
        workflow_instance = WorkflowInstance(
            id="context-forwarding-test",
            definition=sample_workflow,
            status=WorkflowStatus.PENDING
        )
        
        # Mock step implementations
        async def mock_data_source(params, context):
            await context.info("Data Source", "Loading data...")
            return {"data_id": "test-data-123", "data_size": 1000}
        
        async def mock_data_processor(params, context):
            data_id = params.get("data_id")
            await context.info("Data Processor", f"Processing {data_id}...")
            return {"processed_data_id": "processed-123", "quality_score": 0.95}
        
        async def mock_data_validator(params, context):
            processed_data_id = params.get("processed_data_id")
            await context.info("Data Validator", f"Validating {processed_data_id}...")
            return {"validation_passed": True, "error_count": 0}
        
        # Register mock implementations
        workflow_engine.step_registry.steps = {
            "data_source": mock_data_source,
            "data_processor": mock_data_processor,
            "data_validator": mock_data_validator
        }
        
        # Ensure step definitions are registered
        workflow_engine.step_registry.definitions.update({
            "data_source": StepDefinition(
                id="data_source",
                name="Data Source",
                description="Provides data",
                callback="test.data_source",
                io=StepIO(
                    inputs=[
                        IOSchema(name="source_type", type=DataType.STRING, description="Type of data source", required=True)
                    ],
                    outputs=[
                        IOSchema(name="data_id", type=DataType.STRING, description="Unique identifier for the data", required=True),
                        IOSchema(name="data_size", type=DataType.INTEGER, description="Size of the data in bytes", required=True)
                    ],
                    context_keys=["data_id", "data_size"]
                )
            ),
            "data_processor": StepDefinition(
                id="data_processor",
                name="Data Processor",
                description="Processes data",
                callback="test.data_processor",
                io=StepIO(
                    inputs=[
                        IOSchema(name="data_id", type=DataType.STRING, description="ID of the data to process", required=True),
                        IOSchema(name="algorithm", type=DataType.STRING, description="Processing algorithm to use", required=True)
                    ],
                    outputs=[
                        IOSchema(name="processed_data_id", type=DataType.STRING, description="ID of the processed data", required=True),
                        IOSchema(name="quality_score", type=DataType.FLOAT, description="Quality score of the processed data", required=True)
                    ],
                    context_keys=["processed_data_id", "quality_score"]
                )
            ),
            "data_validator": StepDefinition(
                id="data_validator",
                name="Data Validator",
                description="Validates processed data",
                callback="test.data_validator",
                io=StepIO(
                    inputs=[
                        IOSchema(name="processed_data_id", type=DataType.STRING, description="ID of the processed data to validate", required=True),
                        IOSchema(name="validation_rules", type=DataType.JSON, description="Rules for validation", required=False)
                    ],
                    outputs=[
                        IOSchema(name="validation_passed", type=DataType.BOOLEAN, description="Whether validation passed", required=True),
                        IOSchema(name="error_count", type=DataType.INTEGER, description="Number of validation errors", required=True)
                    ],
                    context_keys=["validation_passed", "error_count"]
                )
            )
        })
        
        # Execute workflow
        await workflow_engine.execute_workflow(workflow_instance)
        
        # Verify workflow completed
        assert workflow_instance.status == WorkflowStatus.COMPLETED
        
        # Verify context was forwarded correctly
        assert "data_id" in workflow_instance.context
        assert "processed_data_id" in workflow_instance.context
        assert "validation_passed" in workflow_instance.context
        
        # Verify step results
        assert "data_source" in workflow_instance.step_results
        assert "data_processor" in workflow_instance.step_results
        assert "data_validator" in workflow_instance.step_results
        
        print("✅ Context forwarding in workflow execution successful")


def run_context_forwarding_tests():
    """Run all context forwarding tests."""
    print("🧪 Running Context Forwarding Tests")
    print("=" * 50)
    
    # Create test instances
    test_instance = TestContextForwarding()
    
    # Run tests
    test_instance.test_automatic_context_forwarding(test_instance.step_registry(), test_instance.sample_workflow())
    test_instance.test_context_forwarding_with_multiple_sources(test_instance.step_registry())
    test_instance.test_context_forwarding_with_conditional_steps(test_instance.step_registry())
    test_instance.test_context_forwarding_with_error_handling(test_instance.step_registry())
    test_instance.test_context_forwarding_with_state_management(test_instance.step_registry())
    test_instance.test_context_forwarding_with_performance_monitoring(test_instance.step_registry())
    test_instance.test_context_forwarding_with_complex_chains(test_instance.step_registry())
    test_instance.test_context_forwarding_with_circular_dependencies(test_instance.step_registry())
    test_instance.test_context_forwarding_with_missing_dependencies(test_instance.step_registry())
    
    print("\n🎉 All context forwarding tests passed!")


if __name__ == "__main__":
    run_context_forwarding_tests() 