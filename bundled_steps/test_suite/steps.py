import asyncio
import uuid
import time
import random
import json
from typing import Dict, Any, List
from datetime import datetime, UTC

from app.core import StepContext


async def data_source(params: Dict[str, Any], context: StepContext):
    """Simulates a data source that provides initial data"""
    source_type = params.get('source_type', 'csv')
    file_path = params.get('file_path', '/default/data.csv')
    
    await context.info("Data Source", f"Loading data from {source_type} source: {file_path}")
    
    # Simulate data loading
    await asyncio.sleep(0.1)
    
    # Generate mock data
    data_id = str(uuid.uuid4())
    data_size = random.randint(1000, 10000)
    record_count = random.randint(100, 1000)
    
    await context.success("Data Loaded", f"Successfully loaded {record_count} records ({data_size} bytes)")
    
    return {
        'data_id': data_id,
        'data_size': data_size,
        'record_count': record_count
    }


async def data_processor(params: Dict[str, Any], context: StepContext):
    """Processes data with various algorithms"""
    data_id = params.get('data_id')
    algorithm = params.get('algorithm', 'standard')
    parameters = params.get('parameters', {})
    
    await context.info("Data Processing", f"Processing data {data_id} with algorithm: {algorithm}")
    
    # Simulate processing time
    processing_time = random.uniform(0.5, 2.0)
    await asyncio.sleep(processing_time)
    
    # Generate processed data
    processed_data_id = str(uuid.uuid4())
    quality_score = random.uniform(0.7, 1.0)
    
    await context.success("Processing Complete", f"Data processed in {processing_time:.2f}s with quality score: {quality_score:.2f}")
    
    return {
        'processed_data_id': processed_data_id,
        'processing_time': processing_time,
        'quality_score': quality_score
    }


async def data_validator(params: Dict[str, Any], context: StepContext):
    """Validates data quality and structure"""
    processed_data_id = params.get('processed_data_id')
    validation_rules = params.get('validation_rules', {})
    
    await context.info("Data Validation", f"Validating processed data {processed_data_id}")
    
    # Simulate validation
    await asyncio.sleep(0.2)
    
    # Random validation result
    validation_passed = random.choice([True, True, True, False])  # 75% success rate
    error_count = random.randint(0, 5) if not validation_passed else 0
    
    validation_report = {
        'timestamp': datetime.now(UTC).isoformat(),
        'processed_data_id': processed_data_id,
        'rules_applied': list(validation_rules.keys()) if validation_rules else ['default'],
        'errors': [f"Error {i+1}" for i in range(error_count)] if error_count > 0 else []
    }
    
    if validation_passed:
        await context.success("Validation Passed", f"Data validation successful with {error_count} errors")
    else:
        await context.error("Validation Failed", f"Data validation failed with {error_count} errors")
    
    return {
        'validation_passed': validation_passed,
        'error_count': error_count,
        'validation_report': validation_report
    }


