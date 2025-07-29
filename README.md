# Workflow API with Dynamic Step Loading

This API allows you to define and execute custom workflow steps. The system dynamically loads step definitions and implementations from custom directories using a callback-based architecture.

## Quick Start

### Using Custom Steps
```bash
python main.py --config-root /path/to/your/steps
# or
uv run main.py --config-root /path/to/your/steps
```

**Note:** The `--config-root` parameter is required. You must provide a path to your step definitions.

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

### Callback Resolution

The system supports several callback formats:

1. **Full module path**: `"custom_steps.steps.validate_data"`
2. **Relative path**: `".steps.validate_data"` (relative to config root)
3. **Direct function reference**: The function name if it's in the same module

### File Naming Conventions

The system will automatically find step files with these patterns:
- `definitions.py` (preferred for step definitions)
- `steps.py` (preferred for step implementations)
- `step_definitions.py`
- `workflow_steps.py`
- `*.steps.py`
- Any `.py` file (except `__init__.py`)

## Step Implementation Requirements

Each step implementation must:

1. Be an async function
2. Accept exactly 2 parameters:
   - `params`: Dictionary of step parameters
   - `context`: StepContext object for logging
3. Return a dictionary with results

### StepContext Methods

- `context.info(title, message)`: Log informational message
- `context.warning(title, message)`: Log warning message
- `context.error(title, message)`: Log error message
- `context.success(title, message)`: Log success message

## Command Line Options

```bash
python main.py --help
```

Available options:
- `--config-root`: Path to directory containing custom step definitions (required)
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
python main.py --config-root ./my_custom_steps
```

### 3. The system will:
- Load all Python files in the directory
- Extract step definitions from `STEP_DEFINITIONS` or `get_step_definitions()`
- Resolve callback references to actual functions
- Register all steps automatically
- Validate that all definitions have implementations

## Validation

The system validates:
- All step definitions have corresponding implementations (via callbacks)
- All callback references can be resolved
- Step function signatures are correct

If validation fails, the server will not start and will show error messages.

## API Endpoints

Once running, the API provides endpoints for:
- Listing available steps
- Executing individual steps
- Managing workflows
- Real-time notifications

## Error Handling

- Missing step directories will show clear error messages
- Invalid callback references will be caught and reported
- Validation errors prevent server startup
- Runtime errors are logged and reported via the notification system

## Migration from Old Format

If you have existing step files in the old format, you can:

1. Create a `definitions.py` file with your step definitions
2. Add `callback` fields to each `StepDefinition`
3. Reference your implementation functions in the callbacks
4. Use `--config-root` instead of the old parameter