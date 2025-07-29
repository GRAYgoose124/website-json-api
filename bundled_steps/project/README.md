# Project Management Steps

This module provides a set of steps for secure project management in scientific workflows. Each workflow is isolated to its own project directory, and access is controlled through secure project tokens.

## Features

- **Secure Project Isolation**: Each workflow gets its own isolated project directory
- **Token-based Authentication**: Secure project tokens for access control
- **File Management**: Upload, download, and list files within projects
- **Automatic Context Management**: Project tokens are automatically filled in subsequent steps

## Steps Overview

### 1. Create Project (`create_project`)

Creates a new isolated project directory with a unique UUID and generates a secure project token.

**Inputs:**
- `project_name` (string): Name of the project
- `description` (string, optional): Project description

**Outputs:**
- `project_id` (string): UUID of the created project
- `project_path` (string): Full path to the project directory
- `project_token` (string): Hashed project token for future access

**Context Keys:** `project_id`, `project_path`, `project_token`

### 2. Upload File to Project (`upload_file_to_project`)

Uploads a local file to the specified project directory.

**Inputs:**
- `project_token` (string): Project token for authentication (auto-filled from context)
- `file_path` (string): Path to the local file to upload
- `destination_path` (string, optional): Destination path within the project
- `overwrite` (boolean, optional): Whether to overwrite existing files

**Outputs:**
- `uploaded_file_path` (string): Full path to the uploaded file
- `file_size` (integer): Size of the uploaded file in bytes
- `upload_status` (string): Status of the upload operation

**Context Keys:** `uploaded_file_path`, `file_size`, `upload_status`

### 3. Download Project as ZIP (`download_project_zip`)

Creates a ZIP archive of the project and provides download path.

**Inputs:**
- `project_token` (string): Project token for authentication (auto-filled from context)
- `include_hidden` (boolean, optional): Include hidden files and directories
- `compression_level` (integer, optional): ZIP compression level (0-9)

**Outputs:**
- `zip_file_path` (string): Path to the created ZIP file
- `zip_file_size` (integer): Size of the ZIP file in bytes
- `files_included` (integer): Number of files included in the ZIP

**Context Keys:** `zip_file_path`, `zip_file_size`, `files_included`

### 4. Validate Project Token (`validate_project_token`)

Validates a project token and returns project information.

**Inputs:**
- `project_token` (string): Project token to validate (auto-filled from context)

**Outputs:**
- `is_valid` (boolean): Whether the token is valid
- `project_id` (string): Project ID if token is valid
- `project_path` (string): Project path if token is valid
- `validation_message` (string): Validation result message

**Context Keys:** `is_valid`, `project_id`, `project_path`, `validation_message`

### 5. List Project Files (`list_project_files`)

Lists all files in the project directory.

**Inputs:**
- `project_token` (string): Project token for authentication (auto-filled from context)
- `recursive` (boolean, optional): List files recursively in subdirectories
- `include_hidden` (boolean, optional): Include hidden files and directories

**Outputs:**
- `files_list` (json): List of files with their metadata
- `total_files` (integer): Total number of files found
- `total_size` (integer): Total size of all files in bytes

**Context Keys:** `files_list`, `total_files`, `total_size`

## Security Features

### Project Isolation
- Each workflow gets its own isolated project directory
- Projects are created with UUID-based names to prevent conflicts
- No access to other projects or system directories

### Token-based Access Control
- Secure project tokens are generated using SHA-256 hashing
- Tokens include project ID, timestamp, and random UUID for uniqueness
- Tokens are validated before any project operations

### Automatic Context Management
- Project tokens are automatically filled in subsequent steps
- No need to manually pass tokens between steps
- Context values are securely managed by the workflow engine

## Usage Example

```python
# Step 1: Create a project
project_result = await create_project({
    'project_name': 'My Data Science Project',
    'description': 'A comprehensive data analysis workflow'
}, context)

# Step 2: Upload a file (project_token is auto-filled)
upload_result = await upload_file_to_project({
    'file_path': '/path/to/data.csv',
    'destination_path': 'data/input/data.csv'
}, context)

# Step 3: List files (project_token is auto-filled)
files_result = await list_project_files({
    'recursive': True
}, context)
```

## Workflow Integration

When used in a workflow, the `create_project` step automatically provides context values that are used by subsequent project steps:

1. `create_project` → provides `project_token`, `project_id`, `project_path`
2. `upload_file_to_project` → uses `project_token` from context
3. `list_project_files` → uses `project_token` from context
4. `download_project_zip` → uses `project_token` from context

The workflow engine automatically handles the dependency resolution and context flow between steps.

## File Structure

```
/projects/
├── {project-uuid-1}/
│   ├── .project_metadata.json
│   ├── data/
│   ├── scripts/
│   └── results/
├── {project-uuid-2}/
│   ├── .project_metadata.json
│   └── ...
└── downloads/
    ├── project1_20231201_143022.zip
    └── project2_20231201_143045.zip
```

Each project directory contains:
- `.project_metadata.json`: Project information and token hash
- User files and directories as uploaded/created
- Downloads directory for ZIP archives 