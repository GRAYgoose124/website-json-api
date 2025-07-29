import React from 'react';

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

export default WorkflowChain; 