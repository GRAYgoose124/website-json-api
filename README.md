# Workflow API with Dynamic Step Loading

This API allows you to define and execute custom workflow steps. The system dynamically loads step definitions and implementations from custom directories using a callback-based architecture.

## Custom Step Structure

Your custom step directory should contain Python files with step definitions and implementations. The system uses a callback-based approach where step definitions reference their implementations.

### Required Structure

1. **Step Definitions**: A dictionary or function that returns `StepDefinition` objects with callback references
2. **Step Implementations**: Async functions that implement the steps, referenced by callbacks

### Example Custom Step Structure

```
custom_steps/
├── definitions.py    # Step definitions with callbacks
└── steps.py         # Step implementations
```

### Example Custom Step Files

**definitions.py:**
```python
from app.models import StepDefinition

STEP_DEFINITIONS = {
    "data_validation": StepDefinition(
        id="data_validation",
        name="Data Validation",
        description="Validates input data format and constraints",
        callback="steps.validate_data",  # References implementation
        params_schema={
            "type": "object",
            "properties": {
                "data_path": {
                    "type": "string",
                    "title": "Data Path",
                    "description": "Path to the data file to validate"
                }
            },
            "required": ["data_path"]
        }
    )
}
```

**steps.py:**
```python
import asyncio
from typing import Dict, Any
from app.core import StepContext

async def validate_data(params: Dict[str, Any], context: StepContext):
    await context.info("Starting", f"Validating {params.get('data_path')}")
    
    # Your custom logic here
    await asyncio.sleep(1)
    
    await context.success("Complete", "Validation completed")
    return {"valid": True, "records": 1000}
```

## Command Line Options

```bash
python main.py --help
```

Available options:
- `--include-steps-root`: Path to directory containing custom step definitions (required)
- `--userdata-root`: Path to main userdata directory (will contain uploads and projects)
- `--host`: Host to bind server to (default: 0.0.0.0)
- `--port`: Port to bind server to (default: 8001)

## Example Usage

### 1. Create Custom Steps Directory
```
my_custom_steps/
├── definitions.py
└── steps.py
```

### 2. Run with Custom Steps
```bash
python main.py --include-steps-root ./my_custom_steps --include-steps-root ./bundled_steps/project --userdata-root ./my_userdata
```
