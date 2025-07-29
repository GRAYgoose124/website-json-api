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
        
        # Load definitions.py
        definitions_file = path / "definitions.py"
        if not definitions_file.exists():
            raise FileNotFoundError(f"definitions.py not found in {path}")
        
        self._load_definitions_file(definitions_file, path)
        
        # Load all Python modules in the config root
        self._load_all_modules(path)
        
        # Resolve callbacks
        self._resolve_callbacks(path)
        
        return self.step_definitions, self.step_implementations
    
    def _load_definitions_file(self, file_path: Path, root_path: Path):
        """Load step definitions from definitions.py"""
        try:
            # Load the module
            module_name = f"user_definitions_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.loaded_modules[module_name] = module
            
            # Extract STEP_DEFINITIONS
            if hasattr(module, 'STEP_DEFINITIONS'):
                self.step_definitions.update(module.STEP_DEFINITIONS)
            else:
                raise ValueError("STEP_DEFINITIONS not found in definitions.py")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load definitions file {file_path}: {e}")
    
    def _load_all_modules(self, root_path: Path):
        """Load all Python modules in the config root"""
        self._function_implementations = {}
        
        for py_file in root_path.glob("*.py"):
            if py_file.name in ["definitions.py", "__init__.py"]:
                continue  # Skip definitions.py (already loaded) and __init__.py
                
            try:
                # Load the module
                module_name = f"user_{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                self.loaded_modules[module_name] = module
                
                # Extract all async functions as potential step implementations
                for name, obj in inspect.getmembers(module):
                    if inspect.iscoroutinefunction(obj) and not name.startswith('_'):
                        # Store by module.function_name for callback resolution
                        function_key = f"{py_file.stem}.{name}"
                        self._function_implementations[function_key] = obj
                        
            except Exception as e:
                print(f"Warning: Failed to load module {py_file}: {e}")
    
    def _resolve_callbacks(self, root_path: Path):
        """Resolve callback references to actual functions"""
        for step_id, definition in self.step_definitions.items():
            if hasattr(definition, 'callback') and definition.callback:
                callback_path = definition.callback
                
                try:
                    # Handle "module.function_name" or "module.submodule.function_name" format
                    if '.' in callback_path:
                        # Split the callback path
                        parts = callback_path.split('.')
                        function_name = parts[-1]
                        
                        # Try exact match first (e.g., "steps.validate_data")
                        if callback_path in self._function_implementations:
                            self.step_implementations[step_id] = self._function_implementations[callback_path]
                            continue
                        
                        # Try module.function_name format
                        module_name = parts[0]
                        function_key = f"{module_name}.{function_name}"
                        if function_key in self._function_implementations:
                            self.step_implementations[step_id] = self._function_implementations[function_key]
                            continue
                        
                        # Try importing from the config root
                        if self.config_root:
                            # Try to find the module file
                            module_file = self.config_root / f"{module_name}.py"
                            if module_file.exists():
                                # The module should already be loaded, try to get the function
                                for loaded_module_name, module in self.loaded_modules.items():
                                    if loaded_module_name.endswith(f"_{module_name}"):
                                        if hasattr(module, function_name):
                                            self.step_implementations[step_id] = getattr(module, function_name)
                                            break
                        
                        # Try direct import as fallback
                        try:
                            module = __import__(callback_path, fromlist=[function_name])
                            if hasattr(module, function_name):
                                self.step_implementations[step_id] = getattr(module, function_name)
                                continue
                        except ImportError:
                            pass
                    
                    else:
                        # Just function name, look in all loaded modules
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
    
    def get_steps_by_category(self, category: str) -> Dict[str, StepDefinition]:
        """Get step definitions filtered by category"""
        return {
            step_id: definition 
            for step_id, definition in self.step_definitions.items()
            if definition.category == category
        }
    
    def get_steps_by_tag(self, tag: str) -> Dict[str, StepDefinition]:
        """Get step definitions filtered by tag"""
        return {
            step_id: definition 
            for step_id, definition in self.step_definitions.items()
            if tag in definition.tags
        }
    
    def search_steps(self, query: str) -> Dict[str, StepDefinition]:
        """Search step definitions by name, description, or tags"""
        query_lower = query.lower()
        results = {}
        
        for step_id, definition in self.step_definitions.items():
            if (query_lower in definition.name.lower() or
                query_lower in definition.description.lower() or
                any(query_lower in tag.lower() for tag in definition.tags)):
                results[step_id] = definition
        
        return results 