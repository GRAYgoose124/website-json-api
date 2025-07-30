// Constants and enums matching the API models

export const NoticeType = {
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SUCCESS: 'success',
  DEBUG: 'debug'
};

export const NoticeSeverity = {
  CRITICAL: 50,
  HIGH: 40,
  MEDIUM: 30,
  LOW: 20,
  DEBUG: 10
};

export const WorkflowStatus = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

export const DataType = {
  STRING: 'string',
  INTEGER: 'integer',
  FLOAT: 'float',
  BOOLEAN: 'boolean',
  OBJECT: 'object',
  ARRAY: 'array',
  FILE: 'file',
  DATASET: 'dataset',
  MODEL: 'model',
  IMAGE: 'image',
  TEXT: 'text',
  JSON: 'json'
};

// Status colors for UI
export const StatusColors = {
  [WorkflowStatus.PENDING]: 'bg-yellow-100 text-yellow-800',
  [WorkflowStatus.RUNNING]: 'bg-blue-100 text-blue-800',
  [WorkflowStatus.COMPLETED]: 'bg-green-100 text-green-800',
  [WorkflowStatus.FAILED]: 'bg-red-100 text-red-800',
  [WorkflowStatus.CANCELLED]: 'bg-gray-100 text-gray-800'
};

// Notice type colors for UI
export const NoticeTypeColors = {
  [NoticeType.ERROR]: 'bg-red-100 text-red-800 border-red-200',
  [NoticeType.WARNING]: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  [NoticeType.INFO]: 'bg-blue-100 text-blue-800 border-blue-200',
  [NoticeType.SUCCESS]: 'bg-green-100 text-green-800 border-green-200',
  [NoticeType.DEBUG]: 'bg-gray-100 text-gray-800 border-gray-200'
};

// Step categories for filtering
export const StepCategories = {
  DATA_PROCESSING: 'data_processing',
  VISUALIZATION: 'visualization',
  MACHINE_LEARNING: 'ml',
  FILE_OPERATIONS: 'file_operations',
  PROJECT_MANAGEMENT: 'project_management',
  VALIDATION: 'validation',
  TRANSFORMATION: 'transformation'
};

// Default step parameters for common steps
export const DefaultStepParams = {
  create_project: {
    project_name: 'New Project',
    description: 'A new scientific project'
  },
  upload_file_to_project: {
    file_path: '',
    destination_path: '',
    project_token: ''
  },
  download_project_zip: {
    project_token: '',
    include_hidden: false
  },
  list_project_files: {
    project_token: '',
    recursive: false,
    include_hidden: false
  },
  data_processor: {
    input_data: '',
    processing_type: 'standard'
  },
  data_validator: {
    data_source: '',
    validation_rules: 'basic'
  },
  data_transformer: {
    input_data: '',
    transformation_type: 'normalize'
  }
};

// WebSocket message types
export const WebSocketMessageType = {
  NOTICES: 'notices',
  WORKFLOW_UPDATE: 'workflow_update',
  STEP_UPDATE: 'step_update',
  ERROR: 'error'
}; 