import React, { useState } from 'react';
import { Clock, Activity, CheckCircle, AlertCircle, Copy, Check } from 'lucide-react';
import Modal from './Modal';
import WorkflowChain from './WorkflowChain';

const WorkflowDetails = ({ workflow, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!workflow) return null;

  const copyToClipboard = async () => {
    const details = {
      id: workflow.id,
      name: workflow.definition.name,
      status: workflow.status,
      created_at: workflow.created_at,
      started_at: workflow.started_at,
      completed_at: workflow.completed_at,
      steps: workflow.definition.steps,
      step_results: workflow.step_results,
      current_step: workflow.current_step
    };
    
    try {
      await navigator.clipboard.writeText(JSON.stringify(details, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

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
      pending: <Clock className="w-3 h-3" />,
      running: <Activity className="w-3 h-3 animate-spin" />,
      completed: <CheckCircle className="w-3 h-3" />,
      failed: <AlertCircle className="w-3 h-3" />
    };
    return icons[status];
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-gray-400 bg-gray-600/20 border-gray-500/30',
      running: 'text-blue-400 bg-blue-600/20 border-blue-500/30',
      completed: 'text-green-400 bg-green-600/20 border-green-500/30',
      failed: 'text-red-400 bg-red-600/20 border-red-500/30'
    };
    return colors[status];
  };

  const duration = workflow.completed_at && workflow.started_at
    ? new Date(workflow.completed_at) - new Date(workflow.started_at)
    : null;

  return (
    <Modal isOpen={!!workflow} onClose={onClose} title={workflow?.definition.name} size="lg">
      <div className="space-y-4">
        {/* Header with Copy Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-white">Workflow Details</h2>
            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(workflow.status)}`}>
              {workflow.status}
            </span>
          </div>
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-600/20 border border-blue-500/30 text-blue-400 hover:bg-blue-600/30 transition-colors text-sm"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy Details
              </>
            )}
          </button>
        </div>

        {/* Workflow Chain */}
        <div className="flex justify-center">
          <WorkflowChain workflow={workflow} isActive={false} />
        </div>
        
        {/* Workflow Info - Compact Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
            <div className="text-gray-400 text-xs mb-1">Created</div>
            <div className="font-medium text-white text-sm">{new Date(workflow.created_at).toLocaleDateString()}</div>
          </div>
          {workflow.started_at && (
            <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
              <div className="text-gray-400 text-xs mb-1">Started</div>
              <div className="font-medium text-white text-sm">{new Date(workflow.started_at).toLocaleTimeString()}</div>
            </div>
          )}
          {duration && (
            <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
              <div className="text-gray-400 text-xs mb-1">Duration</div>
              <div className="font-medium text-white text-sm">{(duration / 1000).toFixed(1)}s</div>
            </div>
          )}
          <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
            <div className="text-gray-400 text-xs mb-1">Steps</div>
            <div className="font-medium text-white text-sm">{workflow.definition.steps.length}</div>
          </div>
        </div>

        {/* Steps - Tiled Layout */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-white border-b border-gray-700/50 pb-2">Workflow Steps</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {workflow.definition.steps.map((step, index) => {
              const status = getStepStatus(step.step_id);
              const stepResult = workflow.step_results[step.step_id];
              
              return (
                <div key={step.step_id} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="text-lg">{getStepEmoji(step.step_id)}</div>
                      <div>
                        <h4 className="font-medium text-white text-sm">
                          {step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </h4>
                        <p className="text-xs text-gray-400">Step {index + 1}</p>
                      </div>
                    </div>
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
                      {getStatusIcon(status)}
                      <span className="capitalize">{status}</span>
                    </div>
                  </div>
                  
                  {stepResult && (
                    <div className={`mt-2 p-2 rounded border text-xs ${
                      isStepFailed(step.step_id) 
                        ? 'bg-red-600/10 border-red-500/20' 
                        : 'bg-green-600/10 border-green-500/20'
                    }`}>
                      <h5 className={`font-medium mb-1 ${
                        isStepFailed(step.step_id) ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {isStepFailed(step.step_id) ? 'Failed' : 'Result'}
                      </h5>
                      <pre className={`overflow-x-auto bg-gray-900/50 p-2 rounded border border-gray-600/50 ${
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
      </div>
    </Modal>
  );
};

export default WorkflowDetails; 