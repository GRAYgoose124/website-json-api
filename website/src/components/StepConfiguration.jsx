import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Trash2 } from 'lucide-react';

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
              className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
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
            className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
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
            className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
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
            className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleParamChange(key, e.target.checked)}
              className="w-2.5 h-2.5 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1"
            />
          </div>
        );
      
      case 'array':
        if (prop.items?.enum) {
          return (
            <div className="space-y-0.5">
              {prop.items.enum.map(option => (
                <label key={option} className="flex items-center space-x-1">
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
                    className="w-2.5 h-2.5 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1"
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
            className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParamChange(key, e.target.value)}
            className="w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs"
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
    <div className="bg-gray-800/30 rounded border border-gray-700/50 overflow-hidden">
      <div className="p-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{getStepEmoji(step.step_id)}</span>
            <span className="font-medium text-xs text-white truncate">
              {stepDefinition?.name || step.step_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-0.5 rounded hover:bg-gray-700/50 transition-colors"
            >
              {isExpanded ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
            </button>
            <button
              onClick={() => onRemove(step.step_id)}
              className="p-0.5 rounded hover:bg-red-500/20 text-red-400 transition-colors"
            >
              <Trash2 className="w-2.5 h-2.5" />
            </button>
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="border-t border-gray-700/50 p-1.5 space-y-1.5">
          {Object.entries(properties).map(([key, prop]) => (
            <div key={key} className="space-y-0.5">
              <label className="block text-xs font-medium text-gray-300">
                {prop.title || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </label>
              {renderParamInput(key, prop)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StepConfiguration; 