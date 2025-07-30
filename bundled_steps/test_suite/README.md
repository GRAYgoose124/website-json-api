# Test Suite Steps

This module provides a comprehensive set of test steps designed to rigorously test the workflow system for correctness, flexibility, and robustness. These steps cover various scenarios and edge cases that real-world workflows might encounter.

## Overview

The test suite includes 12 different step types that test various aspects of the workflow system:

1. **Data Flow Steps** - Basic data processing pipeline
2. **Parallel Processing Steps** - Concurrent execution scenarios
3. **Conditional Steps** - Branching and decision logic
4. **Error Handling Steps** - Recovery and resilience testing
5. **Aggregation Steps** - Data reduction and summarization
6. **State Management Steps** - Persistence and checkpointing
7. **Performance Monitoring Steps** - Metrics and optimization
8. **Transformation Steps** - Format conversion and data manipulation
9. **Orchestration Steps** - Sub-workflow management

## Step Categories

### 🔧 Data Flow Steps

#### `data_source`
- **Purpose**: Simulates data sources that provide initial data
- **Tests**: Basic data input, context key generation, parameter handling
- **Inputs**: `source_type`, `file_path`
- **Outputs**: `data_id`, `data_size`, `record_count`
- **Context Keys**: `data_id`, `data_size`, `record_count`

#### `data_processor`
- **Purpose**: Processes data with various algorithms
- **Tests**: Data transformation, context consumption, processing time simulation
- **Inputs**: `data_id`, `algorithm`, `parameters`
- **Outputs**: `processed_data_id`, `processing_time`, `quality_score`
- **Context Keys**: `processed_data_id`, `processing_time`, `quality_score`

#### `data_validator`
- **Purpose**: Validates data quality and structure
- **Tests**: Validation logic, error reporting, conditional success/failure
- **Inputs**: `data_id`, `validation_rules`
- **Outputs**: `validation_passed`, `error_count`, `validation_report`
- **Context Keys**: `validation_passed`, `error_count`, `validation_report`

### 🔄 Parallel Processing Steps

#### `parallel_processor`
- **Purpose**: Processes multiple data streams in parallel
- **Tests**: Concurrent execution, task coordination, result aggregation
- **Inputs**: `data_ids`, `worker_count`
- **Outputs**: `parallel_results`, `total_processing_time`, `success_count`
- **Context Keys**: `parallel_results`, `total_processing_time`, `success_count`

### 🎯 Conditional and Branching Steps

#### `conditional_processor`
- **Purpose**: Processes data based on conditions
- **Tests**: Conditional logic, branching, dynamic behavior
- **Inputs**: `data_id`, `condition`, `true_action`, `false_action`
- **Outputs**: `condition_result`, `action_taken`, `processed_data_id`
- **Context Keys**: `condition_result`, `action_taken`, `processed_data_id`

### ⚠️ Error Handling Steps

#### `error_handler`
- **Purpose**: Handles errors and provides recovery options
- **Tests**: Error recovery, retry logic, failure handling
- **Inputs**: `error_context`, `recovery_strategy`, `max_retries`
- **Outputs**: `recovery_successful`, `retry_count`, `final_status`
- **Context Keys**: `recovery_successful`, `retry_count`, `final_status`

### 📊 Data Aggregation Steps

#### `data_aggregator`
- **Purpose**: Aggregates multiple data sources into a single result
- **Tests**: Data reduction, multi-source processing, summary generation
- **Inputs**: `data_ids`, `aggregation_method`, `group_by`
- **Outputs**: `aggregated_data_id`, `aggregation_summary`, `reduction_factor`
- **Context Keys**: `aggregated_data_id`, `aggregation_summary`, `reduction_factor`

### 💾 State Management Steps

#### `state_manager`
- **Purpose**: Manages workflow state and persistence
- **Tests**: State persistence, checkpointing, data serialization
- **Inputs**: `action`, `state_key`, `state_data`
- **Outputs**: `operation_successful`, `state_value`, `state_size`
- **Context Keys**: `operation_successful`, `state_value`, `state_size`

### 📈 Performance Monitoring Steps

#### `performance_monitor`
- **Purpose**: Monitors and reports performance metrics
- **Tests**: Performance measurement, metric collection, optimization recommendations
- **Inputs**: `monitor_target`, `metrics`, `duration`
- **Outputs**: `monitoring_report`, `performance_score`, `recommendations`
- **Context Keys**: `monitoring_report`, `performance_score`, `recommendations`

### 🔄 Data Transformation Steps

