from typing import Dict, Any, Optional
from datetime import datetime, UTC
import uuid
import hashlib
from pathlib import Path

class ProjectManager:
    """Manages project isolation and security"""
    
    def __init__(self, projects_root: str = None):
        self.projects_root = projects_root
        self.project_tokens: Dict[str, Dict[str, Any]] = {}  # token_hash -> project_info
    
    def create_project(self, project_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new isolated project"""
        # Generate project UUID
        project_id = str(uuid.uuid4())
        
        # Create project directory (isolated)
        project_path = self.projects_root / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Generate secure project token
        raw_token = f"{project_id}_{datetime.now(UTC).isoformat()}_{uuid.uuid4()}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Store project info with relative path
        project_info = {
            'project_id': project_id,
            'project_path': str(project_path),
            'project_path_relative': str(project_path.relative_to(self.projects_root)),
            'project_name': project_name,
            'description': description,
            'created_at': datetime.now(UTC).isoformat(),
            'raw_token': raw_token
        }
        self.project_tokens[token_hash] = project_info
        
        # Create project metadata file
        metadata = {
            'project_id': project_id,
            'project_name': project_name,
            'description': description,
            'created_at': project_info['created_at'],
            'token_hash': token_hash
        }
        
        metadata_path = project_path / '.project_metadata.json'
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'project_id': project_id,
            'project_path': str(project_path),
            'project_path_relative': str(project_path.relative_to(self.projects_root)),
            'project_token': token_hash
        }
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a project token and return project info"""
        return self.project_tokens.get(token)
    
    def get_project_path(self, token: str) -> Optional[str]:
        """Get project path for a valid token"""
        project_info = self.validate_token(token)
        return project_info['project_path'] if project_info else None
    
    def get_project_path_relative(self, token: str) -> Optional[str]:
        """Get relative project path for a valid token (safe for API exposure)"""
        project_info = self.validate_token(token)
        return project_info.get('project_path_relative') if project_info else None

