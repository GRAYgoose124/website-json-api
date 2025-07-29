import os
import sys
import importlib.util
import inspect
from typing import Dict, Any, Tuple, List
from pathlib import Path
from .models import StepDefinition

class StepLoader:
    """Dynamically loads step definitions and implementations from a custom path"""
    
    def __init__(self, config_root: str = None):
        self.config_root = Path(config_root).resolve() if config_root else None
        self.loaded_modules = {}
        self.step_definitions = {}
        self.step_implementations = {}
    
    def load_from_path(self, path: str) -> Tuple[Dict[str, StepDefinition], Dict[str, Any]]:
        """
        Load step definitions and implementations from a given path
        
        Args:
            path: Path to the directory containing step definitions
            
        Returns:
            Tuple of (step_definitions, step_implementations)
        """
        path = Path(path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Step definitions path not found: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Step definitions path must be a directory: {path}")
        
        # Add the path to Python path for imports
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
        
        # Look for step definition files
        step_files = self._find_step_files(path)
        
        if not step_files:
            raise ValueError(f"No step definition files found in {path}")
        
        # Load each step file
        for step_file in step_files:
            self._load_step_file(step_file, path)
        
        # Resolve callbacks and load implementations
        self._resolve_callbacks(path)
        
        return self.step_definitions, self.step_implementations
    
    def _find_step_files(self, path: Path) -> List[Path]:
        """Find all Python files that might contain step definitions"""
        step_files = []
        
        # Look for common patterns
        patterns = [
            "definitions.py",
            "steps.py",
            "step_definitions.py", 
            "workflow_steps.py",
            "*.steps.py"
        ]
        
        for pattern in patterns:
            step_files.extend(path.glob(pattern))
        
        # Also look for any Python file that might contain step definitions
        for py_file in path.glob("*.py"):
            if py_file.name not in ["__init__.py"]:
                step_files.append(py_file)
        
        return list(set(step_files))  # Remove duplicates
    
    def _load_step_file(self, file_path: Path, root_path: Path):
        """Load step definitions and implementations from a single file"""
        try:
            # Load the module
            module_name = f"user_steps_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.loaded_modules[module_name] = module
            
            # Extract step definitions from various possible sources
            self._extract_step_definitions(module, root_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load step file {file_path}: {e}")
    
    def _extract_step_definitions(self, module, root_path: Path):
        """Extract step definitions from a module"""
        # Look for different possible definition sources
        definition_sources = [
            'STEP_DEFINITIONS',
            'get_step_definitions',
            'step_definitions'
        ]
        
        for source_name in definition_sources:
            if hasattr(module, source_name):
                source = getattr(module, source_name)
                
                if callable(source):
                    # It's a function, call it
                    definitions = source()
                else:
                    # It's a variable
                    definitions = source
                
                if isinstance(definitions, dict):
                    self.step_definitions.update(definitions)
                    break
    
    def _resolve_callbacks(self, root_path: Path):
        """Resolve callback references to actual functions"""
        for step_id, definition in self.step_definitions.items():
            if hasattr(definition, 'callback') and definition.callback:
                callback_path = definition.callback
                
                try:
                    # Handle different callback formats
                    if callback_path.startswith('.'):
                        # Relative import from config root (e.g., ".steps.validate_data")
                        module_path = callback_path.lstrip('.')
                        module_parts = module_path.split('.')
                        function_name = module_parts[-1]
                        module_path = '.'.join(module_parts[:-1])
                        
                        # Try to load the module from the config root
                        if self.config_root:
                            module_file = self.config_root / f"{module_path.replace('.', '/')}.py"
                            if module_file.exists():
                                spec = importlib.util.spec_from_file_location(f"user_{module_path}", module_file)
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                
                                if hasattr(module, function_name):
                                    self.step_implementations[step_id] = getattr(module, function_name)
                                    continue
                    
                    elif '.' in callback_path:
                        # Full module path (e.g., "custom_steps.steps.validate_data")
                        module_parts = callback_path.split('.')
                        function_name = module_parts[-1]
                        module_path = '.'.join(module_parts[:-1])
                        
                        # Try importing from the config root
                        if self.config_root:
                            # Convert module path to file path
                            module_file = self.config_root / f"{module_path.replace('.', '/')}.py"
                            if module_file.exists():
                                spec = importlib.util.spec_from_file_location(f"user_{module_path}", module_file)
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                
                                if hasattr(module, function_name):
                                    self.step_implementations[step_id] = getattr(module, function_name)
                                    continue
                        
                        # Try direct import
                        try:
                            module = __import__(module_path, fromlist=[function_name])
                            if hasattr(module, function_name):
                                self.step_implementations[step_id] = getattr(module, function_name)
                                continue
                        except ImportError:
                            pass
                    
                    else:
                        # Just function name, look in loaded modules
                        for module_name, module in self.loaded_modules.items():
                            if hasattr(module, callback_path):
                                self.step_implementations[step_id] = getattr(module, callback_path)
                                break
                    
                except Exception as e:
                    print(f"Warning: Could not resolve callback '{callback_path}' for step '{step_id}': {e}")
    
    def get_step_definitions(self) -> Dict[str, StepDefinition]:
        """Get all loaded step definitions"""
        return self.step_definitions.copy()
    
    def get_step_implementations(self) -> Dict[str, Any]:
        """Get all loaded step implementations"""
        return self.step_implementations.copy()
    
    def validate_steps(self) -> List[str]:
        """Validate that all step definitions have implementations and vice versa"""
        errors = []
        
        # Check that all definitions have implementations
        for step_id in self.step_definitions:
            if step_id not in self.step_implementations:
                errors.append(f"Step definition '{step_id}' has no implementation (callback not resolved)")
        
        # Check that all implementations have definitions
        for step_id in self.step_implementations:
            if step_id not in self.step_definitions:
                errors.append(f"Step implementation '{step_id}' has no definition")
        
        return errors 