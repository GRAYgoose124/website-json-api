# Scientific Workflow UI

A modern React-based web interface for managing scientific workflows with real-time updates and advanced dependency management.

## Features

- 🔐 **Secure Authentication**: JWT-based authentication system
- 🔄 **Real-time Updates**: WebSocket-powered live updates for workflows and notices
- 📊 **Workflow Management**: Create, monitor, and manage complex scientific workflows
- 🧩 **Step Configuration**: Visual step selection and parameter configuration
- 📁 **File Operations**: Upload, download, and manage project files
- 🔗 **Dependency Resolution**: Automatic workflow dependency analysis and validation
- 📈 **Progress Tracking**: Real-time workflow execution progress monitoring
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- API server running on port 8002

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to `http://localhost:5173`

### API Server Setup

Make sure the API server is running:

```bash
# From the project root
python main.py --include-steps-root bundled_steps/project --include-steps-root bundled_steps/test_suite --port 8002
```

## Usage

### Authentication

1. **Login**: Use the test credentials:
   - Username: `test_user`
   - Password: `test_password`

2. **Session Management**: Tokens are automatically managed and refreshed

### Creating Workflows

1. **Select Steps**: Browse available steps by category, tags, or search
2. **Configure Parameters**: Set step-specific parameters with context-aware defaults
3. **Validate**: The system automatically validates workflow dependencies
4. **Execute**: Submit the workflow for execution

### Monitoring Workflows

- **Real-time Status**: Watch workflow progress in real-time
- **Step Results**: View detailed results for each completed step
- **Error Handling**: Clear error messages and recovery suggestions
- **File Downloads**: Automatic download prompts for completed workflows

### Managing Notices

- **Live Updates**: Real-time notice updates via WebSocket
- **Filtering**: Filter notices by type, severity, or workflow
- **Dismissal**: Dismiss notices when no longer needed
- **Auto-cleanup**: Automatic cleanup of old notices

## Architecture

### Frontend Structure

```
src/
├── components/          # React components
│   ├── LoginModal.jsx   # Authentication interface
│   ├── WorkflowCard.jsx # Workflow display component
│   ├── StepSelector.jsx # Step selection interface
│   └── ...
├── utils/              # Utility functions
│   ├── api.js          # API client and communication
│   ├── constants.js    # Constants and enums
│   └── workflowUtils.js # Workflow management utilities
└── App.jsx             # Main application component
```

### API Integration

The application uses a centralized API client (`src/utils/api.js`) that provides:

- **Authentication**: Automatic token management
- **Error Handling**: Consistent error handling across all requests
- **WebSocket**: Real-time communication for live updates
- **File Operations**: Streamlined upload/download functionality

### Key Components

#### API Client (`api.js`)
- Centralized API communication
- Automatic authentication handling
- WebSocket connection management
- File operation utilities

#### Workflow Utilities (`workflowUtils.js`)
- Workflow validation and creation
- Step status and progress tracking
- Context management and template resolution
- Error detection and handling

#### Constants (`constants.js`)
- Type definitions matching API models
- UI color schemes and styling
- Default configurations

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Variables

Create a `.env` file for custom configuration:

```env
VITE_API_BASE_URL=http://localhost:8002
VITE_WS_URL=ws://localhost:8002
```

### API Endpoints

The application integrates with the following API endpoints:

- **Authentication**: `/auth/login`
- **Workflows**: `/workflows/*`
- **Steps**: `/steps/*`
- **Notices**: `/notices/*`
- **Files**: `/upload-file`, `/download/*`
- **WebSocket**: `/ws/notices`

## Testing

### Manual Testing

1. **Authentication Flow**:
   - Login with test credentials
   - Verify token persistence
   - Test logout functionality

2. **Workflow Creation**:
   - Select and configure steps
   - Validate workflow dependencies
   - Submit and monitor execution

3. **Real-time Features**:
   - Monitor WebSocket connection
   - Test notice updates
   - Verify file download triggers

### API Testing

Use the provided test credentials to verify API integration:

```bash
# Test authentication
curl -X POST http://localhost:8002/auth/login \
  -F "username=test_user" \
  -F "password=test_password"

# Test steps endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:8002/steps
```

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Ensure API server is running on port 8002
   - Check firewall settings
   - Verify network connectivity

2. **Authentication Issues**:
   - Clear browser storage
   - Check token expiration
   - Verify API server authentication

3. **WebSocket Issues**:
   - Check WebSocket URL configuration
   - Verify CORS settings
   - Monitor browser console for errors

### Debug Mode

Enable debug logging by setting:

```javascript
localStorage.setItem('debug', 'true');
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests if applicable**
5. **Submit a pull request**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
4. Contact the development team

---

**Note**: This is a development version. For production use, ensure proper security configurations and environment setup.
