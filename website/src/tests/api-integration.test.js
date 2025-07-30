/**
 * Frontend API Integration Tests (no mocks, uses real backend)
 * Tests the API functionality with a real running backend server
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// API client for testing
class ApiClient {
  constructor(baseUrl = 'http://localhost:8003') {
    this.baseUrl = baseUrl;
    this.authToken = null;
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = null;
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      method: 'GET',
      headers: this.getHeaders(),
      ...options
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    // Parse JSON response
    const responseText = await response.text();
    if (responseText.trim()) {
      try {
        return JSON.parse(responseText);
      } catch (parseError) {
        throw new Error(`Failed to parse response: ${parseError.message}`);
      }
    }
    
    return null;
  }

  async get(endpoint) {
    return this.request(endpoint);
  }

  async post(endpoint, data = null) {
    return this.request(endpoint, {
      method: 'POST',
      body: data
    });
  }

  async uploadFile(file) {
    // Note: This is a simplified file upload for testing
    // In a real implementation, you'd use FormData
    const url = `${this.baseUrl}/upload-file`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      },
      body: JSON.stringify({
        filename: file.name,
        content: file.content
      })
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    
    return response.json();
  }

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Login failed: ${response.status}`);
    }
    
    const data = await response.json();
    this.setAuthToken(data.access_token);
    return data;
  }
}

// Test server management
class TestServer {
  constructor() {
    this.serverProcess = null;
    this.isReady = false;
    this.tempUserdataDir = null;
  }

  async start() {
    return new Promise((resolve, reject) => {
      // Find the project root (two levels up from website/src/tests)
      const projectRoot = path.join(__dirname, '..', '..', '..');
      
      // Create a temporary userdata directory for test isolation
      this.tempUserdataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'workflow-api-test-'));
      console.log(`🧪 Using temporary userdata directory: ${this.tempUserdataDir}`);
      
      // Start the Python backend server with main.py and proper command line arguments
      this.serverProcess = spawn('uv', ['run', 'main.py', 
        '--include-steps-root', './bundled_steps/test_suite',
        '--userdata-root', this.tempUserdataDir,
        '--port', '8003'
      ], {
        cwd: projectRoot,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let output = '';
      let errorOutput = '';
      
      this.serverProcess.stdout.on('data', (data) => {
        output += data.toString();
        console.log(`[SERVER] ${data.toString().trim()}`);
        
        // Check if server is ready - look for uvicorn startup message
        if ((output.includes('Uvicorn running on') && output.includes('8003')) ||
            (errorOutput.includes('Uvicorn running on') && errorOutput.includes('8003'))) {
          this.isReady = true;
          resolve();
        }
      });

      this.serverProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
        const message = data.toString().trim();
        
        // Don't log normal startup messages as errors
        if (message.includes('Shutting down') || 
            message.includes('Application shutdown') || 
            message.includes('Finished server process') ||
            message.includes('Started server process') ||
            message.includes('Waiting for application startup') ||
            message.includes('Application startup complete') ||
            message.includes('Uvicorn running on')) {
          console.log(`[SERVER] ${message}`);
        } else {
          console.error(`[SERVER ERROR] ${message}`);
        }
        
        // Check if server is ready - look for uvicorn startup message
        if ((output.includes('Uvicorn running on') && output.includes('8003')) ||
            (errorOutput.includes('Uvicorn running on') && errorOutput.includes('8003'))) {
          this.isReady = true;
          resolve();
        }
      });

      this.serverProcess.on('error', (error) => {
        console.error('Failed to start server:', error);
        reject(error);
      });

      // Timeout after 15 seconds
      setTimeout(() => {
        if (!this.isReady) {
          this.serverProcess.kill();
          reject(new Error('Server startup timeout'));
        }
      }, 15000);
    });
  }

  async stop() {
    if (this.serverProcess) {
      // Remove event listeners to prevent logging after tests
      this.serverProcess.stdout.removeAllListeners();
      this.serverProcess.stderr.removeAllListeners();
      this.serverProcess.removeAllListeners();
      
      this.serverProcess.kill();
      this.serverProcess = null;
      this.isReady = false;
    }
    
    // Clean up temporary userdata directory
    if (this.tempUserdataDir && fs.existsSync(this.tempUserdataDir)) {
      try {
        fs.rmSync(this.tempUserdataDir, { recursive: true, force: true });
        console.log(`🧹 Cleaned up temporary userdata directory: ${this.tempUserdataDir}`);
      } catch (error) {
        console.warn(`⚠️  Failed to clean up temporary directory: ${error.message}`);
      }
    }
  }

  async waitForReady() {
    // Wait for server to be ready
    for (let i = 0; i < 30; i++) {
      try {
        const response = await fetch('http://localhost:8003/health');
        if (response.ok) {
          console.log('✅ Server is ready!');
          return true;
        } else {
          console.log(`Health check failed: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        console.log(`Fetch error: ${error.message}`);
      }
      if (i % 5 === 0) {
        console.log(`⏳ Waiting for server... (attempt ${i + 1}/30)`);
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error('Server not ready after 30 seconds');
  }
}

describe('API Integration Tests', () => {
  let testServer;
  let apiClient;

  beforeAll(async () => {
    console.log('🚀 Starting integration tests...');
    testServer = new TestServer();
    await testServer.start();
    await testServer.waitForReady();
    apiClient = new ApiClient();
    
    // Authenticate with test credentials
    console.log('🔐 Authenticating...');
    await apiClient.login('test_user', 'test_password');
    console.log('✅ Authentication successful');
    
    console.log('✅ Test setup complete');
  }, 60000);

  afterAll(async () => {
    console.log('🧹 Cleaning up test server...');
    await testServer.stop();
    // Wait a bit for server to fully shutdown
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('✅ Test cleanup complete');
  });

  beforeEach(() => {
    // Don't clear auth token - we want to maintain authentication across tests
    // apiClient.clearAuthToken();
  });

  describe('Health Check', () => {
    test('should return health status', async () => {
      const response = await apiClient.get('/health');
      expect(response).toBeDefined();
      expect(response.status).toBe('healthy');
    });
  });

  describe('Steps API', () => {
    test('should get available steps', async () => {
      const steps = await apiClient.get('/steps');
      expect(steps).toBeDefined();
      expect(typeof steps).toBe('object');
      expect(Object.keys(steps).length).toBeGreaterThan(0);
    });

    test('should get specific step details', async () => {
      // First get all steps to find a valid step ID
      const allSteps = await apiClient.get('/steps');
      const stepIds = Object.keys(allSteps);
      
      if (stepIds.length > 0) {
        const stepId = stepIds[0];
        // Now test the individual step details endpoint
        const stepDetails = await apiClient.get(`/steps/${stepId}`);
        expect(stepDetails).toBeDefined();
        expect(stepDetails.id).toBe(stepId);
        expect(stepDetails.name).toBeDefined();
        expect(stepDetails.description).toBeDefined();
        expect(stepDetails.callback).toBeDefined();
      } else {
        expect(stepIds.length).toBeGreaterThan(0); // Should have at least one step
      }
    });
  });

  describe('Workflows API', () => {
    test('should create a workflow', async () => {
      const workflowDefinition = {
        name: 'Test Integration Workflow',
        description: 'A test workflow created during integration tests',
        steps: [
          {
            step_id: 'data_source',
            params: { 
              source_type: 'file',
              file_path: '/tmp/test.txt'
            }
          }
        ]
      };

      const result = await apiClient.post('/workflows', workflowDefinition);
      expect(result).toBeDefined();
      expect(result.id).toBeDefined();
      expect(result.definition).toBeDefined();
      expect(result.definition.name).toBe(workflowDefinition.name);
    });

    test('should list workflows', async () => {
      const workflows = await apiClient.get('/workflows');
      expect(workflows).toBeDefined();
      expect(Array.isArray(workflows)).toBe(true);
    });

    test('should get workflow by ID', async () => {
      // First create a workflow
      const workflowDefinition = {
        name: 'Test Get Workflow',
        description: 'Workflow to test get by ID',
        steps: [
          {
            step_id: 'data_processor',
            params: { 
              data_id: 'test_data_123',
              algorithm: 'standard',
              parameters: {
                filter_enabled: true,
                quality_threshold: 0.8
              }
            }
          }
        ]
      };

      const created = await apiClient.post('/workflows', workflowDefinition);
      expect(created.id).toBeDefined();

      // Then get it by ID
      const retrieved = await apiClient.get(`/workflows/${created.id}`);
      expect(retrieved).toBeDefined();
      expect(retrieved.id).toBe(created.id);
      expect(retrieved.definition.name).toBe(workflowDefinition.name);
    });
  });

  describe('File Upload', () => {
    test('should upload a file', async () => {
      // Create a test file using Node.js FormData
      const FormData = require('form-data');
      const fs = require('fs');
      const path = require('path');
      
      // Create a temporary test file
      const testContent = 'This is a test file for integration testing';
      const tempFilePath = path.join(require('os').tmpdir(), 'test-integration.txt');
      fs.writeFileSync(tempFilePath, testContent);
      
      try {
        // Create FormData and append the file
        const formData = new FormData();
        formData.append('file', fs.createReadStream(tempFilePath), {
          filename: 'test-integration.txt',
          contentType: 'text/plain'
        });
        
        // Make the upload request
        const response = await fetch(`${apiClient.baseUrl}/upload-file`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiClient.authToken}`,
            ...formData.getHeaders()
          },
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status} - ${response.statusText}`);
        }
        
        const result = await response.json();
        expect(result).toBeDefined();
        expect(result.success).toBe(true);
        expect(result.temp_file_path).toBeDefined();
        
      } finally {
        // Clean up temporary file
        if (fs.existsSync(tempFilePath)) {
          fs.unlinkSync(tempFilePath);
        }
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle non-existent endpoints', async () => {
      await expect(apiClient.get('/non-existent-endpoint'))
        .rejects.toThrow();
    });

    test('should handle invalid workflow creation', async () => {
      const invalidWorkflow = {
        // Missing required fields
      };

      await expect(apiClient.post('/workflows', invalidWorkflow))
        .rejects.toThrow();
    });
  });
}); 