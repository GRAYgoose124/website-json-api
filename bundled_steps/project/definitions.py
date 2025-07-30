from app.models import StepDefinition, StepIO, IOSchema, DataType


STEP_DEFINITIONS = {
    "create_project": StepDefinition(
        id="create_project",
        name="Create Project",
        description="Creates a new project directory with UUID and generates a project token",
        callback="steps.create_project",
        category="project_management",
        tags=["project", "creation", "uuid"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="project_name",
                    type=DataType.STRING,
                    description="Name of the project",
                    required=True,
                    default="New Project"
                ),
                IOSchema(
                    name="description",
                    type=DataType.STRING,
                    description="Optional project description",
                    required=False,
                    default=""
                )
            ],
            outputs=[
                IOSchema(
                    name="project_id",
                    type=DataType.STRING,
                    description="UUID of the created project",
                    required=True
                ),
                IOSchema(
                    name="project_path",
                    type=DataType.STRING,
                    description="Full path to the project directory",
                    required=True
                ),
                IOSchema(
                    name="project_path_relative",
                    type=DataType.STRING,
                    description="Relative path to the project directory (safe for API exposure)",
                    required=True
                ),
                IOSchema(
                    name="project_token",
                    type=DataType.STRING,
                    description="Hashed project token for future access",
                    required=True
                )
            ],
            context_keys=["project_id", "project_path", "project_path_relative", "project_token"]
        )
    ),
    
    "upload_file_to_project": StepDefinition(
        id="upload_file_to_project",
        name="Upload File to Project",
        description="Uploads a local file to the specified project directory",
        callback="steps.upload_file_to_project",
        category="project_management",
        tags=["project", "upload", "file"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="project_token",
                    type=DataType.STRING,
                    description="Project token for authentication",
                    required=True
                ),
                IOSchema(
                    name="file_path",
                    type=DataType.STRING,
                    description="Path to the local file to upload",
                    required=True
                ),
                IOSchema(
                    name="destination_path",
                    type=DataType.STRING,
                    description="Destination path within the project (relative to project root)",
                    required=False,
                    default=""
                ),
                IOSchema(
                    name="overwrite",
                    type=DataType.BOOLEAN,
                    description="Whether to overwrite existing files",
                    required=False,
                    default=False
                )
            ],
            outputs=[
                IOSchema(
                    name="uploaded_file_path",
                    type=DataType.STRING,
                    description="Full path to the uploaded file in the project",
                    required=True
                ),
                IOSchema(
                    name="file_size",
                    type=DataType.INTEGER,
                    description="Size of the uploaded file in bytes",
                    required=True
                ),
                IOSchema(
                    name="upload_status",
                    type=DataType.STRING,
                    description="Status of the upload operation",
                    required=True
                )
            ],
            context_keys=["uploaded_file_path", "file_size", "upload_status"]
        )
    ),
    
    "download_project_zip": StepDefinition(
        id="download_project_zip",
        name="Download Project as ZIP",
        description="Creates a ZIP archive of the project and provides download path",
        callback="steps.download_project_zip",
        category="project_management",
        tags=["project", "download", "zip"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="project_token",
                    type=DataType.STRING,
                    description="Project token for authentication",
                    required=True
                ),
                IOSchema(
                    name="uploaded_file_path",
                    type=DataType.STRING,
                    description="Path to uploaded file (ensures files are uploaded before downloading)",
                    required=False
                ),
                IOSchema(
                    name="include_hidden",
                    type=DataType.BOOLEAN,
                    description="Include hidden files and directories in the ZIP",
                    required=False,
                    default=False
                ),
                IOSchema(
                    name="compression_level",
                    type=DataType.INTEGER,
                    description="ZIP compression level (0-9)",
                    required=False,
                    default=6,
                    constraints={"minimum": 0, "maximum": 9}
                )
            ],
            outputs=[
                IOSchema(
                    name="zip_file_path",
                    type=DataType.STRING,
                    description="Path to the created ZIP file",
                    required=True
                ),
                IOSchema(
                    name="zip_file_size",
                    type=DataType.INTEGER,
                    description="Size of the ZIP file in bytes",
                    required=True
                ),
                IOSchema(
                    name="files_included",
                    type=DataType.INTEGER,
                    description="Number of files included in the ZIP",
                    required=True
                ),
                IOSchema(
                    name="download_url",
                    type=DataType.STRING,
                    description="URL for downloading the ZIP file",
                    required=True
                ),
                IOSchema(
                    name="download_filename",
                    type=DataType.STRING,
                    description="Filename of the ZIP file for download",
                    required=True
                )
            ],
            context_keys=["zip_file_path", "zip_file_size", "files_included", "download_url", "download_filename"]
        )
    ),
    
    "validate_project_token": StepDefinition(
        id="validate_project_token",
        name="Validate Project Token",
        description="Validates a project token and returns project information",
        callback="steps.validate_project_token",
        category="project_management",
        tags=["project", "validation", "authentication"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="project_token",
                    type=DataType.STRING,
                    description="Project token to validate",
                    required=True
                )
            ],
            outputs=[
                IOSchema(
                    name="is_valid",
                    type=DataType.BOOLEAN,
                    description="Whether the token is valid",
                    required=True
                ),
                IOSchema(
                    name="project_id",
                    type=DataType.STRING,
                    description="Project ID if token is valid",
                    required=False
                ),
                IOSchema(
                    name="project_path",
                    type=DataType.STRING,
                    description="Project path if token is valid",
                    required=False
                ),
                IOSchema(
                    name="project_path_relative",
                    type=DataType.STRING,
                    description="Relative project path if token is valid (safe for API exposure)",
                    required=False
                ),
                IOSchema(
                    name="validation_message",
                    type=DataType.STRING,
                    description="Validation result message",
                    required=True
                )
            ],
            context_keys=["is_valid", "project_id", "project_path", "project_path_relative", "validation_message"]
        )
    ),
    
    "list_project_files": StepDefinition(
        id="list_project_files",
        name="List Project Files",
        description="Lists all files in the project directory",
        callback="steps.list_project_files",
        category="project_management",
        tags=["project", "files", "listing"],
        io=StepIO(
            inputs=[
                IOSchema(
                    name="project_token",
                    type=DataType.STRING,
                    description="Project token for authentication",
                    required=True
                ),
                IOSchema(
                    name="recursive",
                    type=DataType.BOOLEAN,
                    description="List files recursively in subdirectories",
                    required=False,
                    default=True
                ),
                IOSchema(
                    name="include_hidden",
                    type=DataType.BOOLEAN,
                    description="Include hidden files and directories",
                    required=False,
                    default=False
                )
            ],
            outputs=[
                IOSchema(
                    name="files_list",
                    type=DataType.JSON,
                    description="List of files with their metadata",
                    required=True
                ),
                IOSchema(
                    name="total_files",
                    type=DataType.INTEGER,
                    description="Total number of files found",
                    required=True
                ),
                IOSchema(
                    name="total_size",
                    type=DataType.INTEGER,
                    description="Total size of all files in bytes",
                    required=True
                )
            ],
            context_keys=["files_list", "total_files", "total_size"]
        )
    )
} 