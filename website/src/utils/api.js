// API Client Utility for the new workflow system
const API_BASE = 'http://localhost:8002';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
    this.authToken = localStorage.getItem('authToken');
  }

  setAuthToken(token) {
    this.authToken = token;
    localStorage.setItem('authToken', token);
  }

  clearAuthToken() {
    this.authToken = null;
    localStorage.removeItem('authToken');
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
      headers: this.getHeaders(),
      ...options,
    };
    
    // Suppress logging for workflow requests to reduce noise
    const isWorkflowRequest = endpoint === '/workflows';
    if (!isWorkflowRequest) {
      console.log('[apiClient.request] About to fetch', url, 'with method:', config.method || 'GET', 'and body:', config.body);
    }
    
    try {
      const response = await fetch(url, config);
      
      if (!isWorkflowRequest) {
        console.log('[apiClient.request] Fetch response', response);
      }
      
      if (response.status === 401) {
        this.clearAuthToken();
        throw new Error('Authentication required');
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Log the response text before parsing JSON
      const responseText = await response.text();
      if (!isWorkflowRequest) {
        console.log('[apiClient.request] Response text:', responseText);
      }
      
      // Try to parse JSON
      let responseData;
      try {
        responseData = JSON.parse(responseText);
        if (!isWorkflowRequest) {
          console.log('[apiClient.request] Parsed response data:', responseData);
        }
      } catch (parseError) {
        console.error('[apiClient.request] JSON parse error:', parseError);
        throw new Error(`Failed to parse response: ${parseError.message}`);
      }
      
      return responseData;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Authentication
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Invalid credentials');
    }
    
    const data = await response.json();
    this.setAuthToken(data.access_token);
    return data;
  }

  // Health and Config
  async getHealth() {
    return this.request('/health');
  }

  async getConfig() {
    return this.request('/config');
  }

  // Steps
  async getSteps(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.tag) params.append('tag', filters.tag);
    if (filters.search) params.append('search', filters.search);
    
    const endpoint = `/steps${params.toString() ? `?${params.toString()}` : ''}`;
    return this.request(endpoint);
  }

  async getStepCategories() {
    return this.request('/steps/categories');
  }

  async getStepTags() {
    return this.request('/steps/tags');
  }

  // Workflows
  async getWorkflows(status = null) {
    const params = status ? `?status=${status}` : '';
    return this.request(`/workflows${params}`);
  }

  async getWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`);
  }

  async createWorkflow(definition) {
    console.log('[apiClient.createWorkflow] Creating workflow with definition:', definition);
    const result = await this.request('/workflows', {
      method: 'POST',
      body: JSON.stringify(definition),
    });
    console.log('[apiClient.createWorkflow] Received response:', result);
    return result;
  }

  async validateWorkflow(definition) {
    return this.request('/workflows/validate', {
      method: 'POST',
      body: JSON.stringify(definition),
    });
  }

  async resolveWorkflowDependencies(definition) {
    return this.request('/workflows/resolve-dependencies', {
      method: 'POST',
      body: JSON.stringify(definition),
    });
  }

  async getWorkflowDependencies(workflowId) {
    return this.request(`/workflows/${workflowId}/dependencies`);
  }

  async getWorkflowContext(workflowId) {
    return this.request(`/workflows/${workflowId}/context`);
  }

  async getContextFlow(workflowId) {
    return this.request(`/workflows/${workflowId}/context-flow`);
  }

  async executeStep(workflowId, stepId, params) {
    return this.request(`/workflows/${workflowId}/steps/${stepId}/execute`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getStepContext(workflowId, stepId) {
    return this.request(`/workflows/${workflowId}/steps/${stepId}/context`);
  }

  async forwardContext(workflowId, sourceStepId, targetStepId, contextKeys) {
    return this.request(`/workflows/${workflowId}/forward-context`, {
      method: 'POST',
      body: JSON.stringify({
        source_step_id: sourceStepId,
        target_step_id: targetStepId,
        context_keys: contextKeys,
      }),
    });
  }

  // Notices
  async getNotices(filters = {}) {
    const params = new URLSearchParams();
    if (filters.workflow_id) params.append('workflow_id', filters.workflow_id);
    if (filters.notice_type) params.append('notice_type', filters.notice_type);
    
    const endpoint = `/notices${params.toString() ? `?${params.toString()}` : ''}`;
    return this.request(endpoint);
  }

  async dismissNotice(noticeId) {
    return this.request(`/notices/${noticeId}`, {
      method: 'DELETE',
    });
  }

  // File operations
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/upload-file`, {
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

  getDownloadUrl(filePath) {
    // If the filePath already starts with /download/, don't add it again
    if (filePath.startsWith('/download/')) {
      return `${this.baseUrl}${filePath}`;
    }
    return `${this.baseUrl}/download/${filePath}`;
  }

  // WebSocket connection for real-time updates
  createWebSocketConnection() {
    if (!this.authToken) {
      throw new Error('Authentication required for WebSocket connection');
    }
    
    const wsUrl = `ws://localhost:8002/ws/notices`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return ws;
  }

  // Debug endpoints
  async getDebugWorkflowEngine() {
    return this.request('/debug/workflow-engine');
  }

  async getDebugStepRegistry() {
    return this.request('/debug/step-registry');
  }
}

// Create and export a singleton instance
const apiClient = new ApiClient();
export default apiClient; 