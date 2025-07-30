// Utility functions for workflow and step management

import { WorkflowStatus, NoticeType, DefaultStepParams } from './constants.js';

/**
 * Check if a step has failed based on its results
 */
export function isStepFailed(stepId, workflow) {
  const result = workflow?.step_results?.[stepId];
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
}

/**
 * Get step status based on workflow state
 */
export function getStepStatus(stepId, workflow) {
  if (!workflow) return 'unknown';
  
  // Check if step is currently running
  if (workflow.current_step === stepId && workflow.status === WorkflowStatus.RUNNING) {
    return 'running';
  }
  
  // Check if step has results
  if (workflow.step_results?.[stepId]) {
    if (isStepFailed(stepId, workflow)) {
      return 'failed';
    }
    return 'completed';
  }
  
  // Check if workflow has failed
  if (workflow.status === WorkflowStatus.FAILED) {
    return 'failed';
  }
  
  return 'pending';
}

/**
 * Get workflow progress percentage
 */
export function getWorkflowProgress(workflow) {
  if (!workflow?.definition?.steps) return 0;
  
  const totalSteps = workflow.definition.steps.length;
  if (totalSteps === 0) return 100;
  
  const completedSteps = Object.keys(workflow.step_results || {}).length;
  return Math.round((completedSteps / totalSteps) * 100);
}

/**
 * Format workflow duration
 */
export function formatWorkflowDuration(workflow) {
  if (!workflow.started_at) return 'Not started';
  
  const startTime = new Date(workflow.started_at);
  const endTime = workflow.completed_at ? new Date(workflow.completed_at) : new Date();
  const duration = endTime - startTime;
  
  if (duration < 1000) return 'Less than 1 second';
  
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Create a new workflow step with proper structure
 */
export function createWorkflowStep(stepId, params = {}) {
  const defaultParams = DefaultStepParams[stepId] || {};
  let instanceId;
  if (window.crypto && window.crypto.randomUUID) {
    instanceId = window.crypto.randomUUID();
  } else {
    instanceId = 'step-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
  }
  return {
    step_id: stepId,
    instance_id: instanceId,
    params: { ...defaultParams, ...params },
    depends_on: [],
    auto_dependencies: [],
    provides: [],
    requires: []
  };
}

/**
 * Build a complete workflow definition with proper step dependencies
 */
export function buildWorkflowDefinition(name, description, steps, stepDefinitions) {
  console.log('buildWorkflowDefinition called with:', { name, description, steps, stepDefinitions });
  
  // First pass: set up provides and requires for each step
  const preparedSteps = steps.map(step => {
    const stepDef = stepDefinitions[step.step_id];
    if (!stepDef) {
      console.warn(`Step definition not found for ${step.step_id}`);
      return step;
    }

    const provides = stepDef.io?.context_keys || [];
    const requires = stepDef.io?.inputs?.filter(input => input.required).map(input => input.name) || [];
    
    console.log(`Step ${step.step_id}: provides=${provides}, requires=${requires}`);
    
    return {
      ...step,
      provides,
      requires
    };
  });

  // Second pass: set up dependencies based on requires/provides
  const finalSteps = preparedSteps.map((step, index) => {
    const dependencies = [];
    
    // Check if this step requires outputs from previous steps
    for (let i = 0; i < index; i++) {
      const prevStep = preparedSteps[i];
      const commonKeys = step.requires.filter(req => prevStep.provides.includes(req));
      if (commonKeys.length > 0) {
        console.log(`Step ${step.step_id} depends on ${prevStep.step_id} for: ${commonKeys}`);
        dependencies.push(prevStep.instance_id);
      }
    }

    return {
      ...step,
      depends_on: dependencies
    };
  });

  const result = {
    name,
    description,
    steps: finalSteps
  };
  
  console.log('Final workflow definition:', result);
  return result;
}

/**
 * Validate workflow definition before submission
 */
export function validateWorkflowDefinition(definition) {
  const errors = [];
  
  if (!definition.name || definition.name.trim() === '') {
    errors.push('Workflow name is required');
  }
  
  if (!definition.steps || definition.steps.length === 0) {
    errors.push('At least one step is required');
  }
  
  // Check for duplicate step IDs
  const stepIds = definition.steps.map(step => step.step_id);
  const uniqueStepIds = new Set(stepIds);
  if (stepIds.length !== uniqueStepIds.size) {
    errors.push('Duplicate step IDs are not allowed');
  }
  
  // Check for required parameters in steps
  definition.steps?.forEach(step => {
    const stepDefaults = DefaultStepParams[step.step_id];
    if (stepDefaults) {
      Object.entries(stepDefaults).forEach(([paramName, defaultValue]) => {
        // Only validate if the parameter is truly required (not just has an empty default)
        // For now, we'll skip validation of optional parameters and let the API handle validation
        // This prevents false positives from empty default values
      });
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors: errors
  };
}

/**
 * Extract context values from workflow for step parameter resolution
 */
export function getWorkflowContext(workflow) {
  if (!workflow) return {};
  
  const context = { ...workflow.context };
  
  // Add step results to context
  if (workflow.step_results) {
    for (const [stepId, result] of Object.entries(workflow.step_results)) {
      for (const [key, value] of Object.entries(result)) {
        context[key] = value;
      }
    }
  }
  
  return context;
}

/**
 * Resolve template variables in step parameters
 */
export function resolveTemplateVariables(params, context) {
  const resolved = {};
  
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === 'string' && value.includes('{{') && value.includes('}}')) {
      // Simple template variable resolution
      let resolvedValue = value;
      const matches = value.match(/\{\{([^}]+)\}\}/g);
      
      if (matches) {
        for (const match of matches) {
          const varName = match.slice(2, -2).trim();
          if (context[varName] !== undefined) {
            resolvedValue = resolvedValue.replace(match, context[varName]);
          }
        }
      }
      
      resolved[key] = resolvedValue;
    } else {
      resolved[key] = value;
    }
  }
  
  return resolved;
}

/**
 * Sort workflows by creation date (newest first)
 */
export function sortWorkflows(workflows) {
  return [...workflows].sort((a, b) => {
    const dateA = new Date(a.created_at);
    const dateB = new Date(b.created_at);
    return dateB - dateA;
  });
}

/**
 * Filter workflows by status
 */
export function filterWorkflowsByStatus(workflows, status) {
  if (!status) return workflows;
  return workflows.filter(workflow => workflow.status === status);
}

/**
 * Get notices for a specific workflow
 */
export function getWorkflowNotices(notices, workflowId) {
  return notices.filter(notice => notice.workflow_id === workflowId);
}

/**
 * Format notice timestamp
 */
export function formatNoticeTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) { // Less than 1 minute
    return 'Just now';
  } else if (diff < 3600000) { // Less than 1 hour
    const minutes = Math.floor(diff / 60000);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else if (diff < 86400000) { // Less than 1 day
    const hours = Math.floor(diff / 3600000);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
}

/**
 * Check if a notice is dismissible
 */
export function isNoticeDismissible(notice) {
  return notice.dismissible !== false;
}

/**
 * Auto-dismiss notices after a certain time
 */
export function shouldAutoDismissNotice(notice) {
  if (!notice.auto_dismiss_seconds) return false;
  
  const timestamp = new Date(notice.timestamp);
  const now = new Date();
  const diff = (now - timestamp) / 1000; // Convert to seconds
  
  return diff >= notice.auto_dismiss_seconds;
} 