import React, { useState } from 'react';
import { Search as SearchIcon, CheckCircle, Plus, Loader2, Info } from 'lucide-react';

const StepSelector = ({ steps, selectedSteps, onStepToggle }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredSteps = Object.entries(steps).filter(([id, step]) =>
    step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    step.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStepEmoji = (stepId) => {
    const emojiMap = {
      create_project: '📁',
      upload_file_to_project: '📤',
      download_project_zip: '📥',
      list_project_files: '📋',
      data_processor: '⚙️',
      data_validator: '🔍',
      data_transformer: '🔄',
      data_aggregator: '📊',
      data_source: '📡',
      conditional_processor: '🔀',
      parallel_processor: '⚡',
      error_handler: '⚠️',
      performance_monitor: '📈',
      state_manager: '💾',
      workflow_orchestrator: '🎯',
      validate_project_token: '🔐'
    };
    return emojiMap[stepId] || '⚡';
  };

  const getStepTooltip = (step) => {
    const inputs = step.io?.inputs?.filter(input => input.required) || [];
    const outputs = step.io?.outputs || [];
    
    let tooltip = `${step.description}\n\n`;
    
    if (inputs.length > 0) {
      tooltip += `Required inputs:\n${inputs.map(input => `• ${input.name}`).join('\n')}\n\n`;
    }
    
    if (outputs.length > 0) {
      tooltip += `Provides:\n${outputs.map(output => `• ${output.name}`).join('\n')}`;
    }
    
    return tooltip;
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <input
          type="text"
          placeholder="Search steps..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-2 py-1 rounded-md bg-gray-900/50 border border-gray-700 focus:border-blue-500 focus:outline-none transition-colors text-xs"
        />
        <SearchIcon className="w-3 h-3 absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
      </div>
      
      <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto bg-gray-900/30 rounded-md p-1.5 border border-gray-700/50">
        {Object.keys(steps).length === 0 ? (
          <div className="text-center py-2 text-gray-500 w-full">
            <Loader2 className="w-3 h-3 mx-auto mb-1 animate-spin opacity-50" />
            <p className="text-xs">Loading steps...</p>
          </div>
        ) : filteredSteps.length === 0 ? (
          <div className="text-center py-2 text-gray-500 w-full">
            <SearchIcon className="w-3 h-3 mx-auto mb-1 opacity-50" />
            <p className="text-xs">No steps found</p>
          </div>
        ) : (
          filteredSteps.map(([id, step]) => (
            <div
              key={id}
              className={`px-1.5 py-0.5 rounded border transition-all cursor-pointer text-xs group relative ${
                selectedSteps.find(s => s.step_id === id)
                  ? 'bg-blue-500/20 border-blue-500/50 shadow-sm shadow-blue-500/20'
                  : 'bg-gray-800/30 border-gray-700/50 hover:border-gray-600 hover:bg-gray-800/50'
              }`}
              onClick={() => onStepToggle(id)}
              title={getStepTooltip(step)}
            >
              <div className="flex items-center gap-1">
                <span className="text-xs">{getStepEmoji(id)}</span>
                <span className="font-medium truncate max-w-16">{step.name}</span>
                {selectedSteps.find(s => s.step_id === id) ? (
                  <CheckCircle className="w-2.5 h-2.5 text-blue-400 flex-shrink-0" />
                ) : (
                  <Plus className="w-2.5 h-2.5 text-gray-600 flex-shrink-0" />
                )}
                {step.io?.inputs?.some(input => input.required) && (
                  <Info className="w-2.5 h-2.5 text-yellow-400 flex-shrink-0 opacity-60" />
                )}
              </div>
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-0 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-pre-line z-10 max-w-xs">
                {getStepTooltip(step)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StepSelector; 