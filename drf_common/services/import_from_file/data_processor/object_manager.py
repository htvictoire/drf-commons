"""
Object management utilities for data processing operations.
"""

import logging
from typing import Any, Dict, List

from django.db.models import Q

import pandas as pd

from ..core.exceptions import ImportErrorRow

logger = logging.getLogger(__name__)


class ObjectManager:
    """Handles existing object prefetching and management."""

    def __init__(self, transforms: Dict[str, callable]):
        self.transforms = transforms or {}

    def apply_transform(self, transform_name: str, value):
        """Apply named transform function to value."""
        fn = self.transforms.get(transform_name)
        if not fn:
            raise ValueError(
                f"Transform '{transform_name}' not provided. Available transforms: {list(self.transforms.keys())}"
            )
        try:
            return fn(value)
        except Exception as e:
            raise ValueError(
                f"Transform '{transform_name}' failed on value '{value}': {str(e)}"
            )

    def prefetch_existing_objects(
        self,
        model_cls,
        unique_by: List[str],
        model_config: Dict[str, Any],
        df: pd.DataFrame,
    ):
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
                        transform_spec = model_config["transformed_columns"][
                            model_field
                        ]
                        column_name = transform_spec["column"]
                        raw_value = row.get(column_name)
                        if raw_value is not None:
                            try:
                                transform_name = transform_spec["transform"]
                                field_value = self.apply_transform(
                                    transform_name, raw_value
                                )
                            except Exception as e:
                                # Transform failed - this is critical for unique_by fields, raise immediately
                                raise ImportErrorRow(
                                    f"Transform failed for unique_by field '{model_field}': {str(e)}"
                                ) from e
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
                                raise ImportErrorRow(
                                    f"Generator function '{generator_name}' not found",
                                    field_name=model_field,
                                )

                            # For prefetch, we need to compute the value for comparison
                            current_value = None
                            if compute_mode == "if_empty" and "column" in compute_spec:
                                column_name = compute_spec["column"]
                                current_value = row.get(column_name)
                                # Clean pandas NaN values
                                if current_value is not None and str(
                                    current_value
                                ).lower() in ["nan", "none"]:
                                    current_value = None

                            should_compute = False
                            if compute_mode == "always":
                                should_compute = True
                            elif compute_mode == "if_empty":
                                should_compute = (
                                    current_value is None or current_value == ""
                                )

                            if should_compute:
                                # Compute the value for lookup
                                field_value = generator_fn(
                                    row_data={}, created_objects={}, row=row
                                )
                            else:
                                field_value = current_value

                            found = True
                        except Exception:
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

    def find_existing_obj(
        self, existing_map: Dict, unique_by: List[str], kwargs: Dict[str, Any]
    ):
        """Find existing object based on unique_by fields."""
        key = []
        for field in unique_by:
            if field in kwargs:
                key.append(kwargs[field])
            else:
                return None
        return existing_map.get(tuple(key))
