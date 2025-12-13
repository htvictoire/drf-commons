"""
Field processing utilities for data processing operations.
"""

import logging
from typing import Any, Dict

from django.db.models import Model

from ..core.exceptions import ImportErrorRow

logger = logging.getLogger(__name__)


class FieldProcessor:
    """Handles field processing and transformations."""

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

    def process_computed_fields(
        self,
        row: Dict[str, Any],
        model_config: Dict[str, Any],
        created_objs_for_row: Dict[str, Model],
        kwargs: Dict[str, Any],
    ) -> None:
        """Process computed fields and add to kwargs."""
        if "computed_fields" not in model_config:
            return

        for field_name, compute_spec in model_config["computed_fields"].items():
            try:
                generator_name = compute_spec["generator"]
                compute_mode = compute_spec.get(
                    "mode", "if_empty"
                )  # "if_empty" or "always"

                generator_fn = self.transforms.get(generator_name)
                if not generator_fn:
                    raise ImportErrorRow(
                        f"Generator function '{generator_name}' not found",
                        field_name=field_name,
                    )

                # For if_empty mode, get the current value from row first
                current_value = None
                if compute_mode == "if_empty" and "column" in compute_spec:
                    column_name = compute_spec["column"]
                    current_value = row.get(column_name)
                    # Clean pandas NaN values
                    if current_value is not None and str(current_value).lower() in [
                        "nan",
                        "none",
                    ]:
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
                        row_data=kwargs, created_objects=created_objs_for_row, row=row
                    )
                    kwargs[field_name] = computed_value
                else:
                    # Use the existing value from the column
                    kwargs[field_name] = current_value

            except Exception as e:
                raise ImportErrorRow(
                    f"Computed field generation failed: {str(e)}", field_name=field_name
                )

    def process_direct_columns(
        self, row: Dict[str, Any], model_config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> None:
        """Process direct columns (simple field -> column mapping)."""
        if "direct_columns" not in model_config:
            return

        for field_name, column_name in model_config["direct_columns"].items():
            try:
                value = row.get(column_name)
                # Clean pandas NaN values
                if value is not None and str(value).lower() in ["nan", "none"]:
                    value = None
                kwargs[field_name] = value
            except Exception as e:
                raise ImportErrorRow(
                    f"Error processing direct column: {str(e)}", field_name=field_name
                )

    def process_transformed_columns(
        self, row: Dict[str, Any], model_config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> None:
        """Process transformed columns (field -> {column, transform})."""
        if "transformed_columns" not in model_config:
            return

        for field_name, transform_spec in model_config["transformed_columns"].items():
            try:
                column_name = transform_spec["column"]
                transform_name = transform_spec["transform"]
                value = row.get(column_name)
                # Clean pandas NaN values before transformation
                if value is not None and str(value).lower() in ["nan", "none"]:
                    value = None
                if value is not None:
                    value = self.apply_transform(transform_name, value)
                kwargs[field_name] = value
            except Exception as e:
                raise ImportErrorRow(
                    f"Transform failed: {str(e)}", field_name=field_name
                )

    def process_constant_fields(
        self, model_config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> None:
        """Process constant fields (field -> constant_value)."""
        if "constant_fields" not in model_config:
            return

        for field_name, constant_value in model_config["constant_fields"].items():
            kwargs[field_name] = constant_value

    def process_reference_fields(
        self,
        model_config: Dict[str, Any],
        created_objs_for_row: Dict[str, Model],
        kwargs: Dict[str, Any],
    ) -> None:
        """Process reference fields (field -> reference_key from previous step)."""
        if "reference_fields" not in model_config:
            return

        for field_name, reference_key in model_config["reference_fields"].items():
            try:
                ref_obj = created_objs_for_row.get(reference_key)

                # Validate reference object exists
                if ref_obj is None:
                    raise ImportErrorRow(
                        f"Missing previous object '{reference_key}' - object was not created in earlier step",
                        field_name=field_name,
                    )

                # Validate reference object is a valid Django model instance
                if not hasattr(ref_obj, "pk"):
                    raise ImportErrorRow(
                        f"Invalid reference object '{reference_key}' - not a valid model instance",
                        field_name=field_name,
                    )

                # Validate reference object has been saved (has a primary key)
                if ref_obj.pk is None:
                    raise ImportErrorRow(
                        f"Reference object '{reference_key}' has not been saved to database",
                        field_name=field_name,
                    )

                kwargs[field_name] = ref_obj
            except ImportErrorRow:
                raise
            except Exception as e:
                raise ImportErrorRow(
                    f"Reference validation error: {str(e)}", field_name=field_name
                )

    def process_lookup_fields(
        self,
        row: Dict[str, Any],
        model_config: Dict[str, Any],
        lookup_caches: Dict[str, Dict],
        lookup_manager,
        kwargs: Dict[str, Any],
    ) -> None:
        """Process lookup fields (field -> {column, model, lookup_field, create_if_missing})."""
        if "lookup_fields" not in model_config:
            return

        for field_name, lookup_spec in model_config["lookup_fields"].items():
            try:
                column_name = lookup_spec["column"]
                source_val = row.get(column_name)

                if source_val is None:
                    kwargs[field_name] = None
                else:
                    found = lookup_manager.resolve_lookup(
                        lookup_spec, source_val, lookup_caches
                    )
                    if found:
                        kwargs[field_name] = found
                    else:
                        if lookup_spec.get("create_if_missing", False):
                            try:
                                lookup_model = lookup_manager._get_model(
                                    lookup_spec["model"]
                                )
                                lookup_obj, _ = lookup_model.objects.get_or_create(
                                    **{lookup_spec["lookup_field"]: source_val}
                                )
                                # Use consistent cache key normalization
                                cache_key = f"{lookup_spec['model']}__{lookup_spec['lookup_field']}"
                                lookup_caches.setdefault(cache_key, {})[
                                    source_val
                                ] = lookup_obj
                                kwargs[field_name] = lookup_obj
                            except Exception as e:
                                raise ImportErrorRow(
                                    f"Failed to create missing lookup object: {str(e)}",
                                    field_name=field_name,
                                )
                        else:
                            raise ImportErrorRow(
                                f"Lookup failed for {lookup_spec['model']} where {lookup_spec['lookup_field']}={source_val}",
                                field_name=field_name,
                            )
            except ImportErrorRow:
                raise
            except Exception as e:
                raise ImportErrorRow(
                    f"Lookup processing error: {str(e)}", field_name=field_name
                ) from e

    def validate_required_fields(
        self, kwargs: Dict[str, Any], model_config: Dict[str, Any]
    ) -> None:
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
            raise ImportErrorRow(
                f"Missing required fields: {', '.join(missing_required)}"
            )
