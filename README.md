# Scientific Workflow Orchestration System

A modern, real-time workflow orchestration system for scientific computing with a beautiful React frontend and FastAPI backend.

## Features

- 🚀 **Real-time Workflow Execution** - Watch workflows execute step-by-step with live updates
- 📊 **Beautiful UI** - Modern, responsive interface with real-time notifications
- 🔄 **WebSocket Integration** - Live updates and connection management
- 📋 **Step Registry** - Easy to add new workflow steps
- 🎯 **Notice System** - Comprehensive logging and notification system
- 🎨 **Modern Design** - Glassmorphism UI with smooth animations

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic aiohttp
   ```

2. **Start the backend server:**
   ```bash
   uvicorn json_api:app --reload --port 8001
   ```

   The API will be available at `http://localhost:8001`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd workflow-ui
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Usage

### Creating Workflows

1. **Select Steps**: Choose from available workflow steps in the left panel
2. **Name Your Workflow**: Enter a descriptive name
3. **Create**: Click "Create Workflow" to start execution

### Available Steps

- **Data Validation** - Validates input data format and constraints
- **Data Cleaning** - Cleans and preprocesses raw data
- **Data Processing** - Processes validated data
- **Feature Engineering** - Creates and selects features for ML
- **Model Training** - Trains machine learning models
- **Model Evaluation** - Evaluates model performance
- **Result Analysis** - Analyzes results and generates reports
- **Deployment Preparation** - Prepares model for production

### Real-time Monitoring

- **Live Updates**: Watch workflow progress in real-time
- **System Notices**: View detailed logs and notifications
- **Connection Status**: Monitor WebSocket connection health
- **Auto-reconnection**: Automatic reconnection on connection loss

## API Endpoints

### HTTP Endpoints

- `GET /steps` - Get available workflow steps
- `GET /workflows` - List all workflows
- `POST /workflows` - Create a new workflow
- `GET /workflows/{id}` - Get specific workflow
- `GET /notices` - Get system notices
- `DELETE /notices/{id}` - Dismiss a notice

### WebSocket Endpoints

- `WS /ws/notices` - Real-time notice updates

## Development

### Adding New Steps

1. **Define the step function:**
   ```python
   @step_registry.register(StepDefinition(
       id="my_step",
       name="My Step",
       description="Description of what this step does",
       params_schema={
           "type": "object",
           "properties": {
               "param1": {"type": "string"}
           }
       }
   ))
   async def my_step(params: Dict[str, Any], context: StepContext):
       await context.info("Starting", "Step started")
       # Your step logic here
       await context.success("Complete", "Step completed")
       return {"result": "success"}
   ```

2. **The step will automatically appear in the UI**

### Testing

Run the backend test script:
```bash
python test_backend.py
```

## Architecture

### Backend (FastAPI)

- **NoticeManager**: Handles real-time notifications
- **StepRegistry**: Manages available workflow steps
- **WorkflowEngine**: Executes workflows with dependency resolution
- **WebSocket**: Real-time communication

### Frontend (React)

- **Real-time Updates**: WebSocket connection with auto-reconnection
- **Modern UI**: Tailwind CSS with glassmorphism design
- **Responsive**: Works on desktop and mobile
- **Error Handling**: Comprehensive error states and recovery

## Troubleshooting

### WebSocket Connection Issues

1. **Check CORS settings** in `main.py`
2. **Verify backend is running** on port 8001
3. **Check browser console** for connection errors
4. **Restart both servers** if needed

### Workflow Execution Issues

1. **Check step definitions** are properly registered
2. **Verify step dependencies** are correctly set
3. **Monitor system notices** for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details