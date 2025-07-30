import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  AlertCircle, Sparkles, Plus, Settings, BarChart3, Info, RefreshCw, LogOut
} from 'lucide-react';

// Import components
import WorkflowChain from './components/WorkflowChain';
import Notice, { NoticeGroup } from './components/Notice';
import WorkflowCard from './components/WorkflowCard';
import Modal, { OverlayPopup, Tooltip } from './components/Modal';
import WorkflowDetails from './components/WorkflowDetails';
import StepSelector from './components/StepSelector';
import StepConfiguration from './components/StepConfiguration';
import Statistics from './components/Statistics';
import ConnectionStatus from './components/ConnectionStatus';
import LoadingSpinner from './components/LoadingSpinner';
import StepDependencies from './components/StepDependencies';
import LoginModal from './components/LoginModal';

const API_BASE = 'http://localhost:8002';

// Main App Component
export default function App() {
  const [notices, setNotices] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [steps, setSteps] = useState({});
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [workflowName, setWorkflowName] = useState('');
  const [selectedSteps, setSelectedSteps] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingWorkflow, setIsCreatingWorkflow] = useState(false);
  const [lastWorkflowUpdate, setLastWorkflowUpdate] = useState(null);
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(true);
  const [activeTab, setActiveTab] = useState('workflows');
  const [workflowDependencies, setWorkflowDependencies] = useState({});
  const [stepCategories, setStepCategories] = useState([]);
  const [stepTags, setStepTags] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));
  const [showLoginModal, setShowLoginModal] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const workflowPollingRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    const initializeApp = async () => {
      if (!authToken) {
        setShowLoginModal(true);
        return;
      }
      
      setIsLoading(true);
      try {
        await Promise.all([
          fetchSteps(),
          fetchWorkflows(),
          fetchNotices(),
          fetchStepCategories(),
          fetchStepTags()
        ]);
      } catch (error) {
        console.error('Failed to initialize app:', error);
        if (error.status === 401) {
          setShowLoginModal(true);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
    if (authToken) {
      connectWebSocket();
      startWorkflowPolling();
    }
    
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (workflowPollingRef.current) clearInterval(workflowPollingRef.current);
    };
  }, [authToken]);

  // Start automatic workflow polling
  const startWorkflowPolling = () => {
    workflowPollingRef.current = setInterval(() => {
      if (autoUpdateEnabled) {
        fetchWorkflows();
      }
    }, 2000);
  };

  // Toggle auto-updates
  const toggleAutoUpdate = () => {
    setAutoUpdateEnabled(!autoUpdateEnabled);
  };

  // Update selected workflow when workflows change
  useEffect(() => {
    if (selectedWorkflow) {
      const updatedWorkflow = workflows.find(w => w.id === selectedWorkflow.id);
      if (updatedWorkflow) {
        setSelectedWorkflow(updatedWorkflow);
        // Fetch dependencies for the selected workflow
        fetchWorkflowDependencies(updatedWorkflow.id);
      }
    }
  }, [workflows]);

  const fetchSteps = async () => {
    try {
      console.log('Fetching steps from:', `${API_BASE}/steps`);
      const res = await fetch(`${API_BASE}/steps`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const stepsData = await res.json();
        console.log('Fetched steps:', stepsData);
        setSteps(stepsData);
      } else if (res.status === 401) {
        throw { status: 401 };
      } else {
        console.error('Failed to fetch steps:', await res.text());
      }
    } catch (error) {
      console.error('Error fetching steps:', error);
      throw error;
    }
  };

  const fetchStepCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/steps/categories`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const categories = await res.json();
        setStepCategories(categories);
      } else if (res.status === 401) {
        throw { status: 401 };
      }
    } catch (error) {
      console.error('Error fetching step categories:', error);
      throw error;
    }
  };

  const fetchStepTags = async () => {
    try {
      const res = await fetch(`${API_BASE}/steps/tags`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const tags = await res.json();
        setStepTags(tags);
      } else if (res.status === 401) {
        throw { status: 401 };
      }
    } catch (error) {
      console.error('Error fetching step tags:', error);
      throw error;
    }
  };

  const fetchWorkflows = async () => {
    try {
      const res = await fetch(`${API_BASE}/workflows`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const workflowsData = await res.json();
        setWorkflows(workflowsData);
        setLastWorkflowUpdate(new Date());
      } else if (res.status === 401) {
        throw { status: 401 };
      } else {
        console.error('Failed to fetch workflows:', await res.text());
      }
    } catch (error) {
      console.error('Error fetching workflows:', error);
      throw error;
    }
  };

  const fetchWorkflowDependencies = async (workflowId) => {
    try {
      const res = await fetch(`${API_BASE}/workflows/${workflowId}/dependencies`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const dependencies = await res.json();
        setWorkflowDependencies(prev => ({
          ...prev,
          [workflowId]: dependencies
        }));
      } else if (res.status === 401) {
        throw { status: 401 };
      }
    } catch (error) {
      console.error('Error fetching workflow dependencies:', error);
      throw error;
    }
  };

  const fetchNotices = async () => {
    try {
      const res = await fetch(`${API_BASE}/notices`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const noticesData = await res.json();
        setNotices(noticesData);
      } else if (res.status === 401) {
        throw { status: 401 };
      } else {
        console.error('Failed to fetch notices:', await res.text());
      }
    } catch (error) {
      console.error('Error fetching notices:', error);
      throw error;
    }
  };

  const connectWebSocket = () => {
    try {
      wsRef.current = new WebSocket(`ws://localhost:8002/ws/notices`);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsReconnecting(false);
        setConnectionError('');
        reconnectAttemptsRef.current = 0;
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ping') return;
          
          setNotices(prev => [data, ...prev]);

          if (isDownloadNotification(data)) {
            // Check all workflows for download results
            handleDownloadNotification(data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          setIsReconnecting(true);
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current - 1), 30000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
            connectWebSocket();
          }, delay);
        } else {
          setConnectionError('Failed to reconnect after multiple attempts');
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };
      
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnectionError('Failed to create WebSocket connection');
    }
  };

  const dismissNotice = async (id) => {
    try {
      await fetch(`${API_BASE}/notices/${id}`, { 
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      setNotices(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to dismiss notice:', error);
    }
  };

  const handleLogin = (token) => {
    setAuthToken(token);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setAuthToken(null);
    setWorkflows([]);
    setNotices([]);
    setSteps({});
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  // Handle download notifications
  const handleDownload = (downloadUrl, filename) => {
    try {
      console.log(`Attempting download: ${downloadUrl} -> ${filename}`);
      
      // Create a temporary link element to trigger download
      const link = document.createElement('a');
      // Add cache-busting parameter to prevent browser caching
      const cacheBuster = `?t=${Date.now()}`;
      link.href = `${API_BASE}${downloadUrl}${cacheBuster}`;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`Download triggered: ${filename}`);
    } catch (error) {
      console.error('Failed to trigger download:', error);
    }
  };

  // Handle download notifications by checking workflow results
  const handleDownloadNotification = async (notice) => {
    try {
      console.log('Handling download notification:', notice);
      
      // Fetch latest workflows to get the most recent results
      const res = await fetch(`${API_BASE}/workflows`);
      if (res.ok) {
        const workflowsData = await res.json();
        
        // Find the most recent completed workflow with download results
        let mostRecentWorkflow = null;
        let mostRecentTime = 0;
        
        for (const workflow of workflowsData) {
          if (workflow.status === 'completed' && workflow.step_results) {
            for (const [stepId, result] of Object.entries(workflow.step_results)) {
              if (stepId === 'download_project_zip' && result.download_url && result.download_filename) {
                // Check if this workflow is more recent
                const workflowTime = new Date(workflow.created_at || workflow.updated_at || 0).getTime();
                if (workflowTime > mostRecentTime) {
                  mostRecentTime = workflowTime;
                  mostRecentWorkflow = { workflow, result };
                }
              }
            }
          }
        }
        
        // Only trigger download for the most recent workflow
        if (mostRecentWorkflow) {
          const { workflow, result } = mostRecentWorkflow;
          console.log(`Found most recent download result in workflow ${workflow.id}: ${result.download_filename}`);
          console.log(`Download URL: ${result.download_url}`);
          console.log(`Workflow time: ${new Date(mostRecentTime).toISOString()}`);
          
          // Only trigger if the workflow was completed recently (within last 5 minutes)
          const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
          if (mostRecentTime > fiveMinutesAgo) {
            handleDownload(result.download_url, result.download_filename);
          } else {
            console.log(`Skipping download for old workflow: ${workflow.id} (completed ${new Date(mostRecentTime).toISOString()})`);
          }
        } else {
          console.log('No recent completed workflows with download results found');
        }
      }
    } catch (error) {
      console.error('Failed to handle download notification:', error);
    }
  };

  // Check if a notice is a download notification
  const isDownloadNotification = (notice) => {
    return notice.title === 'Download Ready' && notice.message && notice.message.includes('ZIP file ready for download');
  };

  const createWorkflow = async () => {
    if (!workflowName || selectedSteps.length === 0) return;
    
    setIsCreatingWorkflow(true);
    try {
      const definition = {
        name: workflowName,
        description: `Workflow with ${selectedSteps.length} steps`,
        steps: selectedSteps
      };

      const res = await fetch(`${API_BASE}/workflows`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify(definition)
      });

      if (res.ok) {
        setWorkflowName('');
        setSelectedSteps([]);
        await fetchWorkflows();
      } else {
        const errorData = await res.json();
        console.error('Failed to create workflow:', errorData);
        // Show validation errors in notices
        if (errorData.errors) {
          errorData.errors.forEach(error => {
            setNotices(prev => [{
              id: Date.now().toString(),
              type: 'error',
              severity: 50,
              title: 'Workflow Validation Error',
              message: error,
              timestamp: new Date().toISOString(),
              dismissible: true
            }, ...prev]);
          });
        }
      }
    } catch (error) {
      console.error('Failed to create workflow:', error);
    } finally {
      setIsCreatingWorkflow(false);
    }
  };

  const toggleStep = (stepId) => {
    setSelectedSteps(prev => {
      const exists = prev.find(s => s.step_id === stepId);
      if (exists) {
        return prev.filter(s => s.step_id !== stepId);
      }
      return [...prev, { step_id: stepId, params: {} }];
    });
  };

  const updateStepParams = (stepId, params) => {
    setSelectedSteps(prev => 
      prev.map(step => 
        step.step_id === stepId ? { ...step, params } : step
      )
    );
  };

  const removeStep = (stepId) => {
    setSelectedSteps(prev => prev.filter(step => step.step_id !== stepId));
  };

  // Utility function to check if a step failed
  const isStepFailed = (stepId, workflow) => {
    const result = workflow?.step_results?.[stepId];
    if (!result) return false;
    
    // Check for common failure indicators in step results
    if (result.upload_status && result.upload_status.startsWith('failed')) {
      return true;
    }
    
    // Check for other status fields that might indicate failure
    for (const [key, value] of Object.entries(result)) {
      if (key.endsWith('_status') && typeof value === 'string' && value.startsWith('failed')) {
        return true;
      }
    }
    
    return false;
  };

  // Simulate workflow context based on selected steps
  const getWorkflowContext = () => {
    const context = {};
    
    // Find create_project step and extract its outputs
    const createProjectStep = selectedSteps.find(step => step.step_id === 'create_project');
    if (createProjectStep) {
      // Simulate the outputs that would be available after create_project runs
      context.project_id = 'simulated-project-id';
      context.project_path = '/projects/simulated-project-id';
      context.project_token = 'simulated-project-token';
    }
    
    return context;
  };

  const filteredSteps = () => {
    let filtered = steps;
    
    if (selectedCategory) {
      filtered = Object.fromEntries(
        Object.entries(steps).filter(([_, step]) => step.category === selectedCategory)
      );
    }
    
    if (selectedTag) {
      filtered = Object.fromEntries(
        Object.entries(filtered).filter(([_, step]) => step.tags.includes(selectedTag))
      );
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = Object.fromEntries(
        Object.entries(filtered).filter(([_, step]) => 
          step.name.toLowerCase().includes(query) ||
          step.description.toLowerCase().includes(query) ||
          step.tags.some(tag => tag.toLowerCase().includes(query))
        )
      );
    }
    
    return filtered;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-400">Loading workflow orchestration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <ConnectionStatus isConnected={isConnected} isReconnecting={isReconnecting} error={connectionError} isAutoUpdating={!!workflowPollingRef.current && autoUpdateEnabled} />
      
      {/* Workflow Details Modal */}
      <WorkflowDetails 
        workflow={selectedWorkflow} 
        onClose={() => setSelectedWorkflow(null)} 
      />
      
      <div className="max-w-7xl mx-auto px-3 py-3">
        {/* Header - Compact */}
        <header className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded-md bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30">
                <Sparkles className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold gradient-text-blue">
                  Workflow Orchestration
                </h1>
                <p className="text-gray-400 text-xs">Scientific computing made elegant</p>
              </div>
            </div>
            {authToken && (
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-red-500/20 border border-red-500/50 text-red-200 text-xs hover:bg-red-500/30 transition-colors"
              >
                <LogOut className="w-3 h-3" />
                Logout
              </button>
            )}
          </div>
          {connectionError && (
            <div className="flex items-center gap-2 p-1.5 rounded-md bg-red-500/20 border border-red-500/50 text-red-200 text-xs">
              <AlertCircle className="w-3 h-3" />
              <span>{connectionError}</span>
            </div>
          )}
        </header>

        <Statistics workflows={workflows} notices={notices} />

        {/* Main Content - Properly Tiled Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-4">
          {/* Workflow Creation - Compact */}
          <div className="lg:col-span-1">
            <div className="glass-medium rounded-lg p-3 border border-gray-700/50 shadow-lg h-fit">
              <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Plus className="w-3 h-3 text-blue-400" />
                Create Workflow
              </h2>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Name</label>
                  <input
                    type="text"
                    placeholder="Enter workflow name..."
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
                  />
                </div>
                
                {/* Step Filtering - Compact */}
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="flex-1 px-2 py-1.5 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
                    >
                      <option value="">All Categories</option>
                      {stepCategories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                    
                    <select
                      value={selectedTag}
                      onChange={(e) => setSelectedTag(e.target.value)}
                      className="flex-1 px-2 py-1.5 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
                    >
                      <option value="">All Tags</option>
                      {stepTags.map(tag => (
                        <option key={tag} value={tag}>{tag}</option>
                      ))}
                    </select>
                  </div>
                  
                  <input
                    type="text"
                    placeholder="Search steps..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
                  />
                </div>
                
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Steps ({selectedSteps.length} selected, {Object.keys(filteredSteps()).length} available)
                  </label>
                  <StepSelector 
                    steps={filteredSteps()} 
                    selectedSteps={selectedSteps} 
                    onStepToggle={toggleStep} 
                  />
                </div>
                
                <Tooltip content={!workflowName ? "Enter a workflow name" : selectedSteps.length === 0 ? "Select at least one step" : "Create new workflow"}>
                  <button
                    onClick={createWorkflow}
                    disabled={!workflowName || selectedSteps.length === 0 || isCreatingWorkflow}
                    className="w-full py-2 rounded-md bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium shadow-lg flex items-center justify-center gap-2 text-xs copy-button"
                  >
                    {isCreatingWorkflow ? (
                      <>
                        <LoadingSpinner size="sm" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Plus className="w-3 h-3" />
                        Create Workflow
                      </>
                    )}
                  </button>
                </Tooltip>
              </div>
            </div>
          </div>

          {/* Step Configuration - Compact */}
          <div className="lg:col-span-1">
            {selectedSteps.length > 0 ? (
              <div className="glass-medium rounded-lg p-3 border border-gray-700/50 shadow-lg h-fit">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Settings className="w-3 h-3 text-purple-400" />
                  Step Config ({selectedSteps.length})
                </h3>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {selectedSteps.map(step => (
                    <StepConfiguration
                      key={step.step_id}
                      step={step}
                      stepDefinition={steps[step.step_id]}
                      onUpdate={updateStepParams}
                      onRemove={removeStep}
                      workflowContext={getWorkflowContext()}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="glass-medium rounded-lg p-6 border border-gray-700/50 shadow-lg flex items-center justify-center h-40">
                <div className="text-center text-gray-500">
                  <Settings className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm font-medium mb-1">No steps selected</p>
                  <p className="text-gray-400 text-xs">Select steps to configure</p>
                </div>
              </div>
            )}
          </div>

          {/* Workflow Controls - Compact */}
          <div className="lg:col-span-1">
            <div className="glass-medium rounded-lg p-3 border border-gray-700/50 shadow-lg h-fit">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <BarChart3 className="w-3 h-3 text-green-400" />
                Workflow Controls
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Auto Updates</span>
                  <Tooltip content={autoUpdateEnabled ? "Auto-updates enabled" : "Manual updates only"}>
                    <button
                      onClick={toggleAutoUpdate}
                      className={`flex items-center gap-1 px-2 py-1 rounded border transition-colors text-xs ${
                        autoUpdateEnabled 
                          ? 'bg-green-500/20 border-green-500/50 text-green-400 hover:border-green-400' 
                          : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      <div className={`w-1 h-1 rounded-full ${autoUpdateEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
                      {autoUpdateEnabled ? 'Auto' : 'Manual'}
                    </button>
                  </Tooltip>
                </div>
                
                <Tooltip content="Refresh workflows">
                  <button
                    onClick={fetchWorkflows}
                    className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded glass-light border border-gray-700 hover:border-gray-600 transition-colors text-xs"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Refresh Workflows
                  </button>
                </Tooltip>
                
                {lastWorkflowUpdate && (
                  <div className="text-xs text-gray-500 text-center">
                    Updated: {lastWorkflowUpdate.toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats - Compact */}
          <div className="lg:col-span-1">
            <div className="glass-medium rounded-lg p-3 border border-gray-700/50 shadow-lg h-fit">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <BarChart3 className="w-3 h-3 text-blue-400" />
                Quick Stats
              </h3>
              
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Active Workflows:</span>
                  <span className="text-white font-medium">{workflows.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Notices:</span>
                  <span className="text-white font-medium">{notices.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Available Steps:</span>
                  <span className="text-white font-medium">{Object.keys(steps).length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Selected Steps:</span>
                  <span className="text-white font-medium">{selectedSteps.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Workflows and Notices - Side by Side */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {/* Workflows Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold flex items-center gap-1.5">
                <BarChart3 className="w-3 h-3 text-purple-400" />
                Active Workflows ({workflows.length})
                {workflowPollingRef.current && autoUpdateEnabled && (
                  <span className="text-xs text-green-400 flex items-center gap-1">
                    <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse" />
                    Auto
                  </span>
                )}
              </h2>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {workflows.length === 0 ? (
                <div className="text-center py-8 text-gray-500 glass-medium rounded-lg border border-gray-700/50 col-span-full">
                  <BarChart3 className="w-6 h-6 mx-auto mb-2 opacity-50" />
                  <h3 className="text-sm font-medium mb-1">No workflows yet</h3>
                  <p className="text-gray-400 text-xs">Create your first workflow to get started</p>
                </div>
              ) : (
                workflows.map(workflow => (
                  <WorkflowCard 
                    key={workflow.id} 
                    workflow={workflow} 
                    onSelect={setSelectedWorkflow}
                    isSelected={selectedWorkflow?.id === workflow.id}
                    isAutoUpdating={!!workflowPollingRef.current && autoUpdateEnabled}
                    dependencies={workflowDependencies[workflow.id]}
                  />
                ))
              )}
            </div>
          </div>

          {/* Notices Section */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold flex items-center gap-1.5">
              <Info className="w-3 h-3 text-blue-400" />
              System Notices ({notices.length})
            </h2>
            <div className="glass-medium rounded-lg border border-gray-700/50">
              <NoticeGroup notices={notices} onDismiss={dismissNotice} />
            </div>
          </div>
        </div>

        {/* Fixed Notices */}
        <div className="fixed bottom-4 right-4 space-y-2 z-50 max-w-sm">
          {notices.slice(0, 3).map((notice, index) => (
            <Notice
              key={`fixed-${notice.id}-${index}`}
              notice={notice}
              onDismiss={() => dismissNotice(notice.id)}
            />
          ))}
        </div>
      </div>

      {/* Login Modal */}
      <LoginModal 
        isOpen={showLoginModal} 
        onLogin={handleLogin} 
        onClose={() => setShowLoginModal(false)} 
      />
    </div>
  );
}