async def parallel_processor(params: Dict[str, Any], context: StepContext):
    """Processes multiple data streams in parallel"""
    data_ids = params.get('data_ids', [])
    worker_count = params.get('worker_count', 4)
    
    await context.info("Parallel Processing", f"Processing {len(data_ids)} data streams with {worker_count} workers")
    
    # Simulate parallel processing
    start_time = time.time()
    
    # Create tasks for parallel processing
    async def process_single_data(data_id: str) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return {
            'data_id': data_id,
            'processed': True,
            'result': f"processed_{data_id[:8]}"
        }
    
    # Execute in parallel
    tasks = [process_single_data(data_id) for data_id in data_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    
    parallel_results = {
        'results': results,
        'worker_count': worker_count,
        'data_count': len(data_ids)
    }
    
    await context.success("Parallel Processing Complete", 
                         f"Processed {success_count}/{len(data_ids)} data streams in {total_time:.2f}s")
    
    return {
        'parallel_results': parallel_results,
        'total_processing_time': total_time,
        'success_count': success_count
    }


async def conditional_processor(params: Dict[str, Any], context: StepContext):
    """Processes data based on conditions"""
    data_id = params.get('data_id')
    condition = params.get('condition', 'default')
    true_action = params.get('true_action', 'process')
    false_action = params.get('false_action', 'skip')
    
    await context.info("Conditional Processing", f"Evaluating condition: {condition}")
    
    # Simulate condition evaluation
    await asyncio.sleep(0.1)
    
    # Random condition result
    condition_result = random.choice([True, False])
    action_taken = true_action if condition_result else false_action
    
    await context.info("Condition Result", f"Condition '{condition}' evaluated to {condition_result}")
    
    processed_data_id = None
    if condition_result and action_taken == 'process':
        processed_data_id = str(uuid.uuid4())
        await context.success("Action Taken", f"Executed action: {action_taken}")
    else:
        await context.info("Action Taken", f"Executed action: {action_taken}")
    
    return {
        'condition_result': condition_result,
        'action_taken': action_taken,
        'processed_data_id': processed_data_id
    }


async def error_handler(params: Dict[str, Any], context: StepContext):
    """Handles errors and provides recovery options"""
    error_context = params.get('error_context', {})
    recovery_strategy = params.get('recovery_strategy', 'retry')
    max_retries = params.get('max_retries', 3)
    
    await context.warning("Error Handler", f"Handling error with strategy: {recovery_strategy}")
    
    # Simulate error recovery
    await asyncio.sleep(0.3)
    
    # Simulate retry attempts
    retry_count = random.randint(0, max_retries)
    recovery_successful = retry_count < max_retries
    
    if recovery_successful:
        final_status = "recovered"
        await context.success("Recovery Successful", f"Error recovered after {retry_count} retries")
    else:
        final_status = "failed"
        await context.error("Recovery Failed", f"Failed to recover after {retry_count} retries")
    
    return {
        'recovery_successful': recovery_successful,
        'retry_count': retry_count,
        'final_status': final_status
    }


async def data_aggregator(params: Dict[str, Any], context: StepContext):
    """Aggregates multiple data sources into a single result"""
    data_ids = params.get('data_ids', [])
    aggregation_method = params.get('aggregation_method', 'sum')
    group_by = params.get('group_by', [])
    
    await context.info("Data Aggregation", f"Aggregating {len(data_ids)} data sources using {aggregation_method}")
    
    # Simulate aggregation
    await asyncio.sleep(0.4)
    
    aggregated_data_id = str(uuid.uuid4())
    reduction_factor = random.uniform(0.1, 0.8)
    
    aggregation_summary = {
        'method': aggregation_method,
        'input_count': len(data_ids),
        'group_by': group_by,
        'reduction_factor': reduction_factor,
        'timestamp': datetime.now(UTC).isoformat()
    }
    
    await context.success("Aggregation Complete", 
                         f"Aggregated {len(data_ids)} sources with {reduction_factor:.2f} reduction factor")
    
    return {
        'aggregated_data_id': aggregated_data_id,
        'aggregation_summary': aggregation_summary,
        'reduction_factor': reduction_factor
    }


async def state_manager(params: Dict[str, Any], context: StepContext):
    """Manages workflow state and persistence"""
    action = params.get('action', 'save')
    state_key = params.get('state_key', 'default')
    state_data = params.get('state_data', {})
    
    await context.info("State Management", f"Performing {action} operation on state key: {state_key}")
    
    # Simulate state operations
    await asyncio.sleep(0.1)
    
    operation_successful = True
    state_value = None
    state_size = 0
    
    if action == 'save':
        state_size = len(json.dumps(state_data))
        await context.success("State Saved", f"Saved state with size: {state_size} bytes")
    elif action == 'load':
        state_value = {'loaded': True, 'key': state_key, 'timestamp': datetime.now(UTC).isoformat()}
        state_size = len(json.dumps(state_value))
        await context.success("State Loaded", f"Loaded state with size: {state_size} bytes")
    elif action == 'clear':
        state_size = 0
        await context.success("State Cleared", "State cleared successfully")
    else:
        operation_successful = False
        await context.error("Invalid Action", f"Unknown action: {action}")
    
    return {
        'operation_successful': operation_successful,
        'state_value': state_value,
        'state_size': state_size
    }


async def performance_monitor(params: Dict[str, Any], context: StepContext):
    """Monitors and reports performance metrics"""
    monitor_target = params.get('monitor_target', 'workflow')
    metrics = params.get('metrics', ['cpu', 'memory', 'throughput'])
    duration = params.get('duration', 60)
    
    await context.info("Performance Monitoring", f"Monitoring {monitor_target} for {duration}s")
    
    # Simulate monitoring
    await asyncio.sleep(0.2)
    
    # Generate mock performance data
    performance_score = random.uniform(0.6, 1.0)
    
    monitoring_report = {
        'target': monitor_target,
        'duration': duration,
        'metrics': metrics,
        'cpu_usage': random.uniform(20, 80),
        'memory_usage': random.uniform(30, 90),
        'throughput': random.uniform(100, 1000),
        'timestamp': datetime.now(UTC).isoformat()
    }
    
    recommendations = []
    if performance_score < 0.8:
        recommendations.append("Consider optimizing resource allocation")
    if monitoring_report['cpu_usage'] > 70:
        recommendations.append("High CPU usage detected - consider scaling")
    if monitoring_report['memory_usage'] > 80:
        recommendations.append("High memory usage detected - consider cleanup")
    
    await context.success("Monitoring Complete", f"Performance score: {performance_score:.2f}")
    
    return {
        'monitoring_report': monitoring_report,
        'performance_score': performance_score,
        'recommendations': recommendations
    }


async def data_transformer(params: Dict[str, Any], context: StepContext):
    """Transforms data between different formats"""
    data_id = params.get('data_id')
    source_format = params.get('source_format', 'csv')
    target_format = params.get('target_format', 'json')
    transformation_rules = params.get('transformation_rules', {})
    
    await context.info("Data Transformation", f"Transforming {data_id} from {source_format} to {target_format}")
    
    # Simulate transformation
    await asyncio.sleep(0.3)
    
    # Check format compatibility
    format_compatibility = True
    if source_format == 'binary' and target_format == 'text':
        format_compatibility = False
    
    transformed_data_id = str(uuid.uuid4()) if format_compatibility else None
    
    transformation_metadata = {
        'source_format': source_format,
        'target_format': target_format,
        'rules_applied': list(transformation_rules.keys()) if transformation_rules else ['default'],
        'compatibility': format_compatibility,
        'timestamp': datetime.now(UTC).isoformat()
    }
    
    if format_compatibility:
        await context.success("Transformation Complete", f"Successfully transformed to {target_format}")
    else:
        await context.error("Transformation Failed", f"Incompatible formats: {source_format} -> {target_format}")
    
    return {
        'transformed_data_id': transformed_data_id,
        'transformation_metadata': transformation_metadata,
        'format_compatibility': format_compatibility
    }


async def workflow_orchestrator(params: Dict[str, Any], context: StepContext):
    """Orchestrates sub-workflows and manages their execution"""
    sub_workflows = params.get('sub_workflows', [])
    execution_strategy = params.get('execution_strategy', 'sequential')
    failure_handling = params.get('failure_handling', 'stop_on_first')
    
    await context.info("Workflow Orchestration", 
                      f"Orchestrating {len(sub_workflows)} sub-workflows with strategy: {execution_strategy}")
    
    # Simulate orchestration
    start_time = time.time()
    
    sub_workflow_results = []
    for i, workflow in enumerate(sub_workflows):
        await context.info("Sub-workflow", f"Executing sub-workflow {i+1}/{len(sub_workflows)}")
        await asyncio.sleep(0.2)
        
        # Simulate sub-workflow execution
        success = random.choice([True, True, True, False])  # 75% success rate
        result = {
            'workflow_id': workflow.get('id', f'sub_{i}'),
            'status': 'completed' if success else 'failed',
            'execution_time': random.uniform(0.5, 2.0),
            'result': f"result_{i}" if success else None
        }
        
        sub_workflow_results.append(result)
        
        if not success and failure_handling == 'stop_on_first':
            await context.error("Orchestration Failed", f"Sub-workflow {i+1} failed, stopping execution")
            break
    
    total_time = time.time() - start_time
    
    # Determine overall status
    successful_workflows = sum(1 for r in sub_workflow_results if r['status'] == 'completed')
    if successful_workflows == len(sub_workflows):
        orchestration_status = "completed"
        await context.success("Orchestration Complete", f"All {len(sub_workflows)} sub-workflows completed successfully")
    elif successful_workflows > 0:
        orchestration_status = "partial"
        await context.warning("Orchestration Partial", f"{successful_workflows}/{len(sub_workflows)} sub-workflows completed")
    else:
        orchestration_status = "failed"
        await context.error("Orchestration Failed", "All sub-workflows failed")
    
    return {
        'orchestration_status': orchestration_status,
        'sub_workflow_results': sub_workflow_results,
        'total_execution_time': total_time
    } 