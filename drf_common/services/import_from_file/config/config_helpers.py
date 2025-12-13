"""
Helper utilities for creating and working with import configurations.
"""

from typing import Any, Dict, List


class ConfigHelpers:
    """Helper methods for creating import configurations."""

    @staticmethod
    def create_simple_config(
        model_path: str,
        field_mappings: Dict[str, str],
        file_format: str = "xlsx",
        unique_by: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Helper method to create a simple configuration for single model imports.

        Args:
            model_path: Django model path (e.g., "accounts.User")
            field_mappings: Dict of field_name -> column_name mappings
            file_format: File format ("xlsx", "csv", "xls")
            unique_by: List of fields for update detection

        Returns:
            Complete configuration dict
        """
        return {
            "file_format": file_format,
            "order": ["main"],
            "models": {
                "main": {
                    "model": model_path,
                    "unique_by": unique_by or [],
                    "update_if_exists": bool(unique_by),
                    "direct_columns": field_mappings,
                }
            },
        }

    @staticmethod
    def validate_transforms_needed(
        config: Dict[str, Any], transforms: Dict[str, callable]
    ) -> List[str]:
        """
        Validate that all required transform functions are provided.

        Args:
            config: Import configuration
            transforms: Available transform functions

        Returns:
            List of missing transform function names
        """
        required_transforms = set()

        for step_key, model_config in config.get("models", {}).items():
            # Check transformed_columns
            if "transformed_columns" in model_config:
                for transform_spec in model_config["transformed_columns"].values():
                    required_transforms.add(transform_spec["transform"])

            # Check computed_fields generators
            if "computed_fields" in model_config:
                for compute_spec in model_config["computed_fields"].values():
                    required_transforms.add(compute_spec["generator"])

        available_transforms = set(transforms.keys())
        missing_transforms = required_transforms - available_transforms

        return sorted(missing_transforms)
