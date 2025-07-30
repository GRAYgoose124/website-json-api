from app.models import StepDefinition, StepIO, IOSchema, DataType

# Test step definitions that cover various workflow scenarios
STEP_DEFINITIONS = {
    # Basic data flow steps
    "data_source": StepDefinition(
        id="data_source",
        name="Data Source",
        description="Simulates a data source that provides initial data",
        callback="steps.data_source",
        category="data_processing",
        tags=["data", "source", "input"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="source_type",
                    type=DataType.STRING,
                    description="Type of data source",
                    required=True,
                    default="csv"
                ),
                IOSchema(
                    name="file_path",
                    type=DataType.STRING,
                    description="Path to data file",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="data_id",
                    type=DataType.STRING,
                    description="Unique identifier for the data",
                    required=True
                ),
                IOSchema(
                    name="data_size",
                    type=DataType.INTEGER,
                    description="Size of the data in bytes",
                    required=True
                ),
                IOSchema(
                    name="record_count",
                    type=DataType.INTEGER,
                    description="Number of records in the data",
                    required=True
                )
            ],
            context_keys=["data_id", "data_size", "record_count"]
        )
    ),
    
    "data_processor": StepDefinition(
        id="data_processor",
        name="Data Processor",
        description="Processes data with various algorithms",
        callback="steps.data_processor",
        category="data_processing",
        tags=["data", "processing", "algorithm"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="data_id",
                    type=DataType.STRING,
                    description="ID of the data to process",
                    required=True
                ),
                IOSchema(
                    name="algorithm",
                    type=DataType.STRING,
                    description="Processing algorithm to use",
                    required=True,
                    default="standard"
                ),
                IOSchema(
                    name="parameters",
                    type=DataType.JSON,
                    description="Algorithm parameters",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="processed_data_id",
                    type=DataType.STRING,
                    description="ID of the processed data",
                    required=True
                ),
                IOSchema(
                    name="processing_time",
                    type=DataType.FLOAT,
                    description="Time taken for processing in seconds",
                    required=True
                ),
                IOSchema(
                    name="quality_score",
                    type=DataType.FLOAT,
                    description="Quality score of the processed data",
                    required=True
                )
            ],
            context_keys=["processed_data_id", "processing_time", "quality_score"]
        )
    ),
    
    "data_validator": StepDefinition(
        id="data_validator",
        name="Data Validator",
        description="Validates data quality and structure",
        callback="steps.data_validator",
        category="data_processing",
        tags=["data", "validation", "quality"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="processed_data_id",
                    type=DataType.STRING,
                    description="ID of the processed data to validate",
                    required=True
                ),
                IOSchema(
                    name="validation_rules",
                    type=DataType.JSON,
                    description="Validation rules to apply",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="validation_passed",
                    type=DataType.BOOLEAN,
                    description="Whether validation passed",
                    required=True
                ),
                IOSchema(
                    name="error_count",
                    type=DataType.INTEGER,
                    description="Number of validation errors",
                    required=True
                ),
                IOSchema(
                    name="validation_report",
                    type=DataType.JSON,
                    description="Detailed validation report",
                    required=True
                )
            ],
            context_keys=["validation_passed", "error_count", "validation_report"]
        )
    ),
    
    # Parallel processing steps
    "parallel_processor": StepDefinition(
        id="parallel_processor",
        name="Parallel Processor",
        description="Processes multiple data streams in parallel",
        callback="steps.parallel_processor",
        category="parallel_processing",
        tags=["parallel", "processing", "concurrent"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="data_ids",
                    type=DataType.JSON,
                    description="List of data IDs to process",
                    required=True
                ),
                IOSchema(
                    name="worker_count",
                    type=DataType.INTEGER,
                    description="Number of parallel workers",
                    required=False,
                    default=4
                )
            ],
            outputs=[
                IOSchema(
                    name="parallel_results",
                    type=DataType.JSON,
                    description="Results from parallel processing",
                    required=True
                ),
                IOSchema(
                    name="total_processing_time",
                    type=DataType.FLOAT,
                    description="Total time for all parallel operations",
                    required=True
                ),
                IOSchema(
                    name="success_count",
                    type=DataType.INTEGER,
                    description="Number of successful operations",
                    required=True
                )
            ],
            context_keys=["parallel_results", "total_processing_time", "success_count"]
        )
    ),
    
    # Conditional and branching steps
    "conditional_processor": StepDefinition(
        id="conditional_processor",
        name="Conditional Processor",
        description="Processes data based on conditions",
        callback="steps.conditional_processor",
        category="conditional_processing",
        tags=["conditional", "branching", "logic"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="data_id",
                    type=DataType.STRING,
                    description="ID of the data to process",
                    required=True
                ),
                IOSchema(
                    name="condition",
                    type=DataType.STRING,
                    description="Condition to evaluate",
                    required=True
                ),
                IOSchema(
                    name="true_action",
                    type=DataType.STRING,
                    description="Action to take if condition is true",
                    required=True
                ),
                IOSchema(
                    name="false_action",
                    type=DataType.STRING,
                    description="Action to take if condition is false",
                    required=True
                )
            ],
            outputs=[
                IOSchema(
                    name="condition_result",
                    type=DataType.BOOLEAN,
                    description="Result of the condition evaluation",
                    required=True
                ),
                IOSchema(
                    name="action_taken",
                    type=DataType.STRING,
                    description="Action that was actually taken",
                    required=True
                ),
                IOSchema(
                    name="processed_data_id",
                    type=DataType.STRING,
                    description="ID of the processed data",
                    required=False
                )
            ],
            context_keys=["condition_result", "action_taken", "processed_data_id"]
        )
    ),
    
    # Error handling and recovery steps
    "error_handler": StepDefinition(
        id="error_handler",
        name="Error Handler",
        description="Handles errors and provides recovery options",
        callback="steps.error_handler",
        category="error_handling",
        tags=["error", "recovery", "resilience"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="error_context",
                    type=DataType.JSON,
                    description="Context information about the error",
                    required=True
                ),
                IOSchema(
                    name="recovery_strategy",
                    type=DataType.STRING,
                    description="Strategy to use for recovery",
                    required=True,
                    default="retry"
                ),
                IOSchema(
                    name="max_retries",
                    type=DataType.INTEGER,
                    description="Maximum number of retry attempts",
                    required=False,
                    default=3
                )
            ],
            outputs=[
                IOSchema(
                    name="recovery_successful",
                    type=DataType.BOOLEAN,
                    description="Whether recovery was successful",
                    required=True
                ),
                IOSchema(
                    name="retry_count",
                    type=DataType.INTEGER,
                    description="Number of retry attempts made",
                    required=True
                ),
                IOSchema(
                    name="final_status",
                    type=DataType.STRING,
                    description="Final status after recovery attempts",
                    required=True
                )
            ],
            context_keys=["recovery_successful", "retry_count", "final_status"]
        )
    ),
    
    # Data aggregation and reduction steps
    "data_aggregator": StepDefinition(
        id="data_aggregator",
        name="Data Aggregator",
        description="Aggregates multiple data sources into a single result",
        callback="steps.data_aggregator",
        category="data_aggregation",
        tags=["aggregation", "reduction", "summary"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="data_ids",
                    type=DataType.JSON,
                    description="List of data IDs to aggregate",
                    required=True
                ),
                IOSchema(
                    name="aggregation_method",
                    type=DataType.STRING,
                    description="Method to use for aggregation",
                    required=True,
                    default="sum"
                ),
                IOSchema(
                    name="group_by",
                    type=DataType.JSON,
                    description="Fields to group by",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="aggregated_data_id",
                    type=DataType.STRING,
                    description="ID of the aggregated data",
                    required=True
                ),
                IOSchema(
                    name="aggregation_summary",
                    type=DataType.JSON,
                    description="Summary of the aggregation operation",
                    required=True
                ),
                IOSchema(
                    name="reduction_factor",
                    type=DataType.FLOAT,
                    description="Factor by which data was reduced",
                    required=True
                )
            ],
            context_keys=["aggregated_data_id", "aggregation_summary", "reduction_factor"]
        )
    ),
    
    # State management steps
    "state_manager": StepDefinition(
        id="state_manager",
        name="State Manager",
        description="Manages workflow state and persistence",
        callback="steps.state_manager",
        category="state_management",
        tags=["state", "persistence", "checkpoint"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="action",
                    type=DataType.STRING,
                    description="Action to perform (save, load, clear)",
                    required=True
                ),
                IOSchema(
                    name="state_key",
                    type=DataType.STRING,
                    description="Key for the state",
                    required=True
                ),
                IOSchema(
                    name="state_data",
                    type=DataType.JSON,
                    description="Data to save (for save action)",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="operation_successful",
                    type=DataType.BOOLEAN,
                    description="Whether the operation was successful",
                    required=True
                ),
                IOSchema(
                    name="state_value",
                    type=DataType.JSON,
                    description="Retrieved state value (for load action)",
                    required=False
                ),
                IOSchema(
                    name="state_size",
                    type=DataType.INTEGER,
                    description="Size of the state in bytes",
                    required=True
                )
            ],
            context_keys=["operation_successful", "state_value", "state_size"]
        )
    ),
    
    # Performance monitoring steps
    "performance_monitor": StepDefinition(
        id="performance_monitor",
        name="Performance Monitor",
        description="Monitors and reports performance metrics",
        callback="steps.performance_monitor",
        category="monitoring",
        tags=["performance", "monitoring", "metrics"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="monitor_target",
                    type=DataType.STRING,
                    description="Target to monitor (workflow, step, system)",
                    required=True
                ),
                IOSchema(
                    name="metrics",
                    type=DataType.JSON,
                    description="Metrics to collect",
                    required=False
                ),
                IOSchema(
                    name="duration",
                    type=DataType.INTEGER,
                    description="Duration to monitor in seconds",
                    required=False,
                    default=60
                )
            ],
            outputs=[
                IOSchema(
                    name="monitoring_report",
                    type=DataType.JSON,
                    description="Detailed monitoring report",
                    required=True
                ),
                IOSchema(
                    name="performance_score",
                    type=DataType.FLOAT,
                    description="Overall performance score",
                    required=True
                ),
                IOSchema(
                    name="recommendations",
                    type=DataType.JSON,
                    description="Performance improvement recommendations",
                    required=True
                )
            ],
            context_keys=["monitoring_report", "performance_score", "recommendations"]
        )
    ),
    
    # Data transformation steps
    "data_transformer": StepDefinition(
        id="data_transformer",
        name="Data Transformer",
        description="Transforms data between different formats",
        callback="steps.data_transformer",
        category="data_transformation",
        tags=["transformation", "format", "conversion"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="data_id",
                    type=DataType.STRING,
                    description="ID of the data to transform",
                    required=True
                ),
                IOSchema(
                    name="source_format",
                    type=DataType.STRING,
                    description="Source format of the data",
                    required=True
                ),
                IOSchema(
                    name="target_format",
                    type=DataType.STRING,
                    description="Target format for the data",
                    required=True
                ),
                IOSchema(
                    name="transformation_rules",
                    type=DataType.JSON,
                    description="Rules for the transformation",
                    required=False
                )
            ],
            outputs=[
                IOSchema(
                    name="transformed_data_id",
                    type=DataType.STRING,
                    description="ID of the transformed data",
                    required=True
                ),
                IOSchema(
                    name="transformation_metadata",
                    type=DataType.JSON,
                    description="Metadata about the transformation",
                    required=True
                ),
                IOSchema(
                    name="format_compatibility",
                    type=DataType.BOOLEAN,
                    description="Whether the transformation was compatible",
                    required=True
                )
            ],
            context_keys=["transformed_data_id", "transformation_metadata", "format_compatibility"]
        )
    ),
    
    # Workflow orchestration steps
    "workflow_orchestrator": StepDefinition(
        id="workflow_orchestrator",
        name="Workflow Orchestrator",
        description="Orchestrates sub-workflows and manages their execution",
        callback="steps.workflow_orchestrator",
        category="orchestration",
        tags=["orchestration", "sub-workflow", "management"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="sub_workflows",
                    type=DataType.JSON,
                    description="List of sub-workflows to orchestrate",
                    required=True
                ),
                IOSchema(
                    name="execution_strategy",
                    type=DataType.STRING,
                    description="Strategy for executing sub-workflows",
                    required=True,
                    default="sequential"
                ),
                IOSchema(
                    name="failure_handling",
                    type=DataType.STRING,
                    description="How to handle sub-workflow failures",
                    required=False,
                    default="stop_on_first"
                )
            ],
            outputs=[
                IOSchema(
                    name="orchestration_status",
                    type=DataType.STRING,
                    description="Status of the orchestration",
                    required=True
                ),
                IOSchema(
                    name="sub_workflow_results",
                    type=DataType.JSON,
                    description="Results from all sub-workflows",
                    required=True
                ),
                IOSchema(
                    name="total_execution_time",
                    type=DataType.FLOAT,
                    description="Total time for all sub-workflows",
                    required=True
                )
            ],
            context_keys=["orchestration_status", "sub_workflow_results", "total_execution_time"]
        )
    )
} 