import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  AlertCircle, CheckCircle, Info, AlertTriangle, X, Activity, Play, Clock, Zap, 
  RefreshCw, Settings, BarChart3, Plus, ChevronRight, ChevronDown, Loader2,
  Calendar, Timer, User, Database, Cpu, Target, TrendingUp, Shield, Rocket, Search as SearchIcon
} from 'lucide-react';

const API_BASE = 'http://localhost:8001';

// Enhanced Notice component with better animations
const Notice = ({ notice, onDismiss }) => {
  const [progress, setProgress] = useState(100);
  const [isExiting, setIsExiting] = useState(false);
  
  useEffect(() => {
    if (notice.auto_dismiss_seconds) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev <= 0) {
            handleDismiss();
            return 0;
          }
          return prev - (100 / (notice.auto_dismiss_seconds * 10));
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [notice.auto_dismiss_seconds]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => onDismiss(notice.id), 300);
  };

  const icons = {
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
    success: <CheckCircle className="w-5 h-5" />,
    debug: <Settings className="w-5 h-5" />
  };

  const colors = {
    error: 'from-red-500/20 to-red-600/20 border-red-500/50 text-red-200',
    warning: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-200',
    info: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-200',
    success: 'from-green-500/20 to-green-600/20 border-green-500/50 text-green-200',
    debug: 'from-purple-500/20 to-purple-600/20 border-purple-500/50 text-purple-200'
  };

  return (
    <div className={`relative overflow-hidden rounded-xl border backdrop-blur-md bg-gradient-to-br ${colors[notice.type]} p-4 transition-all duration-300 ${isExiting ? 'opacity-0 translate-x-full scale-95' : 'opacity-100 translate-x-0 scale-100'} shadow-lg`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">{icons[notice.type]}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold truncate">{notice.title}</h4>
          <p className="text-sm opacity-90 mt-1 line-clamp-2">{notice.message}</p>
          {notice.step_id && (
            <span className="text-xs opacity-70 mt-2 inline-block bg-black/20 px-2 py-1 rounded">
              Step: {notice.step_id}
            </span>
          )}
        </div>
        {notice.dismissible && (
          <button 
            onClick={handleDismiss} 
            className="opacity-70 hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      {notice.auto_dismiss_seconds && (
        <div className="absolute bottom-0 left-0 h-1 bg-white/30 transition-all duration-100 rounded-b-xl" style={{ width: `${progress}%` }} />
      )}
    </div>
  );
};

