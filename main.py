from app.api import app
from app.core import step_registry
from steps import (
    get_step_definitions,
    validate_data,
    process_data,
    train_model,
    analyze_results,
    clean_data,
    engineer_features,
    evaluate_model,
    prepare_deployment
)

# Register all step definitions and implementations
step_definitions = get_step_definitions()

# Register each step with its implementation
step_registry.register(step_definitions["data_validation"])(validate_data)
step_registry.register(step_definitions["data_processing"])(process_data)
step_registry.register(step_definitions["model_training"])(train_model)
step_registry.register(step_definitions["result_analysis"])(analyze_results)
step_registry.register(step_definitions["data_cleaning"])(clean_data)
step_registry.register(step_definitions["feature_engineering"])(engineer_features)
step_registry.register(step_definitions["model_evaluation"])(evaluate_model)
step_registry.register(step_definitions["deployment_prep"])(prepare_deployment)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
