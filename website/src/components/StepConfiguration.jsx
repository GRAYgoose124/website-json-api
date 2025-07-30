import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Trash2, Lock, Upload } from 'lucide-react';

const StepConfiguration = ({ step, stepDefinition, onUpdate, onRemove, workflowContext = {} }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [params, setParams] = useState(step.params || {});
  const [uploading, setUploading] = useState(false);

  // Use io.inputs instead of params_schema
  const inputs = stepDefinition?.io?.inputs || [];

  const handleParamChange = (key, value) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    onUpdate(step.step_id, newParams);
  };

  const handleFileUpload = async (inputName, file) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8002/upload-file', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: formData,
      });
      
      if (response.ok) {
        const result = await response.json();
        handleParamChange(inputName, result.file_path);
      } else {
        console.error('File upload failed:', await response.text());
      }
    } catch (error) {
      console.error('File upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  // Check if a parameter is auto-filled from context
  const isAutoFilled = (paramName) => {
    // Special handling for project_token in project steps
    if (paramName === 'project_token' && step.step_id !== 'create_project') {
      return 'project_token' in workflowContext;
    }
    return paramName in workflowContext;
  };

  const renderParamInput = (input) => {
    const value = params[input.name] ?? input.default;
    const autoFilled = isAutoFilled(input.name);
    
    // If auto-filled, show the context value instead
    const displayValue = autoFilled ? workflowContext[input.name] : value;
    
    // Check if this is a file path input
    const isFilePath = input.name === 'file_path' || 
                      input.name.includes('path') || 
                      input.description?.toLowerCase().includes('file') ||
                      input.description?.toLowerCase().includes('path');
    
    switch (input.type) {
      case 'string':
        if (input.constraints?.enum) {
          return (
            <div className="relative">
              <select
                value={displayValue}
                onChange={(e) => handleParamChange(input.name, e.target.value)}
                disabled={autoFilled}
                className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                  autoFilled ? 'opacity-60 cursor-not-allowed' : ''
                }`}
              >
                {input.constraints.enum.map(option => (
                  <option key={option} value={option}>
                    {option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
              {autoFilled && (
                <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
              )}
            </div>
          );
        }
        
        // File input for file paths
        if (isFilePath && !autoFilled) {
          return (
            <div className="relative">
              <div className="flex gap-1">
                <input
                  type="text"
                  value={displayValue}
                  onChange={(e) => handleParamChange(input.name, e.target.value)}
                  placeholder={input.description || "Enter file path or upload file"}
                  disabled={autoFilled || uploading}
                  className={`flex-1 px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                    autoFilled || uploading ? 'opacity-60 cursor-not-allowed' : ''
                  }`}
                />
                <input
                  type="file"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      handleFileUpload(input.name, file);
                    }
                  }}
                  className="hidden"
                  id={`file-input-${input.name}`}
                  disabled={uploading}
                />
                <label
                  htmlFor={`file-input-${input.name}`}
                  className={`px-2 py-0.5 border rounded text-xs cursor-pointer transition-colors flex items-center gap-1 ${
                    uploading 
                      ? 'bg-gray-500/20 border-gray-500/50 text-gray-400 cursor-not-allowed' 
                      : 'bg-blue-500/20 border-blue-500/50 text-blue-400 hover:bg-blue-500/30'
                  }`}
                >
                  {uploading ? (
                    <>
                      <div className="w-2 h-2 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-2.5 h-2.5" />
                      Upload
                    </>
                  )}
                </label>
              </div>
              {autoFilled && (
                <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
              )}
            </div>
          );
        }
        
        return (
          <div className="relative">
            <input
              type="text"
              value={displayValue}
              onChange={(e) => handleParamChange(input.name, e.target.value)}
              placeholder={input.description}
              disabled={autoFilled}
              className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
      
      case 'float':
      case 'number':
        return (
          <div className="relative">
            <input
              type="number"
              value={displayValue}
              min={input.constraints?.minimum}
              max={input.constraints?.maximum}
              step="any"
              onChange={(e) => handleParamChange(input.name, parseFloat(e.target.value))}
              disabled={autoFilled}
              className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
      
      case 'integer':
        return (
          <div className="relative">
            <input
              type="number"
              value={displayValue}
              min={input.constraints?.minimum}
              max={input.constraints?.maximum}
              onChange={(e) => handleParamChange(input.name, parseInt(e.target.value))}
              disabled={autoFilled}
              className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
      
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={displayValue}
              onChange={(e) => handleParamChange(input.name, e.target.checked)}
              disabled={autoFilled}
              className={`w-2.5 h-2.5 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1 ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="ml-1 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
      
      case 'array':
        if (input.constraints?.items?.enum) {
          return (
            <div className="space-y-0.5">
              {input.constraints.items.enum.map(option => (
                <label key={option} className="flex items-center space-x-1">
                  <input
                    type="checkbox"
                    checked={Array.isArray(displayValue) && displayValue.includes(option)}
                    onChange={(e) => {
                      const currentArray = Array.isArray(displayValue) ? displayValue : [];
                      const newArray = e.target.checked
                        ? [...currentArray, option]
                        : currentArray.filter(item => item !== option);
                      handleParamChange(input.name, newArray);
                    }}
                    disabled={autoFilled}
                    className={`w-2.5 h-2.5 text-blue-500 bg-gray-800 border-gray-700 rounded focus:ring-blue-500 focus:ring-1 ${
                      autoFilled ? 'opacity-60 cursor-not-allowed' : ''
                    }`}
                  />
                  <span className="text-xs text-gray-300">
                    {option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </label>
              ))}
              {autoFilled && (
                <Lock className="w-2.5 h-2.5 text-blue-400" />
              )}
            </div>
          );
        }
        return (
          <div className="relative">
            <input
              type="text"
              value={Array.isArray(displayValue) ? displayValue.join(', ') : ''}
              onChange={(e) => handleParamChange(input.name, e.target.value.split(',').map(s => s.trim()))}
              placeholder="Comma-separated values"
              disabled={autoFilled}
              className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
      
      default:
        return (
          <div className="relative">
            <input
              type="text"
              value={displayValue}
              onChange={(e) => handleParamChange(input.name, e.target.value)}
              disabled={autoFilled}
              className={`w-full px-1.5 py-0.5 rounded bg-gray-800/50 border border-gray-700 focus:border-blue-500 focus:outline-none text-xs ${
                autoFilled ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />
            {autoFilled && (
              <Lock className="absolute right-1.5 top-1/2 transform -translate-y-1/2 w-2.5 h-2.5 text-blue-400" />
            )}
          </div>
        );
    }
  };

  const getStepEmoji = (stepId) => {
    const emojiMap = {
      create_project: '📁',
      upload_file_to_project: '📤',
      download_project_zip: '📥',
      validate_project_token: '🔐',
      list_project_files: '📋',
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
    <div className="bg-gray-800/30 rounded border border-gray-700/50 overflow-hidden card-mini">
      <div className="p-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{getStepEmoji(step.step_id)}</span>
            <span className="font-medium text-xs text-white truncate content-wrap">
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
              className="p-0.5 rounded hover:red-500/20 text-red-400 transition-colors"
            >
              <Trash2 className="w-2.5 h-2.5" />
            </button>
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="border-t border-gray-700/50 p-1.5 space-y-1">
          {inputs.map((input) => {
            const autoFilled = isAutoFilled(input.name);
            return (
              <div key={input.name} className="space-y-0.5">
                <div className="flex items-center gap-1">
                  <label className="block text-xs font-medium text-gray-300 content-wrap">
                    {input.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    {input.required && <span className="text-red-400 ml-1">*</span>}
                  </label>
                  {autoFilled && (
                    <span className="text-xs text-blue-400 bg-blue-400/10 px-1 py-0.5 rounded">
                      Auto-filled
                    </span>
                  )}
                </div>
                {renderParamInput(input)}
                {input.description && (
                  <p className="text-xs text-gray-400 mt-0.5 content-wrap">{input.description}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StepConfiguration; 