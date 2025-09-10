"""
Data processing and transformation utilities for import operations.
"""

import logging
from typing import Dict, Any, List, Optional, Set
import pandas as pd
from django.apps import apps
from django.db.models import Model, Q

from .exceptions import ImportErrorRow

logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data processing, transformations, and model operations."""
    
    def __init__(self, config: Dict[str, Any], transforms: Dict[str, callable]):
        self.config = config
        self.transforms = transforms
    
    def collect_lookup_values(self, df: pd.DataFrame) -> Dict[str, set]:
        """Scan configurations and gather unique source values for lookups."""
        lookup_values = {}
        for step_key in self.config["order"]:
            model_config = self.config["models"][step_key]
            
            if "lookup_fields" in model_config:
                for field_name, lookup_spec in model_config["lookup_fields"].items():
                    col = lookup_spec["column"]
                    if col and col in df.columns:
                        vals = set(df[col].dropna().unique().tolist())
                        # Use full model path to avoid conflicts between apps
                        model_path = lookup_spec['model']
                        if '.' not in model_path:
                            raise ValueError(f"Model path '{model_path}' must be fully qualified (app_label.ModelName)")
                        key = f"{model_path}__{lookup_spec['lookup_field']}"
                        lookup_values.setdefault(key, set()).update(vals)
        return lookup_values
    
    def prefetch_lookups(self, lookup_values: Dict[str, set]) -> Dict[str, Dict[Any, Model]]:
        """Prefetch lookup objects to avoid N+1 queries."""
        caches = {}
        for key, values in lookup_values.items():
            model_path, field = key.split("__", 1)
            model = self._get_model(model_path)
            
            # Check if the field is a database field or a property/attribute
            if self._is_model_field(model, field):
                # Database field - use ORM filtering
                q = {f"{field}__in": list(values)}
                qs = model.objects.filter(**q)
                map_ = {getattr(obj, field): obj for obj in qs}
            else:
                # Property/attribute - fetch all objects and filter in Python
                qs = model.objects.all()
                map_ = {}
                for obj in qs:
                    try:
                        attr_value = getattr(obj, field)
                        if attr_value in values:
                            map_[attr_value] = obj
                    except AttributeError:
                        # Attribute doesn't exist on this object
                        continue
            
            caches[key] = map_
        return caches
    
    def resolve_lookup(self, lookup_spec: Dict[str, Any], value, lookup_caches: Dict[str, Dict]) -> Optional[Model]:
        """Return existing object from cache or None."""
        model_path = lookup_spec["model"]
        if '.' not in model_path:
            raise ValueError(f"Model path '{model_path}' must be fully qualified (app_label.ModelName)")
        field = lookup_spec["lookup_field"]
        key = f"{model_path}__{field}"
        cache = lookup_caches.get(key, {})
        return cache.get(value)
    
    def apply_transform(self, transform_name: str, value):
        """Apply named transform function to value."""
        fn = self.transforms.get(transform_name)
        if not fn:
            raise ValueError(f"Transform '{transform_name}' not provided. Available transforms: {list(self.transforms.keys())}")
        try:
            return fn(value)
        except Exception as e:
            raise ValueError(f"Transform '{transform_name}' failed on value '{value}': {str(e)}")
    
    def prepare_kwargs_for_row(self, row, model_config: Dict[str, Any], 
                              created_objs_for_row: Dict[str, Model], 
                              lookup_caches: Dict[str, Dict]) -> Dict[str, Any]:
        """Prepare kwargs for model creation from row data."""
        kwargs = {}

        # Process computed fields FIRST - they may be needed for lookups and unique_by
        if "computed_fields" in model_config:
            for field_name, compute_spec in model_config["computed_fields"].items():
                try:
                    generator_name = compute_spec["generator"]
                    compute_mode = compute_spec.get("mode", "if_empty")  # "if_empty" or "always"
                    
                    generator_fn = self.transforms.get(generator_name)
                    if not generator_fn:
                        raise ImportErrorRow(f"Generator function '{generator_name}' not found", field_name=field_name)
                    
                    # For if_empty mode, get the current value from row first
                    current_value = None
                    if compute_mode == "if_empty" and "column" in compute_spec:
                        column_name = compute_spec["column"]
                        current_value = row.get(column_name)
                        # Clean pandas NaN values
                        if current_value is not None and str(current_value).lower() in ['nan', 'none']:
                            current_value = None
                    
                    # Check if we should compute the value
                    should_compute = False
                    if compute_mode == "always":
                        # Always generate (fully generated fields like student_id)
                        should_compute = True
                    elif compute_mode == "if_empty":
                        # Generate only if empty/missing (hybrid fields like email)
                        should_compute = current_value is None or current_value == ""
                    
                    if should_compute:
                        # Pass the current kwargs and created objects for computation
                        computed_value = generator_fn(
                            row_data=kwargs, 
                            created_objects=created_objs_for_row,
                            row=row
                        )
                        kwargs[field_name] = computed_value
                    else:
                        # Use the existing value from the column
                        kwargs[field_name] = current_value
                    
                except Exception as e:
                    raise ImportErrorRow(f"Computed field generation failed: {str(e)}", field_name=field_name)

        # Process direct columns (simple field -> column mapping)
        if "direct_columns" in model_config:
            for field_name, column_name in model_config["direct_columns"].items():
                try:
                    value = row.get(column_name)
                    # Clean pandas NaN values
                    if value is not None and str(value).lower() in ['nan', 'none']:
                        value = None
                    kwargs[field_name] = value
                except Exception as e:
                    raise ImportErrorRow(f"Error processing direct column: {str(e)}", field_name=field_name)

        # Process transformed columns (field -> {column, transform})
        if "transformed_columns" in model_config:
            for field_name, transform_spec in model_config["transformed_columns"].items():
                try:
                    column_name = transform_spec["column"]
                    transform_name = transform_spec["transform"]
                    value = row.get(column_name)
                    # Clean pandas NaN values before transformation
                    if value is not None and str(value).lower() in ['nan', 'none']:
                        value = None
                    if value is not None:
                        value = self.apply_transform(transform_name, value)
                    kwargs[field_name] = value
                except Exception as e:
                    raise ImportErrorRow(f"Transform failed: {str(e)}", field_name=field_name)

        # Process constant fields (field -> constant_value)
        if "constant_fields" in model_config:
            for field_name, constant_value in model_config["constant_fields"].items():
                kwargs[field_name] = constant_value

        # Process reference fields (field -> reference_key from previous step)
        if "reference_fields" in model_config:
            for field_name, reference_key in model_config["reference_fields"].items():
                try:
                    ref_obj = created_objs_for_row.get(reference_key)
                    
                    # Validate reference object exists
                    if ref_obj is None:
                        raise ImportErrorRow(f"Missing previous object '{reference_key}' - object was not created in earlier step", field_name=field_name)
                    
                    # Validate reference object is a valid Django model instance
                    if not hasattr(ref_obj, 'pk'):
                        raise ImportErrorRow(f"Invalid reference object '{reference_key}' - not a valid model instance", field_name=field_name)
                    
                    # Validate reference object has been saved (has a primary key)
                    if ref_obj.pk is None:
                        raise ImportErrorRow(f"Reference object '{reference_key}' has not been saved to database", field_name=field_name)
                    
                    kwargs[field_name] = ref_obj
                except ImportErrorRow:
                    raise
                except Exception as e:
                    raise ImportErrorRow(f"Reference validation error: {str(e)}", field_name=field_name)

        # Process lookup fields (field -> {column, model, lookup_field, create_if_missing})
        if "lookup_fields" in model_config:
            for field_name, lookup_spec in model_config["lookup_fields"].items():
                try:
                    column_name = lookup_spec["column"]
                    source_val = row.get(column_name)
                    
                    if source_val is None:
                        kwargs[field_name] = None
                    else:
                        found = self.resolve_lookup(lookup_spec, source_val, lookup_caches)
                        if found:
                            kwargs[field_name] = found
                        else:
                            if lookup_spec.get("create_if_missing", False):
                                try:
                                    lookup_model = self._get_model(lookup_spec["model"])
                                    lookup_obj, _ = lookup_model.objects.get_or_create(**{lookup_spec["lookup_field"]: source_val})
                                    # Use consistent cache key normalization
                                    cache_key = f"{lookup_spec['model']}__{lookup_spec['lookup_field']}"
                                    lookup_caches.setdefault(cache_key, {})[source_val] = lookup_obj
                                    kwargs[field_name] = lookup_obj
                                except Exception as e:
                                    raise ImportErrorRow(f"Failed to create missing lookup object: {str(e)}", field_name=field_name)
                            else:
                                raise ImportErrorRow(f"Lookup failed for {lookup_spec['model']} where {lookup_spec['lookup_field']}={source_val}", field_name=field_name)
                except ImportErrorRow:
                    raise
                except Exception as e:
                    raise ImportErrorRow(f"Lookup processing error: {str(e)}", field_name=field_name) from e

        # Validate required fields AFTER all field processing is complete
        self._validate_required_fields_from_kwargs(kwargs, model_config, row)
        
        return kwargs
    
    def prefetch_existing_objects(self, model_cls, unique_by: List[str], model_config: Dict[str, Any], df: pd.DataFrame):
        """Prefetch existing objects from DB based on unique keys."""
        unique_values = {}
        for idx, row in df.iterrows():
            tuple_key = []
            missing_value = False
            
            for model_field in unique_by:
                field_value = None
                found = False
                
                # Check in direct_columns
                if "direct_columns" in model_config:
                    if model_field in model_config["direct_columns"]:
                        column_name = model_config["direct_columns"][model_field]
                        field_value = row.get(column_name)
                        found = True
                
                # Check in transformed_columns (apply transform for lookup)
                if not found and "transformed_columns" in model_config:
                    if model_field in model_config["transformed_columns"]:
                        transform_spec = model_config["transformed_columns"][model_field]
                        column_name = transform_spec["column"]
                        raw_value = row.get(column_name)
                        if raw_value is not None:
                            try:
                                transform_name = transform_spec["transform"]
                                field_value = self.apply_transform(transform_name, raw_value)
                            except Exception as e:
                                # Transform failed - this is critical for unique_by fields, raise immediately
                                raise ImportErrorRow(f"Transform failed for unique_by field '{model_field}': {str(e)}") from e
                        else:
                            field_value = None
                        found = True
                
                # Check in constant_fields
                if not found and "constant_fields" in model_config:
                    if model_field in model_config["constant_fields"]:
                        field_value = model_config["constant_fields"][model_field]
                        found = True
                
                # Check in computed_fields
                if not found and "computed_fields" in model_config:
                    if model_field in model_config["computed_fields"]:
                        try:
                            compute_spec = model_config["computed_fields"][model_field]
                            generator_name = compute_spec["generator"]
                            compute_mode = compute_spec.get("mode", "if_empty")
                            
                            generator_fn = self.transforms.get(generator_name)
                            if not generator_fn:
                                raise ImportErrorRow(f"Generator function '{generator_name}' not found", field_name=model_field)
                            
                            # For prefetch, we need to compute the value for comparison
                            current_value = None
                            if compute_mode == "if_empty" and "column" in compute_spec:
                                column_name = compute_spec["column"]
                                current_value = row.get(column_name)
                                # Clean pandas NaN values
                                if current_value is not None and str(current_value).lower() in ['nan', 'none']:
                                    current_value = None
                            
                            should_compute = False
                            if compute_mode == "always":
                                should_compute = True
                            elif compute_mode == "if_empty":
                                should_compute = current_value is None or current_value == ""
                            
                            if should_compute:
                                # Compute the value for lookup
                                field_value = generator_fn(
                                    row_data={}, 
                                    created_objects={},
                                    row=row
                                )
                            else:
                                field_value = current_value
                            
                            found = True
                        except Exception as e:
                            # If computed field generation fails during prefetch, we can't lookup existing objects
                            # This is not necessarily an error - just means we can't find existing objects by this field
                            missing_value = True
                            break
                
                if not found:
                    missing_value = True
                    break
                    
                tuple_key.append(field_value)
            
            if not missing_value and all(v is not None for v in tuple_key):
                tup = tuple(tuple_key)
                unique_values.setdefault(tup, []).append(idx)

        q_objs = Q()
        for values in unique_values.keys():
            params = {}
            for field_name, val in zip(unique_by, values):
                params[field_name] = val
            q_objs |= Q(**params)

        existing_map = {}
        if q_objs:
            qs = model_cls.objects.filter(q_objs)
            for obj in qs:
                key = tuple(getattr(obj, f) for f in unique_by)
                existing_map[key] = obj
        return existing_map
    
    def find_existing_obj(self, existing_map: Dict, unique_by: List[str], kwargs: Dict[str, Any]):
        """Find existing object based on unique_by fields."""
        key = []
        for field in unique_by:
            if field in kwargs:
                key.append(kwargs[field])
            else:
                return None
        return existing_map.get(tuple(key))
    
    def _validate_required_fields_from_kwargs(self, kwargs: Dict[str, Any], model_config: Dict[str, Any], row: Dict[str, Any]) -> None:
        """Validate that required fields have values after all processing is complete."""
        if "required_fields" not in model_config:
            return
        
        missing_required = []
        for field_name in model_config["required_fields"]:
            # Check if the field is in kwargs and has a valid value
            field_value = kwargs.get(field_name)
            
            # Check if the field is empty/missing
            if field_value is None or field_value == "":
                missing_required.append(field_name)
        
        if missing_required:
            raise ImportErrorRow(f"Missing required fields: {', '.join(missing_required)}")
    
    
    def _get_model(self, model_path: str):
        """Get Django model from app.Model path."""
        return apps.get_model(model_path)
    
    def _is_model_field(self, model_cls, field_name: str) -> bool:
        """Check if field_name is a database field on the model."""
        try:
            model_cls._meta.get_field(field_name)
            return True
        except Exception:
            # Field doesn't exist in model's database fields
            return False