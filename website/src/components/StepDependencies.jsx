import React from 'react';
import { ArrowRight, ArrowDown, ArrowUp, Link, Unlink, Info } from 'lucide-react';

const StepDependencies = ({ step, allSteps, dependencies, contextFlow }) => {
  const stepDefinition = allSteps[step.step_id];
  
  if (!stepDefinition) {
    return (
      <div className="text-xs text-gray-400 p-2">
        Step definition not found
      </div>
    );
  }

  const getDependencies = () => {
    if (!dependencies) return [];
    return dependencies[step.step_id] || [];
  };

  const getDependents = () => {
    if (!dependencies) return [];
    return Object.entries(dependencies)
      .filter(([_, deps]) => deps.includes(step.step_id))
      .map(([stepId, _]) => stepId);
  };

  const getContextFlow = () => {
    if (!contextFlow) return {};
    return contextFlow[step.step_id] || {};
  };

  const dependenciesList = getDependencies();
  const dependentsList = getDependents();
  const contextFlowData = getContextFlow();

  return (
    <div className="space-y-3 text-xs">
      {/* IO Information */}
      <div className="bg-gray-800/50 rounded-md p-2">
        <div className="flex items-center gap-1 mb-2 text-blue-400">
          <Info className="w-3 h-3" />
          <span className="font-medium">Inputs & Outputs</span>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          {/* Inputs */}
          <div>
            <div className="text-gray-400 mb-1">Inputs:</div>
            {stepDefinition.io?.inputs?.length > 0 ? (
              <div className="space-y-1">
                {stepDefinition.io.inputs.map((input, idx) => (
                  <div key={idx} className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${
                      input.required ? 'bg-red-400' : 'bg-yellow-400'
                    }`} />
                    <span className="text-gray-300">{input.name}</span>
                    <span className="text-gray-500">({input.type})</span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-gray-500">None</span>
            )}
          </div>
          
          {/* Outputs */}
          <div>
            <div className="text-gray-400 mb-1">Outputs:</div>
            {stepDefinition.io?.outputs?.length > 0 ? (
              <div className="space-y-1">
                {stepDefinition.io.outputs.map((output, idx) => (
                  <div key={idx} className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-green-400" />
                    <span className="text-gray-300">{output.name}</span>
                    <span className="text-gray-500">({output.type})</span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-gray-500">None</span>
            )}
          </div>
        </div>
        
        {/* Context Keys */}
        {stepDefinition.io?.context_keys?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <div className="text-gray-400 mb-1">Provides to Context:</div>
            <div className="flex flex-wrap gap-1">
              {stepDefinition.io.context_keys.map((key, idx) => (
                <span key={idx} className="px-1.5 py-0.5 bg-blue-500/20 text-blue-300 rounded text-xs">
                  {key}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Dependencies */}
      <div className="bg-gray-800/50 rounded-md p-2">
        <div className="flex items-center gap-1 mb-2 text-orange-400">
          <ArrowDown className="w-3 h-3" />
          <span className="font-medium">Dependencies</span>
        </div>
        
        {dependenciesList.length > 0 ? (
          <div className="space-y-1">
            {dependenciesList.map((depId, idx) => {
              const depStep = allSteps[depId];
              return (
                <div key={idx} className="flex items-center gap-1 text-gray-300">
                  <Link className="w-3 h-3 text-orange-400" />
                  <span className="font-medium">{depId}</span>
                  {depStep && (
                    <span className="text-gray-500">({depStep.name})</span>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <span className="text-gray-500">No dependencies</span>
        )}
      </div>

      {/* Dependents */}
      <div className="bg-gray-800/50 rounded-md p-2">
        <div className="flex items-center gap-1 mb-2 text-green-400">
          <ArrowUp className="w-3 h-3" />
          <span className="font-medium">Dependents</span>
        </div>
        
        {dependentsList.length > 0 ? (
          <div className="space-y-1">
            {dependentsList.map((depId, idx) => {
              const depStep = allSteps[depId];
              return (
                <div key={idx} className="flex items-center gap-1 text-gray-300">
                  <Link className="w-3 h-3 text-green-400" />
                  <span className="font-medium">{depId}</span>
                  {depStep && (
                    <span className="text-gray-500">({depStep.name})</span>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <span className="text-gray-500">No dependents</span>
        )}
      </div>

      {/* Context Flow */}
      {Object.keys(contextFlowData).length > 0 && (
        <div className="bg-gray-800/50 rounded-md p-2">
          <div className="flex items-center gap-1 mb-2 text-purple-400">
            <ArrowRight className="w-3 h-3" />
            <span className="font-medium">Context Flow</span>
          </div>
          
          <div className="space-y-1">
            {Object.entries(contextFlowData).map(([contextKey, providerStep], idx) => (
              <div key={idx} className="flex items-center gap-1 text-gray-300">
                <span className="text-purple-400">{contextKey}</span>
                <ArrowRight className="w-3 h-3 text-gray-500" />
                <span className="font-medium">{providerStep}</span>
                {allSteps[providerStep] && (
                  <span className="text-gray-500">({allSteps[providerStep].name})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manual Dependencies */}
      {step.depends_on?.length > 0 && (
        <div className="bg-gray-800/50 rounded-md p-2">
          <div className="flex items-center gap-1 mb-2 text-yellow-400">
            <Unlink className="w-3 h-3" />
            <span className="font-medium">Manual Dependencies</span>
          </div>
          
          <div className="space-y-1">
            {step.depends_on.map((depId, idx) => {
              const depStep = allSteps[depId];
              return (
                <div key={idx} className="flex items-center gap-1 text-gray-300">
                  <Unlink className="w-3 h-3 text-yellow-400" />
                  <span className="font-medium">{depId}</span>
                  {depStep && (
                    <span className="text-gray-500">({depStep.name})</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default StepDependencies; 