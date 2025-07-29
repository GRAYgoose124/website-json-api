import React from 'react';
import { Clock, Activity, CheckCircle, AlertCircle, X } from 'lucide-react';
import WorkflowChain from './WorkflowChain';

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

export default WorkflowCard; 