// Enhanced Workflow Card with progress bar
const WorkflowCard = ({ workflow, onSelect, isSelected, isAutoUpdating }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const statusColors = {
    pending: 'text-gray-400 bg-gray-500/20',
    running: 'text-blue-400 bg-blue-500/20 animate-pulse',
    completed: 'text-green-400 bg-green-500/20',
    failed: 'text-red-400 bg-red-500/20',
    cancelled: 'text-orange-400 bg-orange-500/20'
  };

  const statusIcons = {
    pending: <Clock className="w-4 h-4" />,
    running: <Activity className="w-4 h-4 animate-spin" />,
    completed: <CheckCircle className="w-4 h-4" />,
    failed: <AlertCircle className="w-4 h-4" />,
    cancelled: <X className="w-4 h-4" />
  };

  const duration = workflow.completed_at && workflow.started_at
    ? new Date(workflow.completed_at) - new Date(workflow.started_at)
    : null;

  const totalSteps = workflow.definition.steps.length;
  const completedSteps = workflow.status === 'completed' ? totalSteps : 
                        workflow.status === 'failed' ? 0 : 
                        workflow.current_step ? workflow.definition.steps.findIndex(s => s.step_id === workflow.current_step) : 0;
  const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  const getStepIcon = (stepId) => {
    const stepIcons = {
      data_validation: <Shield className="w-4 h-4" />,
      data_processing: <Cpu className="w-4 h-4" />,
      model_training: <Target className="w-4 h-4" />,
      result_analysis: <TrendingUp className="w-4 h-4" />,
      data_cleaning: <Database className="w-4 h-4" />,
      feature_engineering: <Settings className="w-4 h-4" />,
      model_evaluation: <BarChart3 className="w-4 h-4" />,
      deployment_prep: <Rocket className="w-4 h-4" />
    };
    return stepIcons[stepId] || <Zap className="w-4 h-4" />;
  };

  return (
    <div className={`rounded-xl border transition-all duration-300 backdrop-blur-sm ${
      isSelected 
        ? 'bg-gradient-to-br from-blue-800/30 to-blue-900/30 border-blue-500/50 shadow-xl shadow-blue-500/20' 
        : 'bg-gradient-to-br from-gray-800/50 to-gray-900/50 border-gray-700/50 hover:border-gray-600 hover:shadow-xl hover:shadow-black/20'
    } ${workflow.status === 'running' && isAutoUpdating ? 'ring-1 ring-blue-500/30 animate-pulse' : ''}`}>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate">{workflow.definition.name}</h3>
            <p className="text-sm text-gray-400 mt-1 line-clamp-2">{workflow.definition.description}</p>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${statusColors[workflow.status]}`}>
            {statusIcons[workflow.status]}
            <span className="capitalize">{workflow.status}</span>
            {workflow.status === 'running' && isAutoUpdating && (
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>Progress</span>
            <span>{completedSteps}/{totalSteps} steps</span>
          </div>
          <div className="w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ease-out ${
                workflow.status === 'completed' ? 'bg-green-500' :
                workflow.status === 'failed' ? 'bg-red-500' :
                workflow.status === 'running' ? 'bg-blue-500' : 'bg-gray-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Workflow Details */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(workflow.created_at).toLocaleDateString()}
            </span>
            {duration && (
              <span className="flex items-center gap-1">
                <Timer className="w-3 h-3" />
                {(duration / 1000).toFixed(1)}s
              </span>
            )}
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 hover:text-gray-300 transition-colors"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            Details
          </button>
        </div>

        {/* Current Step Indicator */}
        {workflow.current_step && workflow.status === 'running' && (
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-center gap-2 text-blue-400">
              <Activity className="w-4 h-4 animate-spin" />
              <span className="text-sm font-medium">Current Step:</span>
              <span className="text-sm">{workflow.current_step}</span>
            </div>
          </div>
        )}

        {/* Expanded Details */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-700/50">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Workflow Steps</h4>
            <div className="space-y-2">
              {workflow.definition.steps.map((step, index) => (
                <div key={step.step_id} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/30">
                  <div className="flex-shrink-0">
                    {getStepIcon(step.step_id)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                    <div className="text-xs text-gray-400">Step {index + 1}</div>
                  </div>
                  {workflow.current_step === step.step_id && workflow.status === 'running' && (
                    <Activity className="w-4 h-4 text-blue-400 animate-spin" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => onSelect(workflow)}
            className="flex-1 py-2 px-4 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all duration-300 font-medium text-sm shadow-lg"
          >
            View Details
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Step Selector
const StepSelector = ({ steps, selectedSteps, onStepToggle }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredSteps = Object.entries(steps).filter(([id, step]) =>
    step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    step.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStepIcon = (stepId) => {
    const stepIcons = {
      data_validation: <Shield className="w-5 h-5" />,
      data_processing: <Cpu className="w-5 h-5" />,
      model_training: <Target className="w-5 h-5" />,
      result_analysis: <TrendingUp className="w-5 h-5" />,
      data_cleaning: <Database className="w-5 h-5" />,
      feature_engineering: <Settings className="w-5 h-5" />,
      model_evaluation: <BarChart3 className="w-5 h-5" />,
      deployment_prep: <Rocket className="w-5 h-5" />
    };
    return stepIcons[stepId] || <Zap className="w-5 h-5" />;
  };

  return (
    <div className="space-y-4">
      <div className="relative">
        <input
          type="text"
          placeholder="Search steps..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 pl-10 rounded-lg bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-sm"
        />
        <SearchIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {filteredSteps.map(([id, step]) => (
          <div
            key={id}
            className={`p-4 rounded-lg border transition-all cursor-pointer ${
              selectedSteps.find(s => s.step_id === id)
                ? 'bg-blue-500/20 border-blue-500/50 shadow-lg shadow-blue-500/20'
                : 'bg-gray-800/30 border-gray-700/50 hover:border-gray-600 hover:bg-gray-800/50'
            }`}
            onClick={() => onStepToggle(id)}
          >
            <div className="flex items-center gap-3">
              <div className={`flex-shrink-0 ${selectedSteps.find(s => s.step_id === id) ? 'text-blue-400' : 'text-gray-400'}`}>
                {getStepIcon(id)}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm">{step.name}</h4>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{step.description}</p>
              </div>
              <div className={`flex-shrink-0 transition-colors ${selectedSteps.find(s => s.step_id === id) ? 'text-blue-400' : 'text-gray-600'}`}>
                {selectedSteps.find(s => s.step_id === id) ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <Plus className="w-5 h-5" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Enhanced Connection Status
const ConnectionStatus = ({ isConnected, isReconnecting, error, isAutoUpdating }) => (
  <div className={`fixed top-4 right-4 px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 backdrop-blur-md border ${
    isConnected 
      ? 'bg-green-500/20 text-green-400 border-green-500/50' 
      : isReconnecting
      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      : 'bg-red-500/20 text-red-400 border-red-500/50'
  } shadow-lg`}>
    {isReconnecting && <RefreshCw className="w-4 h-4 animate-spin" />}
    {isConnected ? (
      <>
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        Connected
        {isAutoUpdating && (
          <span className="text-xs opacity-70">• Auto-updating</span>
        )}
      </>
    ) : isReconnecting ? (
      <>
        <Loader2 className="w-4 h-4 animate-spin" />
        Reconnecting...
      </>
    ) : (
      <>
        <div className="w-2 h-2 bg-red-400 rounded-full" />
        Disconnected
      </>
    )}
  </div>
);

// Loading Spinner Component
const LoadingSpinner = ({ size = "md" }) => {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8"
  };
  
  return (
    <div className="flex items-center justify-center">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-400`} />
    </div>
  );
};