#### `data_transformer`
- **Purpose**: Transforms data between different formats
- **Tests**: Format conversion, compatibility checking, transformation rules
- **Inputs**: `data_id`, `source_format`, `target_format`, `transformation_rules`
- **Outputs**: `transformed_data_id`, `transformation_metadata`, `format_compatibility`
- **Context Keys**: `transformed_data_id`, `transformation_metadata`, `format_compatibility`

### 🎼 Workflow Orchestration Steps

#### `workflow_orchestrator`
- **Purpose**: Orchestrates sub-workflows and manages their execution
- **Tests**: Sub-workflow management, execution strategies, failure handling
- **Inputs**: `sub_workflows`, `execution_strategy`, `failure_handling`
- **Outputs**: `orchestration_status`, `sub_workflow_results`, `total_execution_time`
- **Context Keys**: `orchestration_status`, `sub_workflow_results`, `total_execution_time`

## Testing Scenarios

### Basic Data Pipeline
```
data_source -> data_processor -> data_validator
```
Tests basic linear workflow execution and context flow.

### Parallel Processing
```
data_source (3 instances) -> parallel_processor
```
Tests multiple instances of the same step type and parallel execution.

### Conditional Processing
```
data_source -> conditional_processor -> data_processor
```
Tests branching logic and conditional dependencies.

### Error Handling
```
data_source -> data_processor -> error_handler
```
Tests error recovery and resilience mechanisms.

### Complex Aggregation
```
data_source (3 instances) -> data_processor (3 instances) -> data_aggregator
```
Tests complex dependency chains with multiple data sources and processors.

### State Management
```
data_source -> state_manager (save) -> data_processor -> state_manager (load)
```
Tests state persistence and checkpointing throughout workflow execution.

### Performance Monitoring
```
performance_monitor -> data_source -> data_processor -> performance_monitor
```
Tests performance measurement and monitoring capabilities.

### Data Transformation Chain
```
data_source -> data_transformer -> data_transformer
```
Tests sequential data transformations and format conversions.

### Workflow Orchestration
```
data_source -> workflow_orchestrator
```
Tests sub-workflow management and orchestration capabilities.

## Test Coverage

The test suite covers the following aspects of the workflow system:

### ✅ Dependency Resolution
- Linear dependencies
- Complex dependency chains
- Multiple instances of same step type
- Circular dependency detection
- Missing dependency detection

### ✅ Context Flow
- Context key generation
- Context consumption
- Context propagation
- Context validation

### ✅ Error Handling
- Step failure detection
- Error recovery mechanisms
- Retry logic
- Failure propagation

### ✅ Performance
- Execution time measurement
- Resource monitoring
- Performance optimization
- Scalability testing

### ✅ State Management
- State persistence
- Checkpointing
- State recovery
- Data serialization

### ✅ Parallel Processing
- Concurrent execution
- Task coordination
- Result aggregation
- Resource management

### ✅ Conditional Logic
- Branching decisions
- Dynamic behavior
- Conditional dependencies
- Flow control

## Usage

To use these test steps in your own tests:

```python
from app.step.loader import StepLoader
from app.dependency_resolver import DependencyResolver

# Load test suite steps
step_loader = StepLoader()
step_definitions, step_implementations = step_loader.load_from_path("bundled_steps/test_suite")

# Create dependency resolver
resolver = DependencyResolver(step_definitions)

# Create test workflows
workflow_def = WorkflowDefinition(
    name="Test Workflow",
    steps=[
        WorkflowStep(step_id="data_source", params={"source_type": "csv"}),
        WorkflowStep(step_id="data_processor", params={"algorithm": "standard"}),
        WorkflowStep(step_id="data_validator", params={})
    ]
)

# Resolve dependencies
resolution = resolver.resolve_dependencies(workflow_def)
```

## Running Tests

The test suite includes comprehensive tests in `tests/test_workflow_system.py`:

```bash
# Run all workflow system tests
uv run pytest tests/test_workflow_system.py -v

# Run specific test categories
uv run pytest tests/test_workflow_system.py::TestWorkflowSystem::test_basic_data_pipeline -v
uv run pytest tests/test_workflow_system.py::TestWorkflowSystem::test_parallel_processing_workflow -v
```

## Extending the Test Suite

To add new test steps:

1. Add step definition to `definitions.py`
2. Add step implementation to `steps.py`
3. Add corresponding tests to `tests/test_workflow_system.py`
4. Update this README with documentation

The test suite is designed to be extensible and can accommodate new step types that test additional aspects of the workflow system. 