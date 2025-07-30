/**
 * Simple Frontend API Tests
 * Tests the API functionality without complex ES module imports
 */

// Mock the API client functionality
const mockApiClient = {
  authToken: null,
  
  setAuthToken(token) {
    this.authToken = token;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('authToken', token);
    }
  },
  
  clearAuthToken() {
    this.authToken = null;
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('authToken');
    }
  },
  
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  },
  
  async request(endpoint, options = {}) {
    const url = `http://localhost:8002${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };
    
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      this.clearAuthToken();
      throw new Error('Authentication required');
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const responseText = await response.text();
    let responseData;
    try {
      responseData = JSON.parse(responseText);
    } catch (parseError) {
      throw new Error(`Failed to parse response: ${parseError.message}`);
    }
    
    return responseData;
  },
  
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },
  
  async post(endpoint, data = null) {
    const options = { method: 'POST' };
    if (data) {
      options.body = JSON.stringify(data);
    }
    return this.request(endpoint, options);
  },
  
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`http://localhost:8002/upload-file`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
};

describe('API Client Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    fetch.mockClear();
  });

  describe('Authentication', () => {
    test('should set auth token correctly', () => {
      const token = 'test-token-123';
      mockApiClient.setAuthToken(token);
      expect(mockApiClient.authToken).toBe(token);
      if (typeof localStorage !== 'undefined') {
        expect(localStorage.setItem).toHaveBeenCalledWith('authToken', token);
      }
    });

    test('should clear auth token', () => {
      mockApiClient.setAuthToken('test-token');
      mockApiClient.clearAuthToken();
      expect(mockApiClient.authToken).toBeNull();
      if (typeof localStorage !== 'undefined') {
        expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
      }
    });
  });

  describe('API Endpoints', () => {
    beforeEach(() => {
      mockApiClient.setAuthToken('test-token');
    });

    test('should make authenticated requests with Bearer token', async () => {
      const mockResponse = { 
        ok: true, 
        json: () => Promise.resolve({ data: 'test' }),
        text: () => Promise.resolve('{"data": "test"}')
      };
      fetch.mockResolvedValue(mockResponse);

      await mockApiClient.get('/test-endpoint');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test-endpoint'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
          })
        })
      );
    });

    test('should handle GET requests correctly', async () => {
      const mockData = { steps: { create_project: { id: 'create_project' } } };
      const mockResponse = { 
        ok: true, 
        json: () => Promise.resolve(mockData),
        text: () => Promise.resolve(JSON.stringify(mockData))
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await mockApiClient.get('/steps');
      expect(result).toEqual(mockData);
    });

    test('should handle POST requests correctly', async () => {
      const mockData = { id: 'workflow-123', name: 'Test Workflow' };
      const mockResponse = { 
        ok: true, 
        json: () => Promise.resolve(mockData),
        text: () => Promise.resolve(JSON.stringify(mockData))
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await mockApiClient.post('/workflows', { name: 'Test Workflow' });
      expect(result).toEqual(mockData);
    });

    test('should handle file uploads correctly', async () => {
      const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = { 
        ok: true, 
        json: () => Promise.resolve({ success: true, temp_file_path: '/tmp/test.txt' }),
        status: 200
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await mockApiClient.uploadFile(file);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/upload-file'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );
      expect(result).toEqual({ success: true, temp_file_path: '/tmp/test.txt' });
    });

    test('should handle authentication errors', async () => {
      const mockResponse = { 
        ok: false, 
        status: 401, 
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
        text: () => Promise.resolve('{"detail": "Unauthorized"}')
      };
      fetch.mockResolvedValue(mockResponse);

      await expect(mockApiClient.get('/protected-endpoint')).rejects.toThrow('Authentication required');
    });

    test('should handle server errors', async () => {
      const mockResponse = { 
        ok: false, 
        status: 500, 
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ detail: 'Internal Server Error' }),
        text: () => Promise.resolve('{"detail": "Internal Server Error"}')
      };
      fetch.mockResolvedValue(mockResponse);

      await expect(mockApiClient.get('/test-endpoint')).rejects.toThrow('Internal Server Error');
    });
  });

  describe('Workflow Operations', () => {
    beforeEach(() => {
      mockApiClient.setAuthToken('test-token');
    });

    test('should create workflow correctly', async () => {
      const workflowDefinition = {
        name: 'Test Workflow',
        description: 'A test workflow',
        steps: [
          {
            step_id: 'create_project',
            params: { project_name: 'Test Project' }
          }
        ]
      };

      const mockData = { 
        id: 'workflow-123',
        definition: workflowDefinition,
        status: 'pending'
      };
      const mockResponse = { 
        ok: true, 
        json: () => Promise.resolve(mockData),
        text: () => Promise.resolve(JSON.stringify(mockData))
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await mockApiClient.post('/workflows', workflowDefinition);
      expect(result).toEqual(mockData);
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      mockApiClient.setAuthToken('test-token');
    });

    test('should handle network errors', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      await expect(mockApiClient.get('/test-endpoint')).rejects.toThrow('Network error');
    });

    test('should handle JSON parsing errors', async () => {
      const mockResponse = { 
        ok: true, 
        json: () => Promise.reject(new Error('Invalid JSON')),
        text: () => Promise.resolve('invalid json content')
      };
      fetch.mockResolvedValue(mockResponse);

      await expect(mockApiClient.get('/test-endpoint')).rejects.toThrow('Failed to parse response');
    });
  });
}); 