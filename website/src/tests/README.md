# Frontend API Tests

This directory contains comprehensive tests for the frontend API integration with the backend workflow system.

## Test Types

### 1. Unit Tests (`api-simple.test.js`)
- **Purpose**: Fast, isolated tests that mock all external dependencies
- **Use Case**: Testing API client logic, error handling, and data transformations
- **Setup**: Uses `setup-unit.js` with mocked fetch, localStorage, FormData, and File APIs
- **Speed**: Very fast execution

### 2. Integration Tests (`api-integration.test.js`)
- **Purpose**: End-to-end tests that use a real backend server
- **Use Case**: Testing actual API contracts, authentication, and real data flow
- **Setup**: Uses `setup-integration.js` with real fetch and no mocks
- **Speed**: Slower due to server startup/shutdown

## Running Tests

### Quick Commands
```bash
# Run all tests
npm test

# Run only unit tests (fast)
npm run test:unit

# Run only integration tests (real backend)
npm run test:integration

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Manual Commands
```bash
# Unit tests with mocks
npm test -- src/tests/api-simple.test.js

# Integration tests with real backend
TEST_ENV=integration npm test -- src/tests/api-integration.test.js

# Run specific test file
npm test -- src/tests/api-integration.test.js
```

## Test Coverage

### Unit Tests (`api-simple.test.js`)
- ✅ Authentication token management
- ✅ HTTP request formatting
- ✅ Error handling and parsing
- ✅ File upload mock testing
- ✅ Workflow creation mock testing

### Integration Tests (`api-integration.test.js`)
- ✅ **Health Check**: Backend server status
- ✅ **Authentication**: Real login with JWT tokens
- ✅ **Steps API**: Get available workflow steps
- ✅ **Workflows API**: Create, list, and retrieve workflows
- ✅ **Error Handling**: Invalid endpoints and data
- ✅ **File Upload**: Placeholder for future implementation

## Test Environment

### Unit Test Environment
- **Jest Environment**: `jsdom` (browser-like)
- **Mocks**: fetch, localStorage, FormData, File
- **Setup File**: `setup-unit.js`

### Integration Test Environment
- **Jest Environment**: `jsdom` (browser-like)
- **Real Dependencies**: fetch polyfill, no mocks
- **Backend Server**: Real Python FastAPI server on port 8003
- **Setup File**: `setup-integration.js`

## Backend Requirements

Integration tests require:
- Python backend server with FastAPI
- Test credentials: `test_user` / `test_password`
- Available endpoints: `/health`, `/auth/login`, `/steps`, `/workflows`
- Port 8003 available for test server

## Troubleshooting

### Integration Test Issues
1. **Port conflicts**: Ensure port 8003 is available
2. **Backend startup**: Check Python dependencies and step definitions
3. **Authentication**: Verify test credentials work
4. **Network issues**: Check firewall and connectivity

### Unit Test Issues
1. **Mock failures**: Check setup-unit.js configuration
2. **Environment issues**: Verify Jest and jsdom setup

## Adding New Tests

### For Unit Tests
1. Add test to `api-simple.test.js`
2. Use existing mocks from `setup-unit.js`
3. Focus on logic and error handling

### For Integration Tests
1. Add test to `api-integration.test.js`
2. Use real API endpoints
3. Test actual data flow and contracts

## Best Practices

1. **Unit tests first**: Write fast unit tests for new features
2. **Integration validation**: Use integration tests to verify API contracts
3. **Real data**: Integration tests should use realistic test data
4. **Cleanup**: Ensure tests clean up after themselves
5. **Isolation**: Tests should not depend on each other 