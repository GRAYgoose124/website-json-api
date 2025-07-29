import React from 'react';
import { Clock, Activity, CheckCircle, AlertCircle } from 'lucide-react';
import Modal from './Modal';
import WorkflowChain from './WorkflowChain';

const WorkflowDetails = ({ workflow, onClose }) => {
  if (!workflow) return null;

  const isStepFailed = (stepId) => {
    const result = workflow.step_results[stepId];
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

  const getStepStatus = (stepId) => {
    // If workflow is completed, check if individual steps failed
    if (workflow.status === 'completed') {
      if (isStepFailed(stepId)) return 'failed';
      return 'completed';
    }
    
    // If workflow is running, check current step and completed steps
    if (workflow.status === 'running') {
      if (workflow.current_step === stepId) return 'running';
      if (workflow.step_results[stepId]) {
        if (isStepFailed(stepId)) return 'failed';
        return 'completed';
      }
      return 'pending';
    }
    
    // If workflow failed, check individual step results
    if (workflow.status === 'failed') {
      // If this step has a result, check if it failed
      if (workflow.step_results[stepId]) {
        if (isStepFailed(stepId)) return 'failed';
        return 'completed';
      }
      // If this is the current step when workflow failed, it failed
      if (workflow.current_step === stepId) return 'failed';
      // Otherwise, it was never reached (pending)
      return 'pending';
    }
    
    // Default case: pending
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
      pending: 'text-gray-400 bg-gray-600',
      running: 'text-blue-400 bg-blue-600',
      completed: 'text-green-400 bg-green-600',
      failed: 'text-red-400 bg-red-600'
    };
    return colors[status];
  };

  const duration = workflow.completed_at && workflow.started_at
    ? new Date(workflow.completed_at) - new Date(workflow.started_at)
    : null;

  return (
    <Modal isOpen={!!workflow} onClose={onClose} title={workflow?.definition.name} size="lg">
      <div className="space-y-6">
        {/* Workflow Chain */}
        <div className="flex justify-center">
          <WorkflowChain workflow={workflow} isActive={false} />
        </div>
        
        {/* Workflow Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <div className="text-gray-400 text-xs mb-1">Status</div>
            <div className="font-medium text-white">{workflow.status}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <div className="text-gray-400 text-xs mb-1">Created</div>
            <div className="font-medium text-white">{new Date(workflow.created_at).toLocaleDateString()}</div>
          </div>
          {workflow.started_at && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <div className="text-gray-400 text-xs mb-1">Started</div>
              <div className="font-medium text-white">{new Date(workflow.started_at).toLocaleTimeString()}</div>
            </div>
          )}
          {duration && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
              <div className="text-gray-400 text-xs mb-1">Duration</div>
              <div className="font-medium text-white">{(duration / 1000).toFixed(1)}s</div>
            </div>
          )}
        </div>

        {/* Steps */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2">Workflow Steps</h3>
          
          {workflow.definition.steps.map((step, index) => {
            const status = getStepStatus(step.step_id);
            const stepResult = workflow.step_results[step.step_id];
            
            return (
              <div key={step.step_id} className="bg-gray-800 rounded-lg p-4 border border-gray-600">
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
                  <div className={`mt-3 p-3 rounded-lg border ${
                    isStepFailed(step.step_id) 
                      ? 'bg-red-600/20 border-red-500/30' 
                      : 'bg-green-600/20 border-green-500/30'
                  }`}>
                    <h5 className={`text-sm font-medium mb-2 ${
                      isStepFailed(step.step_id) ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {isStepFailed(step.step_id) ? 'Step Failed' : 'Step Result'}
                    </h5>
                    <pre className={`text-xs overflow-x-auto bg-gray-900 p-2 rounded border border-gray-600 ${
                      isStepFailed(step.step_id) ? 'text-red-300' : 'text-green-300'
                    }`}>
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

export default WorkflowDetails; 