// Workflow Details Modal Component
const WorkflowDetails = ({ workflow, onClose }) => {
  if (!workflow) return null;

  const getStepStatus = (stepId) => {
    if (workflow.status === 'completed') return 'completed';
    if (workflow.status === 'failed') return 'failed';
    if (workflow.current_step === stepId) return 'running';
    if (workflow.step_results[stepId]) return 'completed';
    return 'pending';
  };

  const getStepIcon = (stepId) => {
    const stepIcons = {
      data_validation: <Shield className="w-5 h-5" />,
      data_processing: <Cpu className="w-5 h-5" />,
      model_training: <Target className="w-5 h-5" />,
      result_analysis: <TrendingUp className="w-5 h-5" />,
      data_cleaning: <Database className="w-5 h-5" />,
      feature_engineering: <Settings className="w-5 h-5" />,
      model_evaluation: <BarChart3 className="w-5 h-5" />,
      deployment_prep: <Rocket className="w-5 h-5" />
    };
    return stepIcons[stepId] || <Zap className="w-5 h-5" />;
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: <Clock className="w-4 h-4" />,
      running: <Activity className="w-4 h-4 animate-spin" />,
      completed: <CheckCircle className="w-4 h-4" />,
      failed: <AlertCircle className="w-4 h-4" />
    };
    return icons[status];
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-gray-400 bg-gray-500/20',
      running: 'text-blue-400 bg-blue-500/20',
      completed: 'text-green-400 bg-green-500/20',
      failed: 'text-red-400 bg-red-500/20'
    };
    return colors[status];
  };

  const duration = workflow.completed_at && workflow.started_at
    ? new Date(workflow.completed_at) - new Date(workflow.started_at)
    : null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl border border-gray-700/50 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">{workflow.definition.name}</h2>
              <p className="text-gray-400 mt-1">{workflow.definition.description}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              Created: {new Date(workflow.created_at).toLocaleString()}
            </span>
            {workflow.started_at && (
              <span className="flex items-center gap-1">
                <Play className="w-4 h-4" />
                Started: {new Date(workflow.started_at).toLocaleString()}
              </span>
            )}
            {workflow.completed_at && (
              <span className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4" />
                Completed: {new Date(workflow.completed_at).toLocaleString()}
              </span>
            )}
            {duration && (
              <span className="flex items-center gap-1">
                <Timer className="w-4 h-4" />
                Duration: {(duration / 1000).toFixed(1)}s
              </span>
            )}
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">Workflow Steps</h3>
            
            {workflow.definition.steps.map((step, index) => {
              const status = getStepStatus(step.step_id);
              const stepResult = workflow.step_results[step.step_id];
              
              return (
                <div key={step.step_id} className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${getStatusColor(status)}`}>
                        {getStepIcon(step.step_id)}
                      </div>
                      <div>
                        <h4 className="font-medium text-white">
                          {step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </h4>
                        <p className="text-sm text-gray-400">Step {index + 1}</p>
                      </div>
                    </div>
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
                      {getStatusIcon(status)}
                      <span className="capitalize">{status}</span>
                    </div>
                  </div>
                  
                  {stepResult && (
                    <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <h5 className="text-sm font-medium text-green-400 mb-2">Step Result</h5>
                      <pre className="text-xs text-green-300 overflow-x-auto">
                        {JSON.stringify(stepResult, null, 2)}
                      </pre>
                    </div>
                  )}
                  
                  {status === 'failed' && (
                    <div className="mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <h5 className="text-sm font-medium text-red-400 mb-2">Error</h5>
                      <p className="text-xs text-red-300">Step failed to execute</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// Statistics Component
const Statistics = ({ workflows, notices }) => {
  const stats = {
    total: workflows.length,
    running: workflows.filter(w => w.status === 'running').length,
    completed: workflows.filter(w => w.status === 'completed').length,
    failed: workflows.filter(w => w.status === 'failed').length,
    pending: workflows.filter(w => w.status === 'pending').length,
    notices: notices.length
  };

  const getStatusColor = (status) => {
    const colors = {
      total: 'from-blue-500 to-blue-600',
      running: 'from-green-500 to-green-600',
      completed: 'from-purple-500 to-purple-600',
      failed: 'from-red-500 to-red-600',
      pending: 'from-yellow-500 to-yellow-600',
      notices: 'from-indigo-500 to-indigo-600'
    };
    return colors[status];
  };

  const getStatusIcon = (status) => {
    const icons = {
      total: <BarChart3 className="w-5 h-5" />,
      running: <Activity className="w-5 h-5" />,
      completed: <CheckCircle className="w-5 h-5" />,
      failed: <AlertCircle className="w-5 h-5" />,
      pending: <Clock className="w-5 h-5" />,
      notices: <Info className="w-5 h-5" />
    };
    return icons[status];
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 capitalize">{key}</p>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
            <div className={`p-2 rounded-lg bg-gradient-to-br ${getStatusColor(key)}`}>
              {getStatusIcon(key)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

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
    // Poll workflows every 2 seconds to get real-time updates
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
      const res = await fetch(`${API_BASE}/steps`);
      if (res.ok) {
        setSteps(await res.json());
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
        
        // Update selected workflow if it exists in the new data
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
          
          // Trigger workflow refresh when workflow-related notices are received
          if (data.workflow_id) {
            // Immediate workflow refresh for real-time updates
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
      {selectedWorkflow && (
        <WorkflowDetails 
          workflow={selectedWorkflow} 
          onClose={() => setSelectedWorkflow(null)} 
        />
      )}
      
      <div className="container mx-auto px-4 py-8">
        <header className="mb-12">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30">
              <BarChart3 className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Workflow Orchestration
              </h1>
              <p className="text-gray-400 mt-1">Scientific computing made elegant</p>
            </div>
          </div>
          {connectionError && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-200">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{connectionError}</span>
            </div>
          )}
        </header>

        <Statistics workflows={workflows} notices={notices} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Workflow Creation */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 shadow-xl">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Play className="w-5 h-5 text-blue-400" />
                Create Workflow
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Workflow Name</label>
                  <input
                    type="text"
                    placeholder="Enter workflow name..."
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Select Steps ({selectedSteps.length} selected)
                  </label>
                  <StepSelector steps={steps} selectedSteps={selectedSteps} onStepToggle={toggleStep} />
                </div>
                
                <button
                  onClick={createWorkflow}
                  disabled={!workflowName || selectedSteps.length === 0 || isCreatingWorkflow}
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium shadow-lg flex items-center justify-center gap-2"
                >
                  {isCreatingWorkflow ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5" />
                      Create Workflow
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Workflows & Notices */}
          <div className="lg:col-span-2 space-y-8">
            {/* Active Workflows */}
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-purple-400" />
                    Active Workflows ({workflows.length})
                    {workflowPollingRef.current && autoUpdateEnabled && (
                      <span className="text-xs text-green-400 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                        Auto-updating
                      </span>
                    )}
                  </h2>
                  {lastWorkflowUpdate && (
                    <span className="text-xs text-gray-500">
                      Last updated: {lastWorkflowUpdate.toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={toggleAutoUpdate}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors text-sm ${
                      autoUpdateEnabled 
                        ? 'bg-green-500/20 border-green-500/50 text-green-400 hover:border-green-400' 
                        : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${autoUpdateEnabled ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
                    {autoUpdateEnabled ? 'Auto' : 'Manual'}
                  </button>
                  <button
                    onClick={fetchWorkflows}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700 hover:border-gray-600 transition-colors text-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                </div>
              </div>
              
              <div className="grid gap-4">
                {workflows.length === 0 ? (
                  <div className="text-center py-16 text-gray-500 bg-gray-800/30 rounded-xl border border-gray-700/50">
                    <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No workflows yet</h3>
                    <p className="text-sm">Create your first workflow to get started</p>
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

            {/* Notices */}
            <div>
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-400" />
                System Notices ({notices.length})
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto bg-gray-800/30 rounded-xl p-4 border border-gray-700/50">
                {notices.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Info className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No notices</h3>
                    <p className="text-sm">System notices will appear here</p>
                  </div>
                ) : (
                  notices.map(notice => (
                    <Notice key={notice.id} notice={notice} onDismiss={dismissNotice} />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}