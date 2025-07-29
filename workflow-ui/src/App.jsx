import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  AlertCircle, CheckCircle, Info, AlertTriangle, X, Activity, Play, Clock, Zap, 
  RefreshCw, Settings, BarChart3, Plus, ChevronRight, ChevronDown, Loader2,
  Calendar, Timer, User, Database, Cpu, Target, TrendingUp, Shield, Rocket, Search as SearchIcon,
  Edit3, Save, Trash2, Eye, EyeOff, ChevronUp, Sparkles, Flame, Droplets, Leaf, Star
} from 'lucide-react';

const API_BASE = 'http://localhost:8001';

// Animated Emoji Chain Component for Workflow Steps
const WorkflowChain = ({ workflow, isActive }) => {
  const getStepEmoji = (stepId) => {
    const emojiMap = {
      data_validation: '🔍',
      data_processing: '⚙️',
      model_training: '🧠',
      result_analysis: '📊',
      data_cleaning: '🧹',
      feature_engineering: '🔧',
      model_evaluation: '📈',
      deployment_prep: '🚀'
    };
    return emojiMap[stepId] || '⚡';
  };

  const getStepStatus = (stepId) => {
    if (workflow.status === 'completed') return 'completed';
    if (workflow.status === 'failed') return 'failed';
    if (workflow.current_step === stepId) return 'running';
    if (workflow.step_results[stepId]) return 'completed';
    return 'pending';
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-gray-400',
      running: 'text-blue-400 animate-pulse',
      completed: 'text-green-400',
      failed: 'text-red-400'
    };
    return colors[status];
  };

  return (
    <div className="flex items-center justify-center space-x-1 mb-3">
      {workflow.definition.steps.map((step, index) => {
        const status = getStepStatus(step.step_id);
        const isLast = index === workflow.definition.steps.length - 1;
        
        return (
          <div key={step.step_id} className="flex items-center">
            <div className={`relative group ${getStatusColor(status)}`}>
              <div className={`text-lg transition-all duration-500 ${
                status === 'running' ? 'animate-bounce' : 
                status === 'completed' ? 'animate-pulse' : ''
              }`}>
                {getStepEmoji(step.step_id)}
              </div>
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900/95 backdrop-blur-sm rounded border border-gray-700/50 text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
                {step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-3 border-r-3 border-t-3 border-transparent border-t-gray-900/95"></div>
              </div>
            </div>
            
            {!isLast && (
              <div className={`w-6 h-0.5 mx-1 transition-all duration-500 ${
                status === 'completed' ? 'bg-green-400' : 
                status === 'running' ? 'bg-blue-400' : 
                'bg-gray-600'
              }`} />
            )}
          </div>
        );
      })}
    </div>
  );
};

