import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  AlertCircle, Sparkles, Plus, Settings, BarChart3, Info, RefreshCw
} from 'lucide-react';

// Import components
import WorkflowChain from './components/WorkflowChain';
import Notice from './components/Notice';
import WorkflowCard from './components/WorkflowCard';
import Modal from './components/Modal';
import WorkflowDetails from './components/WorkflowDetails';
import StepSelector from './components/StepSelector';
import StepConfiguration from './components/StepConfiguration';
import Statistics from './components/Statistics';
import ConnectionStatus from './components/ConnectionStatus';
import LoadingSpinner from './components/LoadingSpinner';

const API_BASE = 'http://localhost:8001';

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
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const workflowPollingRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    const initializeApp = async () => {
      setIsLoading(true);
      try {
        await Promise.all([
          fetchSteps(),
          fetchWorkflows(),
          fetchNotices()
        ]);
      } catch (error) {
        console.error('Failed to initialize app:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
    connectWebSocket();
    startWorkflowPolling();
    
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (workflowPollingRef.current) clearInterval(workflowPollingRef.current);
    };
  }, []);

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
      }
    }
  }, [workflows, selectedWorkflow]);

  const fetchSteps = async () => {
    try {
      console.log('Fetching steps from:', `${API_BASE}/steps`);
      const res = await fetch(`${API_BASE}/steps`);
      if (res.ok) {
        const stepsData = await res.json();
        console.log('Fetched steps:', stepsData);
        setSteps(stepsData);
      } else {
        console.error('Failed to fetch steps, status:', res.status);
      }
    } catch (error) {
      console.error('Failed to fetch steps:', error);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const res = await fetch(`${API_BASE}/workflows`);
      if (res.ok) {
        const newWorkflows = await res.json();
        setWorkflows(newWorkflows);
        setLastWorkflowUpdate(new Date());
        
        if (selectedWorkflow) {
          const updatedSelected = newWorkflows.find(w => w.id === selectedWorkflow.id);
          if (updatedSelected) {
            setSelectedWorkflow(updatedSelected);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    }
  };

  const fetchNotices = async () => {
    try {
      const res = await fetch(`${API_BASE}/notices`);
      if (res.ok) {
        setNotices(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch notices:', error);
    }
  };

  const connectWebSocket = useCallback(() => {
    try {
      if (wsRef.current) {
        wsRef.current.close();
      }

      wsRef.current = new WebSocket(`ws://localhost:8001/ws/notices`);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        setIsReconnecting(false);
        setConnectionError('');
        reconnectAttemptsRef.current = 0;
        console.log('WebSocket connected');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ping') return;
          
          setNotices(prev => [data, ...prev]);
          
          if (data.workflow_id) {
            fetchWorkflows();
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = (event) => {
        setIsConnected(false);
        console.log('WebSocket disconnected', event.code, event.reason);
        
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          setIsReconnecting(true);
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
        } else {
          setIsReconnecting(false);
          setConnectionError('Connection lost. Please refresh the page.');
        }
      };
      
      wsRef.current.onerror = (error) => {
        setIsConnected(false);
        setConnectionError('WebSocket connection failed');
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      setIsConnected(false);
      setConnectionError('Failed to create WebSocket connection');
      console.error('WebSocket connection error:', error);
    }
  }, []);

  const dismissNotice = async (id) => {
    try {
      await fetch(`${API_BASE}/notices/${id}`, { method: 'DELETE' });
      setNotices(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to dismiss notice:', error);
    }
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(definition)
      });

      if (res.ok) {
        setWorkflowName('');
        setSelectedSteps([]);
        await fetchWorkflows();
      } else {
        console.error('Failed to create workflow:', await res.text());
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
    setSelectedSteps(prev => prev.filter(s => s.step_id !== stepId));
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
      
      <div className="container mx-auto px-3 py-4">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-md bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30">
              <Sparkles className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Workflow Orchestration
              </h1>
              <p className="text-gray-400 text-xs">Scientific computing made elegant</p>
            </div>
          </div>
          {connectionError && (
            <div className="flex items-center gap-2 p-2 rounded-md bg-red-500/20 border border-red-500/50 text-red-200 text-xs">
              <AlertCircle className="w-3 h-3" />
              <span>{connectionError}</span>
            </div>
          )}
        </header>

        <Statistics workflows={workflows} notices={notices} />

        {/* Main Content */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          {/* Workflow Creation Sidebar */}
          <div className="xl:col-span-2">
            <div className="bg-gray-800/30 backdrop-blur-sm rounded-lg p-3 border border-gray-700/50 shadow-lg sticky top-4">
              <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Plus className="w-3 h-3 text-blue-400" />
                Create Workflow
              </h2>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Workflow Name</label>
                  <input
                    type="text"
                    placeholder="Enter workflow name..."
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Select Steps ({selectedSteps.length} selected, {Object.keys(steps).length} available)
                    {Object.keys(steps).length === 0 && (
                      <span className="text-xs text-yellow-400 ml-2">Loading...</span>
                    )}
                  </label>
                  <StepSelector steps={steps} selectedSteps={selectedSteps} onStepToggle={toggleStep} />
                </div>
                
                <button
                  onClick={createWorkflow}
                  disabled={!workflowName || selectedSteps.length === 0 || isCreatingWorkflow}
                  className="w-full py-2 rounded-md bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium shadow-lg flex items-center justify-center gap-2 text-xs"
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
              </div>
            </div>
          </div>

          {/* Step Configuration Area */}
          <div className="xl:col-span-3">
            {selectedSteps.length > 0 ? (
              <div className="bg-gray-800/30 backdrop-blur-sm rounded-lg p-3 border border-gray-700/50 shadow-lg">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Settings className="w-3 h-3 text-purple-400" />
                  Step Configuration ({selectedSteps.length} steps)
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {selectedSteps.map(step => (
                    <StepConfiguration
                      key={step.step_id}
                      step={step}
                      stepDefinition={steps[step.step_id]}
                      onUpdate={updateStepParams}
                      onRemove={removeStep}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-gray-800/30 backdrop-blur-sm rounded-lg p-6 border border-gray-700/50 shadow-lg flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Settings className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm font-medium mb-1">No steps selected</p>
                  <p className="text-xs">Select steps from the left panel to configure them here</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="mt-4">
          {/* Tab Navigation */}
          <div className="flex items-center gap-1 mb-4 bg-gray-800/30 rounded-md p-1 border border-gray-700/50">
            <button
              onClick={() => setActiveTab('workflows')}
              className={`flex-1 py-1.5 px-3 rounded font-medium transition-all duration-300 text-xs ${
                activeTab === 'workflows'
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30'
              }`}
            >
              <div className="flex items-center gap-1.5 justify-center">
                <BarChart3 className="w-3 h-3" />
                Workflows ({workflows.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('notices')}
              className={`flex-1 py-1.5 px-3 rounded font-medium transition-all duration-300 text-xs ${
                activeTab === 'notices'
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30'
              }`}
            >
              <div className="flex items-center gap-1.5 justify-center">
                <Info className="w-3 h-3" />
                Notices ({notices.length})
              </div>
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'workflows' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold flex items-center gap-1.5">
                    <BarChart3 className="w-3 h-3 text-purple-400" />
                    Active Workflows
                    {workflowPollingRef.current && autoUpdateEnabled && (
                      <span className="text-xs text-green-400 flex items-center gap-1">
                        <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse" />
                        Auto
                      </span>
                    )}
                  </h2>
                  {lastWorkflowUpdate && (
                    <span className="text-xs text-gray-500">
                      Updated: {lastWorkflowUpdate.toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={toggleAutoUpdate}
                    className={`flex items-center gap-1.5 px-2 py-1 rounded border transition-colors text-xs ${
                      autoUpdateEnabled 
                        ? 'bg-green-500/20 border-green-500/50 text-green-400 hover:border-green-400' 
                        : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <div className={`w-1 h-1 rounded-full ${autoUpdateEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
                    {autoUpdateEnabled ? 'Auto' : 'Manual'}
                  </button>
                  <button
                    onClick={fetchWorkflows}
                    className="flex items-center gap-1.5 px-2 py-1 rounded bg-gray-800/50 border border-gray-700 hover:border-gray-600 transition-colors text-xs"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Refresh
                  </button>
                </div>
              </div>
              
              <div className="grid gap-3">
                {workflows.length === 0 ? (
                  <div className="text-center py-12 text-gray-500 bg-gray-800/30 rounded-lg border border-gray-700/50">
                    <BarChart3 className="w-8 h-8 mx-auto mb-3 opacity-50" />
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
                    />
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold flex items-center gap-1.5">
                <Info className="w-3 h-3 text-blue-400" />
                System Notices
              </h2>
              <div className="space-y-2 max-h-[400px] overflow-y-auto bg-gray-800/30 rounded-lg p-3 border border-gray-700/50">
                {notices.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <h3 className="text-sm font-medium mb-1">No notices</h3>
                    <p className="text-gray-400 text-xs">System notices will appear here</p>
                  </div>
                ) : (
                  notices.map(notice => (
                    <Notice key={notice.id} notice={notice} onDismiss={dismissNotice} />
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}