"""
Configuration validation for file import operations.
"""

import logging
from typing import Dict, Any, List, Set
from django.apps import apps

from .exceptions import ImportValidationError
from .enums import FileFormat

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates import configuration structure and dependencies."""
    
    def __init__(self, config: Dict[str, Any], transforms: Dict[str, callable]):
        self.config = config
        self.transforms = transforms
    
    def validate(self) -> None:
        """Run all validation checks."""
        self._validate_structure()
        self._validate_models()
        self._validate_field_types()
        self._validate_references()
        self._validate_transforms()
        logger.info("Configuration validation passed")
    
    def _validate_structure(self) -> None:
        """Validate basic configuration structure."""
        required_keys = ["file_format", "order", "models"]
        for key in required_keys:
            if key not in self.config:
                raise ImportValidationError(f"Missing required config key: '{key}'")
        
        # Validate file format
        file_format = self.config["file_format"].lower()
        if file_format not in [f.value for f in FileFormat]:
            raise ImportValidationError(f"Unsupported file format: {file_format}")
        
        # Validate order
        order = self.config["order"]
        if not order:
            raise ImportValidationError("Config 'order' cannot be empty")
        
        # Validate models exist in config
        models = self.config["models"]
        for step in order:
            if step not in models:
                raise ImportValidationError(f"Step '{step}' in order not found in models")
    
    def _validate_models(self) -> None:
        """Validate model configurations."""
        for step, model_config in self.config["models"].items():
            if "model" not in model_config:
                raise ImportValidationError(f"Missing 'model' in config for step '{step}'")
            
            # Validate model can be imported
            try:
                self._get_model(model_config["model"])
            except Exception as e:
                raise ImportValidationError(f"Cannot import model '{model_config['model']}' for step '{step}': {e}")
    
    def _validate_field_types(self) -> None:
        """Validate field type configurations."""
        field_types = ["direct_columns", "transformed_columns", "constant_fields", "reference_fields", "lookup_fields", "computed_fields"]
        
        for step, model_config in self.config["models"].items():
            has_any_fields = any(field_type in model_config for field_type in field_types)
            
            if not has_any_fields:
                raise ImportValidationError(f"Step '{step}' has no field mappings. Add at least one of: {field_types}")
            
            self._validate_transformed_columns(step, model_config)
            self._validate_lookup_fields(step, model_config)
            self._validate_computed_fields(step, model_config)
            self._validate_required_fields(step, model_config)
    
    def _validate_transformed_columns(self, step: str, model_config: Dict[str, Any]) -> None:
        """Validate transformed_columns structure."""
        if "transformed_columns" not in model_config:
            return
            
        for field_name, transform_spec in model_config["transformed_columns"].items():
            if not isinstance(transform_spec, dict):
                raise ImportValidationError(f"transformed_columns['{field_name}'] must be a dict with 'column' and 'transform' keys")
            if "column" not in transform_spec:
                raise ImportValidationError(f"transformed_columns['{field_name}'] missing 'column' key")
            if "transform" not in transform_spec:
                raise ImportValidationError(f"transformed_columns['{field_name}'] missing 'transform' key")
    
    def _validate_lookup_fields(self, step: str, model_config: Dict[str, Any]) -> None:
        """Validate lookup_fields structure."""
        if "lookup_fields" not in model_config:
            return
            
        for field_name, lookup_spec in model_config["lookup_fields"].items():
            if not isinstance(lookup_spec, dict):
                raise ImportValidationError(f"lookup_fields['{field_name}'] must be a dict")
            
            required_lookup_keys = ["column", "model", "lookup_field"]
            for key in required_lookup_keys:
                if key not in lookup_spec:
                    raise ImportValidationError(f"lookup_fields['{field_name}'] missing required key: '{key}'")
            
            # Validate lookup model can be imported
            try:
                self._get_model(lookup_spec["model"])
            except Exception as e:
                raise ImportValidationError(f"Cannot import lookup model '{lookup_spec['model']}' for field '{field_name}': {e}")
    
    def _validate_computed_fields(self, step: str, model_config: Dict[str, Any]) -> None:
        """Validate computed_fields structure."""
        if "computed_fields" not in model_config:
            return
            
        for field_name, compute_spec in model_config["computed_fields"].items():
            if not isinstance(compute_spec, dict):
                raise ImportValidationError(f"computed_fields['{field_name}'] must be a dict")
            
            if "generator" not in compute_spec:
                raise ImportValidationError(f"computed_fields['{field_name}'] missing required key: 'generator'")
            
            # Validate mode if provided
            mode = compute_spec.get("mode", "if_empty")
            valid_modes = ["if_empty", "always"]
            if mode not in valid_modes:
                raise ImportValidationError(f"computed_fields['{field_name}'] mode must be one of: {valid_modes}")
            
            # Note: Generator function validation happens in _validate_transforms
    
    def _validate_required_fields(self, step: str, model_config: Dict[str, Any]) -> None:
        """Validate required_fields structure."""
        if "required_fields" not in model_config:
            return
            
        required_fields = model_config["required_fields"]
        if not isinstance(required_fields, list):
            raise ImportValidationError(f"required_fields for step '{step}' must be a list")
        
        # Collect all available field names from field type configurations
        all_field_names = set()
        field_types = ["direct_columns", "transformed_columns", "constant_fields", "reference_fields", "lookup_fields", "computed_fields"]
        
        for field_type in field_types:
            if field_type in model_config:
                all_field_names.update(model_config[field_type].keys())
        
        # Check that all required fields are defined in some field type
        for field_name in required_fields:
            if field_name not in all_field_names:
                raise ImportValidationError(f"required_fields for step '{step}' contains undefined field '{field_name}'. Available fields: {sorted(all_field_names)}")
    
    def _validate_references(self) -> None:
        """Validate reference_fields point to valid steps."""
        order = self.config["order"]
        
        for step, model_config in self.config["models"].items():
            if "reference_fields" not in model_config:
                continue
                
            for field_name, reference_key in model_config["reference_fields"].items():
                if reference_key not in order:
                    raise ImportValidationError(f"reference_fields['{field_name}'] references unknown step '{reference_key}'")
                
                current_step_index = order.index(step)
                reference_step_index = order.index(reference_key)
                if reference_step_index >= current_step_index:
                    raise ImportValidationError(f"reference_fields['{field_name}'] references step '{reference_key}' that comes later in order")
    
    def _validate_transforms(self) -> None:
        """Validate that all required transform functions are provided."""
        missing_transforms = self.get_missing_transforms()
        if missing_transforms:
            raise ImportValidationError(
                f"Missing required transform functions: {missing_transforms}. "
                f"Available transforms: {list(self.transforms.keys())}"
            )
    
    def get_missing_transforms(self) -> List[str]:
        """Get list of missing transform function names."""
        required_transforms = set()
        
        for step_key, model_config in self.config.get("models", {}).items():
            # Check transformed_columns
            if "transformed_columns" in model_config:
                for transform_spec in model_config["transformed_columns"].values():
                    required_transforms.add(transform_spec["transform"])
            
            # Check computed_fields generators
            if "computed_fields" in model_config:
                for compute_spec in model_config["computed_fields"].values():
                    required_transforms.add(compute_spec["generator"])
        
        available_transforms = set(self.transforms.keys())
        missing_transforms = required_transforms - available_transforms
        
        return sorted(missing_transforms)
    
    def get_all_columns(self) -> Set[str]:
        """Extract all column names from the configuration."""
        columns = set()
        
        for step_key in self.config["order"]:
            model_config = self.config["models"][step_key]
            
            # Direct columns
            if "direct_columns" in model_config:
                columns.update(model_config["direct_columns"].values())
            
            # Transformed columns
            if "transformed_columns" in model_config:
                for field_spec in model_config["transformed_columns"].values():
                    columns.add(field_spec["column"])
            
            # Lookup fields
            if "lookup_fields" in model_config:
                for field_spec in model_config["lookup_fields"].values():
                    columns.add(field_spec["column"])
            
            # Computed fields with "if_empty" mode (hybrid fields that can be provided or generated)
            if "computed_fields" in model_config:
                for field_name, compute_spec in model_config["computed_fields"].items():
                    mode = compute_spec.get("mode", "if_empty")
                    # Only include columns for "if_empty" mode fields that have a column specified
                    if mode == "if_empty" and "column" in compute_spec:
                        columns.add(compute_spec["column"])
                    # Skip "always" mode fields - they are fully generated and don't need file columns
        
        return columns
    
    def _get_model(self, model_path: str):
        """Get Django model from app.Model path."""
        return apps.get_model(model_path)