// Compact Notice Component
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
    setTimeout(() => onDismiss(notice.id), 200);
  };

  const icons = {
    error: <AlertCircle className="w-4 h-4" />,
    warning: <AlertTriangle className="w-4 h-4" />,
    info: <Info className="w-4 h-4" />,
    success: <CheckCircle className="w-4 h-4" />,
    debug: <Settings className="w-4 h-4" />
  };

  const colors = {
    error: 'from-red-500/20 to-red-600/20 border-red-500/50 text-red-200',
    warning: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-200',
    info: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-200',
    success: 'from-green-500/20 to-green-600/20 border-green-500/50 text-green-200',
    debug: 'from-purple-500/20 to-purple-600/20 border-purple-500/50 text-purple-200'
  };

  return (
    <div className={`relative overflow-hidden rounded-lg border backdrop-blur-md bg-gradient-to-br ${colors[notice.type]} p-3 transition-all duration-200 ${isExiting ? 'opacity-0 translate-x-full scale-95' : 'opacity-100 translate-x-0 scale-100'} shadow-lg`}>
      <div className="flex items-start space-x-2">
        <div className="flex-shrink-0 mt-0.5">{icons[notice.type]}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{notice.title}</h4>
          <p className="text-xs opacity-90 mt-1 line-clamp-2">{notice.message}</p>
          {notice.step_id && (
            <span className="text-xs opacity-70 mt-1 inline-block bg-black/20 px-2 py-0.5 rounded">
              {notice.step_id.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        {notice.dismissible && (
          <button 
            onClick={handleDismiss} 
            className="opacity-70 hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>
      {notice.auto_dismiss_seconds && (
        <div className="absolute bottom-0 left-0 h-0.5 bg-white/30 transition-all duration-100 rounded-b-lg" style={{ width: `${progress}%` }} />
      )}
    </div>
  );
};

// Compact Workflow Card
const WorkflowCard = ({ workflow, onSelect, isSelected, isAutoUpdating }) => {
  const statusColors = {
    pending: 'text-gray-400 bg-gray-500/20',
    running: 'text-blue-400 bg-blue-500/20 animate-pulse',
    completed: 'text-green-400 bg-green-500/20',
    failed: 'text-red-400 bg-red-500/20',
    cancelled: 'text-orange-400 bg-orange-500/20'
  };

  const statusIcons = {
    pending: <Clock className="w-3 h-3" />,
    running: <Activity className="w-3 h-3 animate-spin" />,
    completed: <CheckCircle className="w-3 h-3" />,
    failed: <AlertCircle className="w-3 h-3" />,
    cancelled: <X className="w-3 h-3" />
  };

  const totalSteps = workflow.definition.steps.length;
  const completedSteps = workflow.status === 'completed' ? totalSteps : 
                        workflow.status === 'failed' ? 0 : 
                        workflow.current_step ? workflow.definition.steps.findIndex(s => s.step_id === workflow.current_step) : 0;
  const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  return (
    <div className={`rounded-lg border transition-all duration-300 backdrop-blur-sm ${
      isSelected 
        ? 'bg-gradient-to-br from-blue-800/30 to-blue-900/30 border-blue-500/50 shadow-md shadow-blue-500/20' 
        : 'bg-gradient-to-br from-gray-800/50 to-gray-900/50 border-gray-700/50 hover:border-gray-600 hover:shadow-md hover:shadow-black/20'
    } ${workflow.status === 'running' && isAutoUpdating ? 'ring-1 ring-blue-500/30' : ''}`}>
      <div className="p-3">
        {/* Workflow Chain */}
        <WorkflowChain workflow={workflow} isActive={workflow.status === 'running'} />
        
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm truncate mb-0.5">{workflow.definition.name}</h3>
            <p className="text-xs text-gray-400 line-clamp-1">{workflow.definition.description}</p>
          </div>
          <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-medium ${statusColors[workflow.status]}`}>
            {statusIcons[workflow.status]}
            <span className="capitalize">{workflow.status}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Progress</span>
            <span>{completedSteps}/{totalSteps} steps</span>
          </div>
          <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
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

        {/* Current Step */}
        {workflow.current_step && workflow.status === 'running' && (
          <div className="mb-2 p-1.5 bg-blue-500/10 border border-blue-500/30 rounded-md">
            <div className="flex items-center gap-1.5 text-blue-400 text-xs">
              <Activity className="w-2.5 h-2.5 animate-spin" />
              <span className="truncate">
                {workflow.current_step.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={() => onSelect(workflow)}
          className="w-full py-1.5 px-3 rounded-md bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all duration-300 font-medium text-xs shadow-md"
        >
          View Details
        </button>
      </div>
    </div>
  );
};

// Clean Modal Component
const Modal = ({ isOpen, onClose, title, children, size = "md" }) => {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-2xl", 
    lg: "max-w-4xl",
    xl: "max-w-6xl"
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className={`bg-gray-900/95 backdrop-blur-md rounded-xl border border-gray-700/50 shadow-2xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-120px)]">
          {children}
        </div>
      </div>
    </div>
  );
};

// Workflow Details Modal
const WorkflowDetails = ({ workflow, onClose }) => {
  if (!workflow) return null;

  const getStepStatus = (stepId) => {
    if (workflow.status === 'completed') return 'completed';
    if (workflow.status === 'failed') return 'failed';
    if (workflow.current_step === stepId) return 'running';
    if (workflow.step_results[stepId]) return 'completed';
    return 'pending';
  };

  const getStepEmoji = (stepId) => {
    const emojiMap = {
      data_validation: '🔍',
      data_processing: '⚙️',
      model_training: '🧠',
      result_analysis: '📊',
      data_cleaning: '🧹',
      feature_engineering: '🔧',
      model_evaluation: '📈',
      deployment_prep: '🚀'
    };
    return emojiMap[stepId] || '⚡';
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
    <Modal isOpen={!!workflow} onClose={onClose} title={workflow?.definition.name} size="lg">
      <div className="space-y-4">
        {/* Workflow Chain */}
        <div className="flex justify-center">
          <WorkflowChain workflow={workflow} isActive={false} />
        </div>
        
        {/* Workflow Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-800/30 rounded-lg p-3">
            <div className="text-gray-400 text-xs">Status</div>
            <div className="font-medium">{workflow.status}</div>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-3">
            <div className="text-gray-400 text-xs">Created</div>
            <div className="font-medium">{new Date(workflow.created_at).toLocaleDateString()}</div>
          </div>
          {workflow.started_at && (
            <div className="bg-gray-800/30 rounded-lg p-3">
              <div className="text-gray-400 text-xs">Started</div>
              <div className="font-medium">{new Date(workflow.started_at).toLocaleTimeString()}</div>
            </div>
          )}
          {duration && (
            <div className="bg-gray-800/30 rounded-lg p-3">
              <div className="text-gray-400 text-xs">Duration</div>
              <div className="font-medium">{(duration / 1000).toFixed(1)}s</div>
            </div>
          )}
        </div>

        {/* Steps */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white">Workflow Steps</h3>
          
          {workflow.definition.steps.map((step, index) => {
            const status = getStepStatus(step.step_id);
            const stepResult = workflow.step_results[step.step_id];
            
            return (
              <div key={step.step_id} className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{getStepEmoji(step.step_id)}</div>
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
              </div>
            );
          })}
        </div>
      </div>
    </Modal>
  );
};

// Compact Step Selector
const StepSelector = ({ steps, selectedSteps, onStepToggle }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredSteps = Object.entries(steps).filter(([id, step]) =>
    step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    step.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStepEmoji = (stepId) => {
    const emojiMap = {
      data_validation: '🔍',
      data_processing: '⚙️',
      model_training: '🧠',
      result_analysis: '📊',
      data_cleaning: '🧹',
      feature_engineering: '🔧',
      model_evaluation: '📈',
      deployment_prep: '🚀'
    };
    return emojiMap[stepId] || '⚡';
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <input
          type="text"
          placeholder="Search steps..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-2 py-1.5 pl-8 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
        />
        <SearchIcon className="w-3 h-3 absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400" />
      </div>
      
      <div className="space-y-1 max-h-32 overflow-y-auto bg-gray-900/30 rounded-md p-2 border border-gray-700/50">
        {filteredSteps.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            <SearchIcon className="w-4 h-4 mx-auto mb-1 opacity-50" />
            <p className="text-xs">No steps found</p>
          </div>
        ) : (
          filteredSteps.map(([id, step]) => (
            <div
              key={id}
              className={`p-2 rounded-md border transition-all cursor-pointer ${
                selectedSteps.find(s => s.step_id === id)
                  ? 'bg-blue-500/20 border-blue-500/50 shadow-md shadow-blue-500/20'
                  : 'bg-gray-800/30 border-gray-700/50 hover:border-gray-600 hover:bg-gray-800/50'
              }`}
              onClick={() => onStepToggle(id)}
            >
              <div className="flex items-center gap-2">
                <div className="text-lg">{getStepEmoji(id)}</div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-xs">{step.name}</h4>
                  <p className="text-xs text-gray-400 line-clamp-1">{step.description}</p>
                </div>
                <div className={`flex-shrink-0 transition-colors ${selectedSteps.find(s => s.step_id === id) ? 'text-blue-400' : 'text-gray-600'}`}>
                  {selectedSteps.find(s => s.step_id === id) ? (
                    <CheckCircle className="w-3 h-3" />
                  ) : (
                    <Plus className="w-3 h-3" />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Compact Step Configuration Component
const StepConfiguration = ({ step, stepDefinition, onUpdate, onRemove }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [params, setParams] = useState(step.params || {});

  const schema = stepDefinition?.params_schema;
  const properties = schema?.properties || {};

  const handleParamChange = (key, value) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    onUpdate(step.step_id, newParams);
  };

  const renderParamInput = (key, prop) => {
    const value = params[key] ?? prop.default;
    
    switch (prop.type) {
      case 'string':
        if (prop.enum) {
          return (
            <select
              value={value}
              onChange={(e) => handleParamChange(key, e.target.value)}
              className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
            >
              {prop.enum.map(option => (
                <option key={option} value={option}>
                  {option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          );
        }
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParamChange(key, e.target.value)}
            placeholder={prop.description}
            className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            min={prop.minimum}
            max={prop.maximum}
            step="any"
            onChange={(e) => handleParamChange(key, parseFloat(e.target.value))}
            className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      case 'integer':
        return (
          <input
            type="number"
            value={value}
            min={prop.minimum}
            max={prop.maximum}
            onChange={(e) => handleParamChange(key, parseInt(e.target.value))}
            className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleParamChange(key, e.target.checked)}
              className="w-3 h-3 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1"
            />
          </div>
        );
      
      case 'array':
        if (prop.items?.enum) {
          return (
            <div className="space-y-1">
              {prop.items.enum.map(option => (
                <label key={option} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={Array.isArray(value) && value.includes(option)}
                    onChange={(e) => {
                      const currentArray = Array.isArray(value) ? value : [];
                      const newArray = e.target.checked
                        ? [...currentArray, option]
                        : currentArray.filter(item => item !== option);
                      handleParamChange(key, newArray);
                    }}
                    className="w-3 h-3 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1"
                  />
                  <span className="text-xs text-gray-300">
                    {option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </label>
              ))}
            </div>
          );
        }
        return (
          <input
            type="text"
            value={Array.isArray(value) ? value.join(', ') : ''}
            onChange={(e) => handleParamChange(key, e.target.value.split(',').map(s => s.trim()))}
            placeholder="Comma-separated values"
            className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParamChange(key, e.target.value)}
            className="w-full px-2 py-1 rounded-md bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
    }
  };

  const getStepEmoji = (stepId) => {
    const emojiMap = {
      data_validation: '🔍',
      data_processing: '⚙️',
      model_training: '🧠',
      result_analysis: '📊',
      data_cleaning: '🧹',
      feature_engineering: '🔧',
      model_evaluation: '📈',
      deployment_prep: '🚀'
    };
    return emojiMap[stepId] || '⚡';
  };

  return (
    <div className="bg-gray-800/30 rounded-md border border-gray-700/50 overflow-hidden">
      <div className="p-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="text-lg">{getStepEmoji(step.step_id)}</div>
            <div>
              <h4 className="font-medium text-xs text-white">
                {stepDefinition?.name || step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </h4>
              <p className="text-xs text-gray-400">
                {stepDefinition?.description || 'Step configuration'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 rounded hover:bg-gray-700/50 transition-colors"
            >
              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            <button
              onClick={() => onRemove(step.step_id)}
              className="p-1 rounded hover:bg-red-500/20 text-red-400 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="border-t border-gray-700/50 p-2 space-y-2">
          {Object.entries(properties).map(([key, prop]) => (
            <div key={key} className="space-y-1">
              <label className="block text-xs font-medium text-gray-300">
                {prop.title || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                {prop.description && (
                  <span className="block text-xs text-gray-500 mt-0.5">{prop.description}</span>
                )}
              </label>
              {renderParamInput(key, prop)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Compact Statistics
const Statistics = ({ workflows, notices }) => {
  const stats = {
    total: workflows.length,
    running: workflows.filter(w => w.status === 'running').length,
    completed: workflows.filter(w => w.status === 'completed').length,
    failed: workflows.filter(w => w.status === 'failed').length,
    notices: notices.length
  };

  const getStatusColor = (status) => {
    const colors = {
      total: 'from-blue-500 to-blue-600',
      running: 'from-green-500 to-green-600',
      completed: 'from-purple-500 to-purple-600',
      failed: 'from-red-500 to-red-600',
      notices: 'from-indigo-500 to-indigo-600'
    };
    return colors[status];
  };

  const getStatusIcon = (status) => {
    const icons = {
      total: <BarChart3 className="w-4 h-4" />,
      running: <Activity className="w-4 h-4" />,
      completed: <CheckCircle className="w-4 h-4" />,
      failed: <AlertCircle className="w-4 h-4" />,
      notices: <Info className="w-4 h-4" />
    };
    return icons[status];
  };

  return (
    <div className="grid grid-cols-5 gap-2 mb-4">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="bg-gray-800/30 backdrop-blur-sm rounded-md p-2 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 capitalize">{key}</p>
              <p className="text-sm font-bold text-white">{value}</p>
            </div>
            <div className={`p-1.5 rounded-md bg-gradient-to-br ${getStatusColor(key)}`}>
              {getStatusIcon(key)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Connection Status
const ConnectionStatus = ({ isConnected, isReconnecting, error, isAutoUpdating }) => (
  <div className={`fixed top-4 right-4 px-3 py-2 rounded-full text-xs font-medium flex items-center gap-2 backdrop-blur-md border ${
    isConnected 
      ? 'bg-green-500/20 text-green-400 border-green-500/50' 
      : isReconnecting
      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      : 'bg-red-500/20 text-red-400 border-red-500/50'
  } shadow-lg`}>
    {isReconnecting && <RefreshCw className="w-3 h-3 animate-spin" />}
    {isConnected ? (
      <>
        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
        Connected
        {isAutoUpdating && (
          <span className="text-xs opacity-70">• Auto</span>
        )}
      </>
    ) : isReconnecting ? (
      <>
        <Loader2 className="w-3 h-3 animate-spin" />
        Reconnecting...
      </>
    ) : (
      <>
        <div className="w-1.5 h-1.5 bg-red-400 rounded-full" />
        Disconnected
      </>
    )}
  </div>
);

// Loading Spinner
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
          <div className="xl:col-span-1">
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
                    Select Steps ({selectedSteps.length} selected)
                  </label>
                  <StepSelector steps={steps} selectedSteps={selectedSteps} onStepToggle={toggleStep} />
                </div>

                {/* Selected Steps Configuration */}
                {selectedSteps.length > 0 && (
                  <div>
                    <h3 className="text-xs font-medium text-gray-300 mb-2">Step Configuration</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
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
                )}
                
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

          {/* Main Content Area */}
          <div className="xl:col-span-4">
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
    </div>
  );
}