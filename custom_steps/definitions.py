from app.models import StepDefinition


STEP_DEFINITIONS = {
        "data_validation": StepDefinition(
            id="data_validation",
            name="Data Validation",
            description="Validates input data format and constraints",
            callback="steps.validate_data",
            params_schema={
                "type": "object",
                "properties": {
                    "data_path": {
                        "type": "string",
                        "title": "Data Path",
                        "description": "Path to the data file to validate",
                        "default": "/data/input.csv"
                    },
                    "validation_type": {
                        "type": "string",
                        "title": "Validation Type",
                        "description": "Type of validation to perform",
                        "enum": ["schema", "format", "completeness", "all"],
                        "default": "all"
                    },
                    "strict_mode": {
                        "type": "boolean",
                        "title": "Strict Mode",
                        "description": "Enable strict validation rules",
                        "default": False
                    },
                    "max_errors": {
                        "type": "integer",
                        "title": "Max Errors",
                        "description": "Maximum number of errors to report",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 100
                    }
                },
                "required": ["data_path"]
            }
        ),
        "data_processing": StepDefinition(
            id="data_processing",
            name="Data Processing",
            description="Processes validated data",
            callback="steps.process_data",
            params_schema={
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "title": "Processing Algorithm",
                        "description": "Algorithm to use for data processing",
                        "enum": ["standard", "advanced", "ml_optimized", "custom"],
                        "default": "standard"
                    },
                    "batch_size": {
                        "type": "integer",
                        "title": "Batch Size",
                        "description": "Number of records to process in each batch",
                        "minimum": 100,
                        "maximum": 10000,
                        "default": 1000
                    },
                    "parallel_processing": {
                        "type": "boolean",
                        "title": "Parallel Processing",
                        "description": "Enable parallel processing for faster execution",
                        "default": True
                    },
                    "output_format": {
                        "type": "string",
                        "title": "Output Format",
                        "description": "Format for processed data output",
                        "enum": ["csv", "json", "parquet", "hdf5"],
                        "default": "csv"
                    }
                },
                "required": ["algorithm"]
            }
        ),
        "model_training": StepDefinition(
            id="model_training",
            name="Model Training",
            description="Trains machine learning models on processed data",
            callback="steps.train_model",
            params_schema={
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string",
                        "title": "Model Type",
                        "description": "Type of machine learning model to train",
                        "enum": ["neural_network", "random_forest", "svm", "linear_regression", "xgboost"],
                        "default": "neural_network"
                    },
                    "epochs": {
                        "type": "integer",
                        "title": "Training Epochs",
                        "description": "Number of training epochs",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 100
                    },
                    "learning_rate": {
                        "type": "number",
                        "title": "Learning Rate",
                        "description": "Learning rate for training",
                        "minimum": 0.0001,
                        "maximum": 1.0,
                        "default": 0.001
                    },
                    "validation_split": {
                        "type": "number",
                        "title": "Validation Split",
                        "description": "Fraction of data to use for validation",
                        "minimum": 0.1,
                        "maximum": 0.5,
                        "default": 0.2
                    },
                    "early_stopping": {
                        "type": "boolean",
                        "title": "Early Stopping",
                        "description": "Enable early stopping to prevent overfitting",
                        "default": True
                    }
                },
                "required": ["model_type"]
            }
        ),
        "result_analysis": StepDefinition(
            id="result_analysis",
            name="Result Analysis",
            description="Analyzes model results and generates reports",
            callback="steps.analyze_results",
            params_schema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "title": "Analysis Type",
                        "description": "Type of analysis to perform",
                        "enum": ["comprehensive", "performance", "feature_importance", "error_analysis", "custom"],
                        "default": "comprehensive"
                    },
                    "output_format": {
                        "type": "string",
                        "title": "Output Format",
                        "description": "Format for analysis reports",
                        "enum": ["pdf", "html", "markdown", "json"],
                        "default": "pdf"
                    },
                    "include_visualizations": {
                        "type": "boolean",
                        "title": "Include Visualizations",
                        "description": "Generate charts and graphs in the report",
                        "default": True
                    },
                    "confidence_level": {
                        "type": "number",
                        "title": "Confidence Level",
                        "description": "Confidence level for statistical analysis",
                        "minimum": 0.8,
                        "maximum": 0.99,
                        "default": 0.95
                    }
                },
                "required": ["analysis_type"]
            }
        ),
        "data_cleaning": StepDefinition(
            id="data_cleaning",
            name="Data Cleaning",
            description="Cleans and preprocesses raw data",
            callback="steps.clean_data",
            params_schema={
                "type": "object",
                "properties": {
                    "cleaning_method": {
                        "type": "string",
                        "title": "Cleaning Method",
                        "description": "Method to use for data cleaning",
                        "enum": ["standard", "aggressive", "conservative", "custom"],
                        "default": "standard"
                    },
                    "remove_duplicates": {
                        "type": "boolean",
                        "title": "Remove Duplicates",
                        "description": "Remove duplicate records from the dataset",
                        "default": True
                    },
                    "handle_missing": {
                        "type": "string",
                        "title": "Handle Missing Values",
                        "description": "Strategy for handling missing values",
                        "enum": ["drop", "impute_mean", "impute_median", "forward_fill"],
                        "default": "impute_mean"
                    },
                    "outlier_threshold": {
                        "type": "number",
                        "title": "Outlier Threshold",
                        "description": "Threshold for outlier detection (standard deviations)",
                        "minimum": 1.0,
                        "maximum": 5.0,
                        "default": 3.0
                    },
                    "normalize_data": {
                        "type": "boolean",
                        "title": "Normalize Data",
                        "description": "Apply data normalization",
                        "default": True
                    }
                },
                "required": ["cleaning_method"]
            }
        ),
        "feature_engineering": StepDefinition(
            id="feature_engineering",
            name="Feature Engineering",
            description="Creates and selects features for machine learning",
            callback="steps.engineer_features",
            params_schema={
                "type": "object",
                "properties": {
                    "feature_selection": {
                        "type": "string",
                        "title": "Feature Selection Method",
                        "description": "Method for feature selection",
                        "enum": ["correlation", "mutual_info", "lasso", "recursive", "all"],
                        "default": "correlation"
                    },
                    "create_interactions": {
                        "type": "boolean",
                        "title": "Create Interactions",
                        "description": "Create interaction features between variables",
                        "default": True
                    },
                    "polynomial_features": {
                        "type": "integer",
                        "title": "Polynomial Degree",
                        "description": "Degree of polynomial features to create",
                        "minimum": 1,
                        "maximum": 3,
                        "default": 2
                    },
                    "feature_scaling": {
                        "type": "string",
                        "title": "Feature Scaling",
                        "description": "Method for feature scaling",
                        "enum": ["standard", "minmax", "robust", "none"],
                        "default": "standard"
                    },
                    "max_features": {
                        "type": "integer",
                        "title": "Max Features",
                        "description": "Maximum number of features to select",
                        "minimum": 5,
                        "maximum": 100,
                        "default": 20
                    }
                },
                "required": ["feature_selection"]
            }
        ),
        "model_evaluation": StepDefinition(
            id="model_evaluation",
            name="Model Evaluation",
            description="Evaluates model performance using various metrics",
            callback="steps.evaluate_model",
            params_schema={
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "title": "Evaluation Metrics",
                        "description": "Metrics to use for model evaluation",
                        "items": {
                            "type": "string",
                            "enum": ["accuracy", "precision", "recall", "f1", "auc", "mae", "rmse"]
                        },
                        "default": ["accuracy", "precision", "recall", "f1"]
                    },
                    "cross_validation": {
                        "type": "boolean",
                        "title": "Cross Validation",
                        "description": "Use cross-validation for evaluation",
                        "default": True
                    },
                    "cv_folds": {
                        "type": "integer",
                        "title": "Cross Validation Folds",
                        "description": "Number of folds for cross-validation",
                        "minimum": 3,
                        "maximum": 10,
                        "default": 5
                    },
                    "test_size": {
                        "type": "number",
                        "title": "Test Set Size",
                        "description": "Fraction of data to use for testing",
                        "minimum": 0.1,
                        "maximum": 0.5,
                        "default": 0.2
                    },
                    "stratified_sampling": {
                        "type": "boolean",
                        "title": "Stratified Sampling",
                        "description": "Use stratified sampling for test set",
                        "default": True
                    }
                },
                "required": ["metrics"]
            }
        ),
        "deployment_prep": StepDefinition(
            id="deployment_prep",
            name="Deployment Preparation",
            description="Prepares model for production deployment",
            callback="steps.prepare_deployment",
            params_schema={
                "type": "object",
                "properties": {
                    "deployment_type": {
                        "type": "string",
                        "title": "Deployment Type",
                        "description": "Type of deployment to prepare",
                        "enum": ["rest_api", "batch_processing", "streaming", "edge", "cloud"],
                        "default": "rest_api"
                    },
                    "api_format": {
                        "type": "string",
                        "title": "API Format",
                        "description": "Format for the API interface",
                        "enum": ["json", "protobuf", "graphql", "grpc"],
                        "default": "json"
                    },
                    "containerization": {
                        "type": "boolean",
                        "title": "Containerization",
                        "description": "Create Docker container for deployment",
                        "default": True
                    },
                    "health_checks": {
                        "type": "boolean",
                        "title": "Health Checks",
                        "description": "Include health check endpoints",
                        "default": True
                    },
                    "monitoring": {
                        "type": "boolean",
                        "title": "Monitoring",
                        "description": "Include monitoring and logging",
                        "default": True
                    }
                },
                "required": ["deployment_type"]
            }
        )
    }
