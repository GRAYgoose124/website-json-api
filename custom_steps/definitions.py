from app.models import StepDefinition, StepIO, IOSchema, DataType


STEP_DEFINITIONS = {
        "data_validation": StepDefinition(
            id="data_validation",
            name="Data Validation",
            description="Validates input data format and constraints",
            callback="steps.validate_data",
            category="data_processing",
            tags=["data", "validation"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="data_path",
                        type=DataType.STRING,
                        description="Path to the data file to validate",
                        required=True,
                        default="/data/input.csv"
                    ),
                    IOSchema(
                        name="validation_type",
                        type=DataType.STRING,
                        description="Type of validation to perform",
                        required=False,
                        default="all",
                        constraints={"enum": ["schema", "format", "completeness", "all"]}
                    ),
                    IOSchema(
                        name="strict_mode",
                        type=DataType.BOOLEAN,
                        description="Enable strict validation rules",
                        required=False,
                        default=False
                    ),
                    IOSchema(
                        name="max_errors",
                        type=DataType.INTEGER,
                        description="Maximum number of errors to report",
                        required=False,
                        default=100,
                        constraints={"minimum": 1, "maximum": 1000}
                    )
                ],
                outputs=[
                    IOSchema(
                        name="validation_result",
                        type=DataType.JSON,
                        description="Validation results and statistics",
                        required=True
                    )
                ],
                context_keys=["validation_result"]
            )
        ),
        "data_processing": StepDefinition(
            id="data_processing",
            name="Data Processing",
            description="Processes validated data",
            callback="steps.process_data",
            category="data_processing",
            tags=["data", "processing"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="validation_result",
                        type=DataType.JSON,
                        description="Validation results from data validation step",
                        required=True
                    ),
                    IOSchema(
                        name="algorithm",
                        type=DataType.STRING,
                        description="Processing algorithm to use",
                        required=True,
                        default="standard",
                        constraints={"enum": ["standard", "advanced", "ml_optimized", "custom"]}
                    ),
                    IOSchema(
                        name="batch_size",
                        type=DataType.INTEGER,
                        description="Number of records to process in each batch",
                        required=False,
                        default=1000,
                        constraints={"minimum": 100, "maximum": 10000}
                    ),
                    IOSchema(
                        name="parallel_processing",
                        type=DataType.BOOLEAN,
                        description="Enable parallel processing for faster execution",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="output_format",
                        type=DataType.STRING,
                        description="Format for processed data output",
                        required=False,
                        default="csv",
                        constraints={"enum": ["csv", "json", "parquet", "hdf5"]}
                    )
                ],
                outputs=[
                    IOSchema(
                        name="processed_data",
                        type=DataType.DATASET,
                        description="Processed dataset",
                        required=True
                    )
                ],
                context_keys=["processed_data"]
            )
        ),
        "model_training": StepDefinition(
            id="model_training",
            name="Model Training",
            description="Trains machine learning models on processed data",
            callback="steps.train_model",
            category="ml",
            tags=["ml", "training"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="processed_data",
                        type=DataType.DATASET,
                        description="Processed dataset for training",
                        required=True
                    ),
                    IOSchema(
                        name="model_type",
                        type=DataType.STRING,
                        description="Type of model to train",
                        required=True,
                        default="neural_network",
                        constraints={"enum": ["neural_network", "random_forest", "svm", "linear_regression", "xgboost"]}
                    ),
                    IOSchema(
                        name="epochs",
                        type=DataType.INTEGER,
                        description="Number of training epochs",
                        required=False,
                        default=100,
                        constraints={"minimum": 1, "maximum": 1000}
                    ),
                    IOSchema(
                        name="learning_rate",
                        type=DataType.FLOAT,
                        description="Learning rate for training",
                        required=False,
                        default=0.001,
                        constraints={"minimum": 0.0001, "maximum": 1.0}
                    ),
                    IOSchema(
                        name="validation_split",
                        type=DataType.FLOAT,
                        description="Fraction of data to use for validation",
                        required=False,
                        default=0.2,
                        constraints={"minimum": 0.1, "maximum": 0.5}
                    ),
                    IOSchema(
                        name="early_stopping",
                        type=DataType.BOOLEAN,
                        description="Enable early stopping to prevent overfitting",
                        required=False,
                        default=True
                    )
                ],
                outputs=[
                    IOSchema(
                        name="trained_model",
                        type=DataType.MODEL,
                        description="Trained machine learning model",
                        required=True
                    ),
                    IOSchema(
                        name="training_metrics",
                        type=DataType.JSON,
                        description="Training metrics and performance",
                        required=True
                    )
                ],
                context_keys=["trained_model", "training_metrics"]
            )
        ),
        "result_analysis": StepDefinition(
            id="result_analysis",
            name="Result Analysis",
            description="Analyzes model results and generates reports",
            callback="steps.analyze_results",
            category="visualization",
            tags=["analysis", "visualization"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="trained_model",
                        type=DataType.MODEL,
                        description="Trained model for analysis",
                        required=True
                    ),
                    IOSchema(
                        name="training_metrics",
                        type=DataType.JSON,
                        description="Training metrics for analysis",
                        required=True
                    ),
                    IOSchema(
                        name="analysis_type",
                        type=DataType.STRING,
                        description="Type of analysis to perform",
                        required=True,
                        default="comprehensive",
                        constraints={"enum": ["comprehensive", "performance", "feature_importance", "error_analysis", "custom"]}
                    ),
                    IOSchema(
                        name="output_format",
                        type=DataType.STRING,
                        description="Format for analysis reports",
                        required=False,
                        default="pdf",
                        constraints={"enum": ["pdf", "html", "markdown", "json"]}
                    ),
                    IOSchema(
                        name="include_visualizations",
                        type=DataType.BOOLEAN,
                        description="Generate charts and graphs in the report",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="confidence_level",
                        type=DataType.FLOAT,
                        description="Confidence level for statistical analysis",
                        required=False,
                        default=0.95,
                        constraints={"minimum": 0.8, "maximum": 0.99}
                    )
                ],
                outputs=[
                    IOSchema(
                        name="analysis_report",
                        type=DataType.FILE,
                        description="Generated analysis report",
                        required=True,
                        format="pdf"
                    )
                ],
                context_keys=["analysis_report"]
            )
        ),
        "data_cleaning": StepDefinition(
            id="data_cleaning",
            name="Data Cleaning",
            description="Cleans and preprocesses raw data",
            callback="steps.clean_data",
            category="data_processing",
            tags=["data", "cleaning"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="raw_data",
                        type=DataType.DATASET,
                        description="Raw dataset to clean",
                        required=True
                    ),
                    IOSchema(
                        name="cleaning_method",
                        type=DataType.STRING,
                        description="Method to use for data cleaning",
                        required=True,
                        default="standard",
                        constraints={"enum": ["standard", "aggressive", "conservative", "custom"]}
                    ),
                    IOSchema(
                        name="remove_duplicates",
                        type=DataType.BOOLEAN,
                        description="Remove duplicate records from the dataset",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="handle_missing",
                        type=DataType.STRING,
                        description="Strategy for handling missing values",
                        required=False,
                        default="impute_mean",
                        constraints={"enum": ["drop", "impute_mean", "impute_median", "forward_fill"]}
                    ),
                    IOSchema(
                        name="outlier_threshold",
                        type=DataType.FLOAT,
                        description="Threshold for outlier detection (standard deviations)",
                        required=False,
                        default=3.0,
                        constraints={"minimum": 1.0, "maximum": 5.0}
                    ),
                    IOSchema(
                        name="normalize_data",
                        type=DataType.BOOLEAN,
                        description="Apply data normalization",
                        required=False,
                        default=True
                    )
                ],
                outputs=[
                    IOSchema(
                        name="cleaned_data",
                        type=DataType.DATASET,
                        description="Cleaned and preprocessed dataset",
                        required=True
                    )
                ],
                context_keys=["cleaned_data"]
            )
        ),
        "feature_engineering": StepDefinition(
            id="feature_engineering",
            name="Feature Engineering",
            description="Creates and selects features for machine learning",
            callback="steps.engineer_features",
            category="ml",
            tags=["ml", "features"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="cleaned_data",
                        type=DataType.DATASET,
                        description="Cleaned dataset for feature engineering",
                        required=True
                    ),
                    IOSchema(
                        name="feature_selection",
                        type=DataType.STRING,
                        description="Method for feature selection",
                        required=True,
                        default="correlation",
                        constraints={"enum": ["correlation", "mutual_info", "lasso", "recursive", "all"]}
                    ),
                    IOSchema(
                        name="create_interactions",
                        type=DataType.BOOLEAN,
                        description="Create interaction features between variables",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="polynomial_features",
                        type=DataType.INTEGER,
                        description="Degree of polynomial features to create",
                        required=False,
                        default=2,
                        constraints={"minimum": 1, "maximum": 3}
                    ),
                    IOSchema(
                        name="feature_scaling",
                        type=DataType.STRING,
                        description="Method for feature scaling",
                        required=False,
                        default="standard",
                        constraints={"enum": ["standard", "minmax", "robust", "none"]}
                    ),
                    IOSchema(
                        name="max_features",
                        type=DataType.INTEGER,
                        description="Maximum number of features to select",
                        required=False,
                        default=20,
                        constraints={"minimum": 5, "maximum": 100}
                    )
                ],
                outputs=[
                    IOSchema(
                        name="engineered_features",
                        type=DataType.DATASET,
                        description="Dataset with engineered features",
                        required=True
                    )
                ],
                context_keys=["engineered_features"]
            )
        ),
        "model_evaluation": StepDefinition(
            id="model_evaluation",
            name="Model Evaluation",
            description="Evaluates model performance using various metrics",
            callback="steps.evaluate_model",
            category="ml",
            tags=["ml", "evaluation"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="trained_model",
                        type=DataType.MODEL,
                        description="Trained model to evaluate",
                        required=True
                    ),
                    IOSchema(
                        name="engineered_features",
                        type=DataType.DATASET,
                        description="Dataset with features for evaluation",
                        required=True
                    ),
                    IOSchema(
                        name="metrics",
                        type=DataType.ARRAY,
                        description="Metrics to use for model evaluation",
                        required=True,
                        default=["accuracy", "precision", "recall", "f1"],
                        constraints={"items": {"enum": ["accuracy", "precision", "recall", "f1", "auc", "mae", "rmse"]}}
                    ),
                    IOSchema(
                        name="cross_validation",
                        type=DataType.BOOLEAN,
                        description="Use cross-validation for evaluation",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="cv_folds",
                        type=DataType.INTEGER,
                        description="Number of folds for cross-validation",
                        required=False,
                        default=5,
                        constraints={"minimum": 3, "maximum": 10}
                    ),
                    IOSchema(
                        name="test_size",
                        type=DataType.FLOAT,
                        description="Fraction of data to use for testing",
                        required=False,
                        default=0.2,
                        constraints={"minimum": 0.1, "maximum": 0.5}
                    ),
                    IOSchema(
                        name="stratified_sampling",
                        type=DataType.BOOLEAN,
                        description="Use stratified sampling for test set",
                        required=False,
                        default=True
                    )
                ],
                outputs=[
                    IOSchema(
                        name="evaluation_results",
                        type=DataType.JSON,
                        description="Model evaluation results and metrics",
                        required=True
                    )
                ],
                context_keys=["evaluation_results"]
            )
        ),
        "deployment_prep": StepDefinition(
            id="deployment_prep",
            name="Deployment Preparation",
            description="Prepares model for production deployment",
            callback="steps.prepare_deployment",
            category="deployment",
            tags=["deployment", "production"],
            io=StepIO(
                inputs=[
                    IOSchema(
                        name="trained_model",
                        type=DataType.MODEL,
                        description="Trained model for deployment",
                        required=True
                    ),
                    IOSchema(
                        name="evaluation_results",
                        type=DataType.JSON,
                        description="Model evaluation results",
                        required=True
                    ),
                    IOSchema(
                        name="deployment_type",
                        type=DataType.STRING,
                        description="Type of deployment to prepare",
                        required=True,
                        default="rest_api",
                        constraints={"enum": ["rest_api", "batch_processing", "streaming", "edge", "cloud"]}
                    ),
                    IOSchema(
                        name="api_format",
                        type=DataType.STRING,
                        description="Format for the API interface",
                        required=False,
                        default="json",
                        constraints={"enum": ["json", "protobuf", "graphql", "grpc"]}
                    ),
                    IOSchema(
                        name="containerization",
                        type=DataType.BOOLEAN,
                        description="Create Docker container for deployment",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="health_checks",
                        type=DataType.BOOLEAN,
                        description="Include health check endpoints",
                        required=False,
                        default=True
                    ),
                    IOSchema(
                        name="monitoring",
                        type=DataType.BOOLEAN,
                        description="Include monitoring and logging",
                        required=False,
                        default=True
                    )
                ],
                outputs=[
                    IOSchema(
                        name="deployment_package",
                        type=DataType.FILE,
                        description="Deployment package ready for production",
                        required=True,
                        format="tar.gz"
                    )
                ],
                context_keys=["deployment_package"]
            )
        )
}
