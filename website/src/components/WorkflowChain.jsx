import React from 'react';
import { ArrowRight, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const WorkflowChain = ({ workflow, isActive, dependencies }) => {
  const getStepEmoji = (stepId) => {
    const emojiMap = {
      load_data: '📁',
      clean_data: '🧹',
      feature_engineering: '🔧',
      train_model: '🧠',
      evaluate_model: '📊',
      generate_report: '📋',
      save_results: '💾',
      data_validation: '🔍',
      data_processing: '⚙️',
      model_training: '🧠',
      result_analysis: '📊',
      data_cleaning: '🧹',
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-3 h-3" />;
      case 'running':
        return <Clock className="w-3 h-3 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-3 h-3" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  // Get execution order from dependencies if available
  const executionOrder = dependencies?.execution_order || workflow.definition.steps.map(s => s.step_id);
  
  // Create a map of step positions for dependency visualization
  const stepPositions = {};
  executionOrder.forEach((stepId, index) => {
    stepPositions[stepId] = index;
  });

  return (
    <div className="space-y-3">
      {/* Execution Order */}
      <div className="flex items-center justify-center space-x-1">
        {executionOrder.map((stepId, index) => {
          const step = workflow.definition.steps.find(s => s.step_id === stepId);
          if (!step) return null;
          
          const status = getStepStatus(stepId);
          const isLast = index === executionOrder.length - 1;
          
          return (
            <div key={stepId} className="flex items-center">
              <div className={`relative group ${getStatusColor(status)}`}>
                <div className={`text-lg transition-all duration-500 ${
                  status === 'running' ? 'animate-bounce' : 
                  status === 'completed' ? 'animate-pulse' : ''
                }`}>
                  {getStepEmoji(stepId)}
                </div>
                
                {/* Status indicator */}
                <div className="absolute -top-1 -right-1">
                  {getStatusIcon(status)}
                </div>
                
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900/95 backdrop-blur-sm rounded-lg border border-gray-700/50 text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10 min-w-max">
                  <div className="font-medium mb-1">
                    {stepId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-gray-400">
                    Position: {index + 1} of {executionOrder.length}
                  </div>
                  {dependencies?.dependencies?.[stepId]?.length > 0 && (
                    <div className="text-gray-400 mt-1">
                      Depends on: {dependencies.dependencies[stepId].join(', ')}
                    </div>
                  )}
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-3 border-r-3 border-t-3 border-transparent border-t-gray-900/95"></div>
                </div>
              </div>
              
              {!isLast && (
                <div className={`w-8 h-0.5 mx-1 transition-all duration-500 ${
                  status === 'completed' ? 'bg-green-400' : 
                  status === 'running' ? 'bg-blue-400' : 
                  'bg-gray-600'
                }`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Dependency Graph (if dependencies available) */}
      {dependencies && (
        <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-700/50">
          <div className="text-xs font-medium text-gray-300 mb-2 flex items-center gap-1">
            <ArrowRight className="w-3 h-3" />
            Dependency Flow
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-xs">
            {/* Dependencies */}
            <div>
              <div className="text-gray-400 mb-1">Dependencies:</div>
              <div className="space-y-1">
                {Object.entries(dependencies.dependencies || {}).map(([stepId, deps]) => (
                  <div key={stepId} className="text-gray-300">
                    <span className="font-medium">{stepId}</span>
                    {deps.length > 0 && (
                      <span className="text-gray-500"> → {deps.join(', ')}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Execution Order */}
            <div>
              <div className="text-gray-400 mb-1">Execution Order:</div>
              <div className="space-y-1">
                {executionOrder.map((stepId, index) => (
                  <div key={stepId} className="text-gray-300">
                    <span className="text-gray-500">{index + 1}.</span>
                    <span className="font-medium ml-1">{stepId}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Validation Info */}
          {(dependencies.cycles?.length > 0 || dependencies.missing_dependencies?.length > 0) && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              {dependencies.cycles?.length > 0 && (
                <div className="text-red-400 text-xs mb-1">
                  ⚠️ Circular dependencies detected
                </div>
              )}
              {dependencies.missing_dependencies?.length > 0 && (
                <div className="text-yellow-400 text-xs">
                  ⚠️ Missing dependencies: {dependencies.missing_dependencies.length}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowChain; 